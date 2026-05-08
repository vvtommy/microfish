import httpx
import respx

from microfish.tinyfish_client import FetchRequest, TinyFishClient


@respx.mock
async def test_fetch_preserves_partial_failures():
    respx.post("https://api.fetch.tinyfish.ai").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [{"url": "https://example.com", "text": "ok"}],
                "errors": [{"url": "https://bad.invalid", "error": "fetch_error"}],
            },
        )
    )
    client = TinyFishClient("https://api.search.tinyfish.ai", "https://api.fetch.tinyfish.ai", 30)

    result = await client.fetch_content(
        "test-token",
        FetchRequest(urls=["https://example.com", "https://bad.invalid"]),
    )

    assert result["ok"] is True
    assert len(result["data"]["results"]) == 1
    assert len(result["data"]["errors"]) == 1


def test_fetch_include_html_head_defaults_to_false():
    req = FetchRequest(urls=["https://example.com"])
    assert req.include_html_head is False


def test_fetch_include_html_head_true_in_payload():
    req = FetchRequest(urls=["https://example.com"], include_html_head=True)
    payload = req.model_dump(mode="json")
    assert payload["include_html_head"] is True


def test_fetch_include_html_head_false_in_payload():
    req = FetchRequest(urls=["https://example.com"], include_html_head=False)
    payload = req.model_dump(mode="json")
    assert payload["include_html_head"] is False
