from pathlib import Path


def test_dockerfile_uses_uv_sync_no_dev():
    text = Path("Dockerfile").read_text()
    assert "uv sync --frozen --no-dev --no-install-project" in text
    assert "uv sync --frozen --no-dev" in text
    assert 'CMD ["uv", "run", "microfish"]' in text


def test_dockerfile_uses_existing_readme_files():
    text = Path("Dockerfile").read_text()
    assert "COPY README.md README_cn.md ./" in text
    assert "Readmd.md" not in text
    assert "Readmd_cn.md" not in text


def test_build_compose_uses_local_dockerfile():
    text = Path("docker-compose_build.yml").read_text()
    assert "build: ." in text
    assert "/health" in text


def test_default_compose_uses_published_image():
    text = Path("docker-compose.yml").read_text()
    assert "ghcr.io/vvtommy/microfish:${MICROFISH_IMAGE_TAG:-latest}" in text
    assert "build: ." not in text
    assert "/health" in text


def test_compose_files_do_not_contain_real_api_key():
    text = "\n".join(
        Path(path).read_text() for path in ("docker-compose.yml", "docker-compose_build.yml")
    )
    forbidden_fragments = ["sk-", "tf_", "tinyfish_live_"]
    assert all(fragment not in text for fragment in forbidden_fragments)
