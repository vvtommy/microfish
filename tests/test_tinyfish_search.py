import httpx
import pytest
import respx
from pydantic import ValidationError

from microfish.tinyfish_client import SearchRequest, TinyFishApiError, TinyFishClient


@respx.mock
async def test_search_sends_x_api_key_header():
    route = respx.get("https://api.search.tinyfish.ai").mock(
        return_value=httpx.Response(
            200,
            json={"query": "python", "results": [], "total_results": 0, "page": 0},
        )
    )
    client = TinyFishClient("https://api.search.tinyfish.ai", "https://api.fetch.tinyfish.ai", 30)

    result = await client.search("test-token", SearchRequest(query="python"))

    assert result["ok"] is True
    assert route.calls.last.request.headers["X-API-Key"] == "test-token"
    assert "Authorization" not in route.calls.last.request.headers


@respx.mock
async def test_upstream_error_is_structured():
    respx.get("https://api.search.tinyfish.ai").mock(
        return_value=httpx.Response(
            401,
            json={"error": {"code": "INVALID_API_KEY", "message": "Invalid key"}},
        )
    )
    client = TinyFishClient("https://api.search.tinyfish.ai", "https://api.fetch.tinyfish.ai", 30)

    with pytest.raises(TinyFishApiError) as exc_info:
        await client.search("test-token", SearchRequest(query="python"))

    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "INVALID_API_KEY"


def test_search_include_thumbnail_defaults_to_false():
    req = SearchRequest(query="hello")
    assert req.include_thumbnail is False


def test_search_include_thumbnail_to_query_params_true():
    req = SearchRequest(query="hello", include_thumbnail=True)
    params = req.to_query_params()
    assert params["include_thumbnail"] == "true"


def test_search_include_thumbnail_to_query_params_false():
    req = SearchRequest(query="hello", include_thumbnail=False)
    params = req.to_query_params()
    assert params["include_thumbnail"] == "false"


def test_search_query_max_length_exceeded():
    with pytest.raises(ValidationError):
        SearchRequest(query="a" * 2001)


def test_search_query_max_length_exact():
    req = SearchRequest(query="a" * 2000)
    assert len(req.query) == 2000


@respx.mock
async def test_search_include_thumbnail_passed_as_string():
    route = respx.get("https://api.search.tinyfish.ai").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": []})
    )
    client = TinyFishClient(
        search_url="https://api.search.tinyfish.ai",
        fetch_url="https://api.fetch.tinyfish.ai",
        timeout_seconds=5,
    )
    req = SearchRequest(query="test", include_thumbnail=True)
    await client.search("test-key", req)
    sent_params = route.calls[0].request.url.params
    assert sent_params["include_thumbnail"] == "true"
