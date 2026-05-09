import pytest

from microfish.server import create_app, main
from microfish.settings import Settings


def test_default_settings():
    s = Settings()
    assert s.host == "0.0.0.0"
    assert s.port == 8000
    assert s.mcp_path == "/mcp"
    assert s.tinyfish_search_url == "https://api.search.tinyfish.ai"
    assert s.tinyfish_fetch_url == "https://api.fetch.tinyfish.ai"


def test_env_override(monkeypatch):
    monkeypatch.setenv("MICROFISH_PORT", "9000")
    monkeypatch.setenv("MICROFISH_MCP_PATH", "/custom-mcp")
    s = Settings()
    assert s.port == 9000
    assert s.mcp_path == "/custom-mcp"


def test_create_app_without_real_port():
    app = create_app(Settings())
    assert app is not None


def test_default_transport_is_http():
    settings = Settings()
    assert settings.transport == "http"


def test_transport_env_override(monkeypatch):
    monkeypatch.setenv("MICROFISH_TRANSPORT", "stdio")
    settings = Settings()
    assert settings.transport == "stdio"


def test_main_uses_http_when_flag_given(monkeypatch):
    calls = []
    monkeypatch.setattr("sys.argv", ["microfish", "--transport", "http"])
    monkeypatch.setattr(
        "microfish.server.uvicorn.run",
        lambda *args, **kwargs: calls.append(kwargs),
    )
    main()
    assert calls[0]["host"] == "0.0.0.0"
    assert calls[0]["port"] == 8000


def test_main_uses_stdio_without_uvicorn(monkeypatch):
    calls = []

    class FakeMcp:
        def run(self, transport: str) -> None:
            calls.append(transport)

    monkeypatch.setenv("TINYFISH_KEYS", "test-key")
    monkeypatch.setattr("sys.argv", ["microfish", "--transport", "stdio"])
    monkeypatch.setattr("microfish.server.create_mcp", lambda settings: FakeMcp())
    monkeypatch.setattr(
        "microfish.server.uvicorn.run",
        lambda *args, **kwargs: pytest.fail("stdio must not start uvicorn"),
    )

    main()

    assert calls == ["stdio"]


def test_stdio_requires_tinyfish_keys(monkeypatch):
    monkeypatch.delenv("TINYFISH_KEYS", raising=False)
    monkeypatch.setattr("sys.argv", ["microfish", "--transport", "stdio"])
    with pytest.raises(RuntimeError, match="TINYFISH_KEYS"):
        main()
