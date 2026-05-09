import argparse
import contextlib

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from microfish.auth import BearerTokenMiddleware, local_mcp_authentication
from microfish.settings import Settings, load_settings
from microfish.tinyfish_client import TinyFishClient
from microfish.tools import TinyFishToolExecutor, register_tools


async def health_check(request):
    return JSONResponse({"status": "ok"})


def create_mcp(settings: Settings, client: TinyFishClient | None = None) -> FastMCP:
    mcp = FastMCP(
        "microfish",
        stateless_http=True,
        json_response=True,
        streamable_http_path=settings.mcp_path,
    )
    resolved_client = client or TinyFishClient.from_settings(settings)
    register_tools(mcp, TinyFishToolExecutor(settings, resolved_client))
    return mcp


def create_app(settings: Settings | None = None, client: TinyFishClient | None = None) -> Starlette:
    resolved_settings = settings or load_settings()
    mcp = create_mcp(resolved_settings, client)

    @contextlib.asynccontextmanager
    async def lifespan(app):
        async with mcp.session_manager.run():
            yield

    return Starlette(
        routes=[
            Route("/health", health_check, methods=["GET"]),
            Mount("/", app=mcp.streamable_http_app()),
        ],
        middleware=[BearerTokenMiddleware.as_starlette_middleware(resolved_settings)],
        lifespan=lifespan,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="microfish")
    parser.add_argument("--transport", choices=("http", "stdio"), default=None)
    return parser.parse_args()


def settings_from_args() -> Settings:
    settings = load_settings()
    args = parse_args()
    if args.transport is None:
        return settings
    return settings.model_copy(update={"transport": args.transport})


def run_http(settings: Settings) -> None:
    uvicorn.run(
        create_app(settings),
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
    )


def run_stdio(settings: Settings) -> None:
    if not settings.polling_enabled:
        raise RuntimeError("stdio transport requires TINYFISH_KEYS")
    mcp = create_mcp(settings)
    with local_mcp_authentication():
        mcp.run(transport="stdio")


def main() -> None:
    settings = settings_from_args()
    if settings.transport == "stdio":
        run_stdio(settings)
        return
    run_http(settings)
