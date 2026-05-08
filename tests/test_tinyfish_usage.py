import pytest
from pydantic import ValidationError

from microfish.tinyfish_client import FetchUsageRequest, SearchUsageRequest


def test_search_usage_default_limit():
    req = SearchUsageRequest()
    assert req.limit == 100


def test_search_usage_limit_max():
    req = SearchUsageRequest(limit=1000)
    assert req.limit == 1000


def test_search_usage_limit_exceeds_max():
    with pytest.raises(ValidationError):
        SearchUsageRequest(limit=1001)


def test_fetch_usage_default_limit():
    req = FetchUsageRequest()
    assert req.limit == 20


def test_fetch_usage_limit_max():
    req = FetchUsageRequest(limit=100)
    assert req.limit == 100


def test_fetch_usage_limit_exceeds_max():
    with pytest.raises(ValidationError):
        FetchUsageRequest(limit=101)
