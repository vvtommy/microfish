from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

TransportMode = Literal["http", "stdio"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MICROFISH_", populate_by_name=True)

    host: str = "0.0.0.0"
    port: int = 8000
    mcp_path: str = "/mcp"
    transport: TransportMode = "stdio"
    tinyfish_search_url: str = "https://api.search.tinyfish.ai"
    tinyfish_fetch_url: str = "https://api.fetch.tinyfish.ai"
    request_timeout_seconds: float = Field(default=30.0, gt=0)
    log_level: str = "info"
    tinyfish_keys: Annotated[list[str], NoDecode] = Field(
        default_factory=list,
        validation_alias="TINYFISH_KEYS",
        repr=False,
    )
    mcp_auth_token: str | None = Field(
        default=None,
        validation_alias="MCP_AUTH_TOKEN",
        repr=False,
    )

    @field_validator("tinyfish_keys", mode="before")
    @classmethod
    def parse_tinyfish_keys(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [key.strip() for key in value.split(",") if key.strip()]
        if isinstance(value, list):
            return [str(key).strip() for key in value if str(key).strip()]
        return []

    @field_validator("mcp_auth_token", mode="before")
    @classmethod
    def normalize_mcp_auth_token(cls, value: object) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    @field_validator("transport", mode="before")
    @classmethod
    def normalize_transport(cls, value: object) -> object:
        if value is None:
            return "http"
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @property
    def polling_enabled(self) -> bool:
        return bool(self.tinyfish_keys)


def load_settings() -> Settings:
    return Settings()
