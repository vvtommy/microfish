import contextlib
import hmac
from collections.abc import Iterator
from contextvars import ContextVar

from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

from microfish.settings import Settings

current_tinyfish_api_key: ContextVar[str | None] = ContextVar(
    "current_tinyfish_api_key",
    default=None,
)
current_mcp_authenticated: ContextVar[bool] = ContextVar(
    "current_mcp_authenticated",
    default=False,
)


class AuthenticationError(ValueError):
    pass


def parse_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, separator, token = authorization.strip().partition(" ")
    if separator != " " or scheme.lower() != "bearer":
        return None
    cleaned = token.strip()
    return cleaned or None


def require_api_key() -> str:
    token = current_tinyfish_api_key.get()
    if not token:
        raise AuthenticationError("Missing Authorization Bearer token")
    return token


def require_mcp_authentication() -> None:
    if not current_mcp_authenticated.get():
        raise AuthenticationError("Missing or invalid Authorization Bearer token")


@contextlib.contextmanager
def local_mcp_authentication() -> Iterator[None]:
    tinyfish_context = current_tinyfish_api_key.set(None)
    mcp_context = current_mcp_authenticated.set(True)
    try:
        yield
    finally:
        current_tinyfish_api_key.reset(tinyfish_context)
        current_mcp_authenticated.reset(mcp_context)


def mask_token(token: str | None) -> str:
    if not token:
        return "<empty>"
    if len(token) <= 8:
        return "<redacted>"
    return f"{token[:4]}...{token[-4:]}"


class BearerTokenMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings

    @classmethod
    def as_starlette_middleware(cls, settings: Settings) -> Middleware:
        return Middleware(cls, settings=settings)

    async def dispatch(self, request, call_next):
        token = parse_bearer_token(request.headers.get("authorization"))
        tinyfish_context = current_tinyfish_api_key.set(None)
        mcp_context = current_mcp_authenticated.set(False)
        try:
            if self.settings.polling_enabled:
                expected = self.settings.mcp_auth_token
                authenticated = expected is None or (
                    token is not None and hmac.compare_digest(token, expected)
                )
                current_mcp_authenticated.set(authenticated)
            else:
                current_tinyfish_api_key.set(token)
                current_mcp_authenticated.set(token is not None)
            return await call_next(request)
        finally:
            current_tinyfish_api_key.reset(tinyfish_context)
            current_mcp_authenticated.reset(mcp_context)
