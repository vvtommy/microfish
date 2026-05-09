from pathlib import Path

README_FILES = (Path("README.md"), Path("README_cn.md"))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_product_docs_do_not_contain_real_api_key_examples():
    text = "\n".join(read(path) for path in README_FILES)
    forbidden_fragments = ["sk-", "tf_", "tinyfish_live_"]
    assert all(fragment not in text for fragment in forbidden_fragments)
