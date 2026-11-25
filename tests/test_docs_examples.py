"""Execute documented unit-test examples from docs/CALLER_ATTRIBUTION_EXAMPLES.md."""

import re
from pathlib import Path

DOC_PATH = Path(__file__).resolve().parents[1] / "docs" / "CALLER_ATTRIBUTION_EXAMPLES.md"


def _extract_unit_test_block(markdown: str) -> str:
    pattern = re.compile(
        r"###\s+Unit Test Examples\s*\n+```python\n(.*?)\n```",
        re.DOTALL,
    )
    match = pattern.search(markdown)
    if match is None:
        raise AssertionError("Could not find fenced python block under '### Unit Test Examples'")
    return match.group(1)


def test_caller_attribution_doc_examples_pass(caplog):
    markdown = DOC_PATH.read_text(encoding="utf-8")
    code = _extract_unit_test_block(markdown)

    namespace: dict[str, object] = {}
    exec(compile(code, str(DOC_PATH), "exec"), namespace)

    test_funcs = [fn for name, fn in namespace.items() if name.startswith("test_") and callable(fn)]
    assert len(test_funcs) >= 2, "Expected at least two documented test_* examples"

    for test_fn in test_funcs:
        caplog.clear()
        test_fn(caplog)


def test_configuration_guide_filtering_example_filters_records(caplog):
    config_guide = Path(__file__).resolve().parents[1] / "docs" / "CONFIGURATION_GUIDE.md"
    markdown = config_guide.read_text(encoding="utf-8")
    match = re.search(r"###\s+Filtering Logs\s*\n+```python\n(.*?)\n```", markdown, re.DOTALL)
    assert match is not None

    with caplog.at_level("DEBUG", logger="business"):
        exec(compile(match.group(1), str(config_guide), "exec"), {})

    messages = [r.message for r in caplog.records if r.name == "business"]
    assert messages == ["User registered", "Order placed"]


def test_api_reference_base_dir_example_does_not_double_nest():
    api_ref = Path(__file__).resolve().parents[1] / "docs" / "API_REFERENCE.md"
    text = api_ref.read_text(encoding="utf-8")
    assert 'json_file_name="app.jsonl"' in text
    assert 'json_file_name="logs/app.jsonl",\n    json_file_base_dir="logs"' not in text
