import asyncio
from collections.abc import Awaitable, Callable
from typing import Annotated, Any, Literal

from mcp.server.fastmcp import FastMCP
from pydantic import Field, ValidationError

from microfish.auth import AuthenticationError, require_api_key, require_mcp_authentication
from microfish.settings import Settings
from microfish.tinyfish_client import (
    FetchRequest,
    FetchUsageRequest,
    SearchRequest,
    SearchUsageRequest,
    TinyFishApiError,
    TinyFishClient,
)
from microfish.tool_policy import FREE_TOOL_NAMES, retained_tool_names


def error_payload(code: str, message: str, details: Any | None = None) -> dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message, "details": details}}


def safe_call_error(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, AuthenticationError):
        return error_payload("AUTHENTICATION_REQUIRED", str(exc))
    if isinstance(exc, ValidationError):
        return error_payload("INVALID_INPUT", "Input validation failed", exc.errors())
    if isinstance(exc, TinyFishApiError):
        return exc.to_payload()
    return error_payload("INTERNAL_ERROR", "Unexpected tool error")


def assert_policy_consistent() -> None:
    retained = retained_tool_names()
    if retained != FREE_TOOL_NAMES:
        raise RuntimeError("Tool policy and allowlist are inconsistent")


class TinyFishKeyPool:
    def __init__(self, keys: list[str], max_extra_retries: int = 3) -> None:
        if not keys:
            raise ValueError("TinyFish key pool requires at least one key")
        self._keys = keys
        self._max_attempts = min(len(keys), max_extra_retries + 1)
        self._next_index = 0
        self._lock = asyncio.Lock()

    async def next_attempt_keys(self) -> list[str]:
        async with self._lock:
            start_index = self._next_index
            self._next_index = (self._next_index + 1) % len(self._keys)
        return [
            self._keys[(start_index + offset) % len(self._keys)]
            for offset in range(self._max_attempts)
        ]


class TinyFishToolExecutor:
    def __init__(self, settings: Settings, client: TinyFishClient) -> None:
        self.settings = settings
        self.client = client
        self.key_pool = (
            TinyFishKeyPool(settings.tinyfish_keys) if settings.polling_enabled else None
        )

    async def run(self, operation: Callable[[str], Awaitable[dict[str, Any]]]) -> dict[str, Any]:
        if not self.settings.polling_enabled:
            return await operation(require_api_key())

        require_mcp_authentication()
        if self.key_pool is None:
            raise AuthenticationError("TinyFish key pool is not configured")

        last_error: TinyFishApiError | None = None
        for api_key in await self.key_pool.next_attempt_keys():
            try:
                return await operation(api_key)
            except TinyFishApiError as exc:
                last_error = exc

        if last_error is not None:
            raise last_error
        raise TinyFishApiError(502, "UPSTREAM_ERROR", "TinyFish request failed")

    async def search(self, request: SearchRequest) -> dict[str, Any]:
        return await self.run(lambda api_key: self.client.search(api_key, request))

    async def fetch_content(self, request: FetchRequest) -> dict[str, Any]:
        return await self.run(lambda api_key: self.client.fetch_content(api_key, request))

    async def get_search_usage(self, request: SearchUsageRequest) -> dict[str, Any]:
        return await self.run(lambda api_key: self.client.get_search_usage(api_key, request))

    async def list_fetch_usage(self, request: FetchUsageRequest) -> dict[str, Any]:
        return await self.run(lambda api_key: self.client.list_fetch_usage(api_key, request))


