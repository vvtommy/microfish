from microfish.server import create_app
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
