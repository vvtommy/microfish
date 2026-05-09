from pathlib import Path

from microfish.tool_policy import BLOCKED_TOOL_NAMES, FREE_TOOL_NAMES

README_FILES = (Path("README.md"), Path("README_cn.md"))

REQUIRED_SHARED_TERMS = {
    "search",
    "fetch_content",
    "get_search_usage",
    "list_fetch_usage",
    "TINYFISH_KEYS",
    "MCP_AUTH_TOKEN",
    "MICROFISH_HOST",
    "MICROFISH_PORT",
    "MICROFISH_MCP_PATH",
    "MICROFISH_TRANSPORT",
    "uvx microfish",
    "stdio",
    "Claude Code",
    "Codex",
    "Cursor",
    "http://localhost:8000/mcp",
    "docker-compose.yml",
    "docker-compose_build.yml",
    "ghcr.io/vvtommy/microfish",
    "pypi.yml",
    "PyPI OIDC",
    "vX.Y.Z",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_readmes_contain_same_core_terms():
    for path in README_FILES:
        text = read(path)
        missing = REQUIRED_SHARED_TERMS - set(
            term for term in REQUIRED_SHARED_TERMS if term in text
        )
        assert missing == set(), f"{path} is missing terms: {missing}"


def test_product_docs_list_only_allowlisted_tools_as_available():
    for path in README_FILES:
        text = read(path)
        available_section = text.split("##", maxsplit=3)[1]
        for tool_name in FREE_TOOL_NAMES:
            assert tool_name in available_section
        for tool_name in BLOCKED_TOOL_NAMES:
            assert tool_name not in available_section


def test_product_docs_do_not_contain_real_api_key_examples():
    text = "\n".join(read(path) for path in README_FILES)
    forbidden_fragments = ["sk-", "tf_", "tinyfish_live_"]
    assert all(fragment not in text for fragment in forbidden_fragments)