def register_tools(mcp: FastMCP, executor: TinyFishToolExecutor) -> None:
    assert_policy_consistent()

    UsageStatus = Literal["completed", "failed"]

    @mcp.tool(name="search")
    async def search(
        query: Annotated[
            str,
            Field(
                min_length=1,
                max_length=2000,
                description="Search query, up to 2000 characters.",
            ),
        ],
        location: Annotated[
            str | None,
            Field(description="Optional country code for geo-targeted results."),
        ] = None,
        language: Annotated[
            str | None,
            Field(description="Optional language code for result language."),
        ] = None,
        page: Annotated[
            int,
            Field(ge=0, le=10, description="Search result page number, starting from 0."),
        ] = 0,
        include_thumbnail: Annotated[
            bool,
            Field(description="Include thumbnail_url in results when TinyFish has one."),
        ] = False,
    ) -> dict[str, Any]:
        """Search the web through the free TinyFish Search API.

        Returns ranked titles, snippets, URLs, and optional thumbnail URLs.
        This tool does not start Agent, Browser, batch, or run lifecycle APIs.
        """
        try:
            request = SearchRequest(
                query=query,
                location=location,
                language=language,
                page=page,
                include_thumbnail=include_thumbnail,
            )
            return await executor.search(request)
        except Exception as exc:
            return safe_call_error(exc)

    @mcp.tool(name="fetch_content")
    async def fetch_content(
        urls: Annotated[
            list[str],
            Field(min_length=1, max_length=10, description="One to ten URLs to fetch."),
        ],
        format: Annotated[
            Literal["markdown", "html", "json"],
            Field(description="Output format for extracted content."),
        ] = "markdown",
        include_html_head: Annotated[
            bool,
            Field(description="When format is html, include a complete document head."),
        ] = False,
        links: Annotated[
            bool,
            Field(description="Extract outbound links from each page."),
        ] = False,
        image_links: Annotated[
            bool,
            Field(description="Extract image URLs from each page."),
        ] = False,
    ) -> dict[str, Any]:
        """Fetch and extract clean content through the free TinyFish Fetch API.

        Each URL is processed independently; per-URL failures appear in errors.
        This tool does not create browser sessions or run web automation.
        """
        try:
            request = FetchRequest(
                urls=urls,
                format=format,
                include_html_head=include_html_head,
                links=links,
                image_links=image_links,
            )
            return await executor.fetch_content(request)
        except Exception as exc:
            return safe_call_error(exc)

    @mcp.tool(name="get_search_usage")
    async def get_search_usage(
        start_after: Annotated[
            str | None, Field(description="Optional ISO datetime lower bound.")
        ] = None,
        end_before: Annotated[
            str | None, Field(description="Optional ISO datetime upper bound.")
        ] = None,
        status: Annotated[UsageStatus | None, Field(description="completed or failed.")] = None,
        limit: Annotated[int, Field(ge=1, le=1000, description="Search usage page size.")] = 100,
        page: Annotated[int, Field(ge=1, description="Usage page number, starting from 1.")] = 1,
    ) -> dict[str, Any]:
        """List Search API usage records for audit and troubleshooting."""
        try:
            request = SearchUsageRequest(
                start_after=start_after,
                end_before=end_before,
                status=status,
                limit=limit,
                page=page,
            )
            return await executor.get_search_usage(request)
        except Exception as exc:
            return safe_call_error(exc)

    @mcp.tool(name="list_fetch_usage")
    async def list_fetch_usage(
        start_after: Annotated[
            str | None, Field(description="Optional ISO datetime lower bound.")
        ] = None,
        end_before: Annotated[
            str | None, Field(description="Optional ISO datetime upper bound.")
        ] = None,
        status: Annotated[UsageStatus | None, Field(description="completed or failed.")] = None,
        limit: Annotated[int, Field(ge=1, le=100, description="Fetch usage page size.")] = 20,
        page: Annotated[int, Field(ge=1, description="Usage page number, starting from 1.")] = 1,
    ) -> dict[str, Any]:
        """List Fetch API usage records for audit and troubleshooting."""
        try:
            request = FetchUsageRequest(
                start_after=start_after,
                end_before=end_before,
                status=status,
                limit=limit,
                page=page,
            )
            return await executor.list_fetch_usage(request)
        except Exception as exc:
            return safe_call_error(exc)
