from pathlib import Path


def test_compose_files_do_not_contain_real_api_key():
    text = "\n".join(
        Path(path).read_text() for path in ("docker-compose.yml", "docker-compose_build.yml")
    )
    forbidden_fragments = ["sk-", "tf_", "tinyfish_live_"]
    assert all(fragment not in text for fragment in forbidden_fragments)
