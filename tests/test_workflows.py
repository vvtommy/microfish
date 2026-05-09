from pathlib import Path


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
