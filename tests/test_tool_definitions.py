import pytest

from microfish.server import create_mcp
from microfish.settings import Settings


@pytest.fixture
def mcp_instance():
    settings = Settings(tinyfish_keys=["test-key"])
    return create_mcp(settings)


def test_all_tools_registered(mcp_instance):
    tool_names = {tool.name for tool in mcp_instance._tool_manager.list_tools()}
    assert {"search", "fetch_content", "get_search_usage", "list_fetch_usage"} == tool_names


def test_tool_descriptions_non_empty(mcp_instance):
    tools = {tool.name: tool for tool in mcp_instance._tool_manager.list_tools()}
    for name in ("search", "fetch_content", "get_search_usage", "list_fetch_usage"):
        assert tools[name].description, f"{name} description should not be empty"


def test_search_description_does_not_recommend_blocked_tools(mcp_instance):
    tools = {tool.name: tool for tool in mcp_instance._tool_manager.list_tools()}
    blocked_terms = ["run_web_automation", "browser_session", "batch_create", "Agent automation"]
    for term in blocked_terms:
        assert term not in (tools["search"].description or "")
        assert term not in (tools["fetch_content"].description or "")
