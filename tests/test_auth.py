from microfish.auth import mask_token, parse_bearer_token


def test_parse_valid_bearer_token():
    assert parse_bearer_token("Bearer test-token") == "test-token"


def test_parse_invalid_authorization_header():
    assert parse_bearer_token(None) is None
    assert parse_bearer_token("") is None
    assert parse_bearer_token("Basic test-token") is None
    assert parse_bearer_token("Bearer   ") is None


def test_mask_token_never_returns_full_token():
    assert mask_token("abcd1234secret") == "abcd...cret"
