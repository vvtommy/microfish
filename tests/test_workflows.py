from pathlib import Path


def test_pypi_workflow_uses_oidc_trusted_publishing():
    text = Path(".github/workflows/pypi.yml").read_text()
    assert "id-token: write" in text
    assert "uv build" in text
    assert "pypa/gh-action-pypi-publish" in text
    forbidden = ["TWINE_PASSWORD", "PYPI_API_TOKEN", "password:", "username:"]
    assert all(fragment not in text for fragment in forbidden)


def test_docker_workflow_publishes_microfish_image_to_ghcr():
    text = Path(".github/workflows/docker.yml").read_text()
    assert "packages: write" in text
    assert "v*.*.*" in text
    assert "docker/login-action" in text
    assert "docker/metadata-action" in text
    assert "docker/build-push-action" in text
    assert "push: true" in text
    assert "ghcr.io" in text
    assert "github.repository" in text
