from dataclasses import dataclass

FREE_TOOL_NAMES = frozenset(
    {
        "search",
        "fetch_content",
        "get_search_usage",
        "list_fetch_usage",
    }
)

BLOCKED_TOOL_NAMES = frozenset(
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
        "create_browser_session",
        "list_browser_sessions",
    }
)


@dataclass(frozen=True)
class ToolDecision:
    name: str
    group: str
    retained: bool
    evidence: str
    risk: str


TOOL_MATRIX = (
    ToolDecision(
        "search",
        "Web Search",
        True,
        "TinyFish Search API is documented as a free ranked search endpoint",
        "low",
    ),
    ToolDecision(
        "fetch_content",
        "Content Extraction",
        True,
        "TinyFish Fetch API is documented as a free content extraction endpoint "
        "supporting up to 10 URLs",
        "low",
    ),
    ToolDecision(
        "get_search_usage",
        "Web Search",
        True,
        "Search usage endpoint lists historical Search API records without starting automation",
        "low",
    ),
    ToolDecision(
        "list_fetch_usage",
        "Content Extraction",
        True,
        "Fetch usage endpoint lists historical Fetch API records without starting automation",
        "low",
    ),
    ToolDecision(
        "run_web_automation",
        "Agent Automation",
        False,
        "Agent automation is a credits-backed surface outside the Search and Fetch gateway",
        "blocked",
    ),
    ToolDecision(
        "run_web_automation_async",
        "Agent Automation",
        False,
        "Async Agent automation is a credits-backed surface outside the Search and Fetch gateway",
        "blocked",
    ),
    ToolDecision(
        "get_run",
        "Automation Run Tracking",
        False,
        "Automation run metadata belongs to the Agent surface and is not a Search or Fetch API",
        "blocked",
    ),
    ToolDecision(
        "list_runs",
        "Automation Run Tracking",
        False,
        "Automation run listing belongs to the Agent surface and is not a Search or Fetch API",
        "blocked",
    ),
    ToolDecision(
        "cancel_run",
        "Automation Run Tracking",
        False,
        "Automation run cancellation controls Agent jobs and exceeds the free gateway boundary",
        "blocked",
    ),
    ToolDecision(
        "poll_status",
        "Automation Run Tracking",
        False,
        "Polling run status depends on Agent automation runs and must not be exposed by microfish",
        "blocked",
    ),
    ToolDecision(
        "get_steps",
        "Automation Run Tracking",
        False,
        "Run step inspection depends on Agent automation runs and must not be exposed by microfish",
        "blocked",
    ),
    ToolDecision(
        "discover_run",
        "Automation Run Tracking",
        False,
        "Run discovery depends on Agent automation sessions and must not be exposed by microfish",
        "blocked",
    ),
    ToolDecision(
        "batch_create",
        "Batch Automation",
        False,
        "Batch creation starts automation work outside the Search and Fetch gateway",
        "blocked",
    ),
    ToolDecision(
        "batch_status",
        "Batch Automation",
        False,
        "Batch status reads automation work outside the Search and Fetch gateway",
        "blocked",
    ),
    ToolDecision(
        "batch_cancel",
        "Batch Automation",
        False,
        "Batch cancellation controls automation work outside the Search and Fetch gateway",
        "blocked",
    ),
    ToolDecision(
        "create_browser_session",
        "Browser Sessions",
        False,
        "Browser sessions belong to the Browser API, "
        "which is outside the free Search and Fetch surfaces",
        "blocked",
    ),
    ToolDecision(
        "list_browser_sessions",
        "Browser Sessions",
        False,
        "Browser session listing belongs to the Browser API, "
        "which is outside the free Search and Fetch surfaces",
        "blocked",
    ),
)


def retained_tool_names() -> set[str]:
    return {decision.name for decision in TOOL_MATRIX if decision.retained}
