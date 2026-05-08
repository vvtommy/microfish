from microfish.tool_policy import (
    BLOCKED_TOOL_NAMES,
    FREE_TOOL_NAMES,
    TOOL_MATRIX,
    retained_tool_names,
)

ORIGINAL_TINYFISH_TOOL_NAMES = frozenset(
    {
        "run_web_automation",
        "run_web_automation_async",
        "get_run",
        "list_runs",
        "cancel_run",
        "poll_status",
        "get_steps",
        "discover_run",
        "batch_create",
        "batch_status",
        "batch_cancel",
        "search",
        "get_search_usage",
        "create_browser_session",
        "list_browser_sessions",
        "fetch_content",
        "list_fetch_usage",
    }
)


def test_retained_tools_match_allowlist():
    assert retained_tool_names() == FREE_TOOL_NAMES


def test_policy_covers_original_tinyfish_tools():
    assert FREE_TOOL_NAMES | BLOCKED_TOOL_NAMES == ORIGINAL_TINYFISH_TOOL_NAMES
    assert FREE_TOOL_NAMES.isdisjoint(BLOCKED_TOOL_NAMES)


def test_tool_matrix_covers_original_tinyfish_tools():
    assert {decision.name for decision in TOOL_MATRIX} == ORIGINAL_TINYFISH_TOOL_NAMES
