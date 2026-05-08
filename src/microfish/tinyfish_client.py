from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field, HttpUrl, field_validator

from microfish.settings import Settings


class TinyFishApiError(RuntimeError):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(f"TinyFish API error {status_code} {code}: {message}")
        self.status_code = status_code
        self.code = code
        self.message = message

    def to_payload(self) -> dict[str, Any]:
        return {
            "ok": False,
            "error": {
                "status_code": self.status_code,
                "code": self.code,
                "message": self.message,
            },
        }


class SearchRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=2000,
        description="Search query for TinyFish Search.",
    )
    location: str | None = Field(
        default=None,
        description="Country code for geo-targeted results.",
    )
    language: str | None = Field(
        default=None,
        description="Language code for result language.",
    )
    page: int = Field(
        default=0,
        ge=0,
        le=10,
        description="Page number for pagination, starting from 0.",
    )
    include_thumbnail: bool = Field(
        default=False,
        description="When true, include thumbnail_url in search results when available.",
    )

    def to_query_params(self) -> dict[str, Any]:
        params = self.model_dump(exclude_none=True)
        params["include_thumbnail"] = "true" if self.include_thumbnail else "false"
        return params


class FetchRequest(BaseModel):
    urls: list[HttpUrl] = Field(
        min_length=1,
        max_length=10,
        description="Array of URLs to fetch. Each URL is processed independently.",
    )
    format: Literal["markdown", "html", "json"] = Field(
        default="markdown",
        description="Output format for extracted content.",
    )
    include_html_head: bool = Field(
        default=False,
        description="When true and format is html, include a complete HTML document head.",
    )
    links: bool = Field(
        default=False,
        description="Extract outbound links from each page.",
    )
    image_links: bool = Field(
        default=False,
        description="Extract image URLs from each page.",
    )

    @field_validator("urls")
    @classmethod
    def reject_duplicate_urls(cls, urls: list[HttpUrl]) -> list[HttpUrl]:
        normalized = [str(url) for url in urls]
        if len(normalized) != len(set(normalized)):
            raise ValueError("urls must not contain duplicates")
        return urls


UsageStatus = Literal["completed", "failed"]


class SearchUsageRequest(BaseModel):
    start_after: str | None = Field(
        default=None, description="Return records created after this time."
    )
    end_before: str | None = Field(
        default=None, description="Return records created before this time."
    )
    status: UsageStatus | None = Field(
        default=None, description="Filter by completed or failed status."
    )
    limit: int = Field(
        default=100, ge=1, le=1000, description="Page size for search usage records."
    )
    page: int = Field(default=1, ge=1, description="Usage page number, starting from 1.")


class FetchUsageRequest(BaseModel):
    start_after: str | None = Field(
        default=None, description="Return records created after this time."
    )
    end_before: str | None = Field(
        default=None, description="Return records created before this time."
    )
    status: UsageStatus | None = Field(
        default=None, description="Filter by completed or failed status."
    )
    limit: int = Field(default=20, ge=1, le=100, description="Page size for fetch usage records.")
    page: int = Field(default=1, ge=1, description="Usage page number, starting from 1.")


class TinyFishClient:
    def __init__(
        self,
        search_url: str,
        fetch_url: str,
        timeout_seconds: float,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.search_url = search_url.rstrip("/")
        self.fetch_url = fetch_url.rstrip("/")
        self.timeout = httpx.Timeout(timeout_seconds)
        self.http_client = http_client

    @classmethod
    def from_settings(cls, settings: Settings) -> "TinyFishClient":
        return cls(
            search_url=settings.tinyfish_search_url,
            fetch_url=settings.tinyfish_fetch_url,
            timeout_seconds=settings.request_timeout_seconds,
        )

    async def search(self, api_key: str, request: SearchRequest) -> dict[str, Any]:
        return await self._request(
            "GET",
            self.search_url,
            api_key,
            params=request.to_query_params(),
        )

    async def fetch_content(self, api_key: str, request: FetchRequest) -> dict[str, Any]:
        payload = request.model_dump(mode="json")
        return await self._request("POST", self.fetch_url, api_key, json=payload)

    async def get_search_usage(self, api_key: str, request: SearchUsageRequest) -> dict[str, Any]:
        return await self._request(
            "GET",
            f"{self.search_url}/usage",
            api_key,
            params=request.model_dump(exclude_none=True),
        )

    async def list_fetch_usage(self, api_key: str, request: FetchUsageRequest) -> dict[str, Any]:
        return await self._request(
            "GET",
            f"{self.fetch_url}/usage",
            api_key,
            params=request.model_dump(exclude_none=True),
        )

    async def _request(self, method: str, url: str, api_key: str, **kwargs: Any) -> dict[str, Any]:
        headers = {"X-API-Key": api_key}
        client = self.http_client or httpx.AsyncClient(timeout=self.timeout)
        close_client = self.http_client is None
        try:
            response = await client.request(method, url, headers=headers, **kwargs)
            return self._parse_response(response)
        except httpx.TimeoutException as exc:
            raise TinyFishApiError(504, "TIMEOUT", "TinyFish request timed out") from exc
        except httpx.HTTPError as exc:
            raise TinyFishApiError(502, "UPSTREAM_ERROR", str(exc)) from exc
        finally:
            if close_client:
                await client.aclose()

    def _parse_response(self, response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise TinyFishApiError(
                response.status_code, "INVALID_JSON", response.text[:200]
            ) from exc

        if response.is_error:
            error = payload.get("error") if isinstance(payload, dict) else None
            code = str(error.get("code", "HTTP_ERROR")) if isinstance(error, dict) else "HTTP_ERROR"
            message = (
                str(error.get("message", response.reason_phrase))
                if isinstance(error, dict)
                else response.reason_phrase
            )
            raise TinyFishApiError(response.status_code, code, message)

        if not isinstance(payload, dict):
            raise TinyFishApiError(
                response.status_code, "INVALID_RESPONSE", "Expected a JSON object"
            )
        return {"ok": True, "data": payload}
