from pathlib import Path


def test_dockerfile_uses_uv_sync_no_dev():
    text = Path("Dockerfile").read_text()
    assert "uv sync --frozen --no-dev --no-install-project" in text
    assert "uv sync --frozen --no-dev" in text
    assert 'CMD ["uv", "run", "microfish"]' in text


def test_compose_exposes_port_8000():
    text = Path("docker-compose.yml").read_text()
    assert "8000:8000" in text
    assert "/health" in text


def test_compose_does_not_contain_real_api_key():
    text = Path("docker-compose.yml").read_text()
    forbidden_fragments = ["sk-", "tf_", "tinyfish_live_"]
    assert all(fragment not in text for fragment in forbidden_fragments)
