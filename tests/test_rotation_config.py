import gc
import subprocess
import sys
import warnings

import pytest

from arlogi import get_json_logger, setup_logging
from arlogi.config import LoggingConfig
from arlogi.config_builder import LoggingConfigBuilder
from arlogi.handlers import JSONFileHandler, JSONHandler


def test_logging_config_accepts_rotation_options():
    config = LoggingConfig(
        rotate_schedule="hour",
        rotate_retention_count=7,
    )

    assert config.rotate_schedule == "hour"
    assert config.rotate_retention_count == 7


def test_logging_config_rejects_invalid_rotate_schedule():
    with pytest.raises(ValueError, match="Invalid rotate_schedule"):
        LoggingConfig(rotate_schedule="year")


def test_logging_config_rejects_invalid_retention_count():
    with pytest.raises(ValueError, match="rotate_retention_count"):
        LoggingConfig(rotate_schedule="day", rotate_retention_count=0)


def test_from_kwargs_accepts_rotation_keys():
    config = LoggingConfig.from_kwargs(
        level="INFO",
        rotate_schedule="month",
        rotate_retention_count=3,
    )

    assert config.rotate_schedule == "month"
    assert config.rotate_retention_count == 3


def test_builder_with_rotation_options():
    config = (
        LoggingConfigBuilder()
        .with_json_file("logs/app.jsonl")
        .with_rotation(schedule="week", retention_count=9)
        .build()
    )

    assert config.rotate_schedule == "week"
    assert config.rotate_retention_count == 9


def test_builder_with_rotation_defaults_retention_to_none():
    config = LoggingConfigBuilder().with_rotation(schedule="day").build()

    assert config.rotate_schedule == "day"
    assert config.rotate_retention_count is None


def test_setup_logging_accepts_rotation_options():
    # Under tests, setup does not install handlers; this checks API contract only.
    setup_logging(
        level="INFO",
        rotate_schedule="hour",
        rotate_retention_count=7,
    )


def test_logging_config_resolves_trace_level_before_registration():
    code = (
        "from arlogi.config import LoggingConfig; "
        "cfg = LoggingConfig(level='trace', module_levels={'app.db': 'TRACE'}); "
        "assert cfg.resolved_level == 5; "
        "assert cfg.resolve_module_level('app.db', 'TRACE') == 5"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr


@pytest.mark.parametrize("bad_level", [True, False, "BASIC_FORMAT", "_STYLES", "UNKNOWN"])
def test_logging_config_rejects_invalid_and_boolean_levels(bad_level):
    with pytest.raises(ValueError):
        LoggingConfig(level=bad_level)  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        LoggingConfig(module_levels={"app": bad_level})  # type: ignore[dict-item]


@pytest.mark.parametrize("bad_retention", [0, -1, True, False, "7", 1.5])
def test_logging_config_rejects_invalid_retention_types_and_bounds(bad_retention):
    with pytest.raises(ValueError, match="rotate_retention_count"):
        LoggingConfig(rotate_schedule="day", rotate_retention_count=bad_retention)  # type: ignore[arg-type]


def test_builder_default_matches_logging_config():
    built = LoggingConfigBuilder().build()
    assert built == LoggingConfig()
    assert built.level == 20


def test_builder_with_json_console_only_clears_json_file_name():
    from arlogi.handler_factory import HandlerFactory
    from arlogi.handlers import JSONHandler

    config = LoggingConfigBuilder().with_json_file("logs/app.jsonl").with_json_console_only().build()
    assert config.json_file_name is None
    assert config.json_file_only is True
    assert config.show_console is False

    handlers = HandlerFactory.create_handlers(config)
    assert len(handlers) == 1
    assert isinstance(handlers[0], JSONHandler)
    handlers[0].close()


@pytest.mark.parametrize("bad_schedule", ["invalid", "", ["day"], {"schedule": "day"}, 123])
def test_json_file_handler_rejects_invalid_schedule_without_side_effects(tmp_path, bad_schedule):
    target = tmp_path / "sub" / "app.jsonl"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ResourceWarning)
        with pytest.raises(ValueError, match="Invalid rotate_schedule"):
            JSONFileHandler(str(target), rotate_schedule=bad_schedule)  # type: ignore[arg-type]
        gc.collect()

    assert not (tmp_path / "sub").exists()
    assert not any(issubclass(w.category, ResourceWarning) for w in caught)


@pytest.mark.parametrize("bad_schedule", [["day"], {"schedule": "day"}, 123])
def test_logging_config_rejects_unhashable_and_non_str_rotate_schedule(bad_schedule):
    with pytest.raises(ValueError, match="Invalid rotate_schedule"):
        LoggingConfig(rotate_schedule=bad_schedule)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_retention", [0, -1, True, False, "7"])
def test_json_file_handler_rejects_invalid_retention_count(tmp_path, bad_retention):
    target = tmp_path / "app.jsonl"
    with pytest.raises(ValueError, match="rotate_retention_count"):
        JSONFileHandler(str(target), rotate_retention_count=bad_retention)  # type: ignore[arg-type]
    assert not target.exists()


@pytest.mark.parametrize("bad_name", ["", "   ", 123])
def test_empty_or_non_string_json_file_name_rejected(tmp_path, bad_name):
    with pytest.raises(ValueError, match="non-empty string"):
        LoggingConfig(json_file_name=bad_name, json_file_base_dir=str(tmp_path))  # type: ignore[arg-type]


def test_empty_json_file_name_rejected_across_entrypoints(tmp_path):
    with pytest.raises(ValueError, match="non-empty"):
        LoggingConfigBuilder().with_json_file("").build()

    with pytest.raises(ValueError, match="non-empty"):
        setup_logging(json_file_name="", json_file_base_dir=str(tmp_path))

    with pytest.raises(ValueError, match="non-empty"):
        get_json_logger("audit_empty", "")

    with pytest.raises(ValueError, match="non-empty"):
        get_json_logger("audit_empty_base", "", base_dir=str(tmp_path))

    stderr_logger = get_json_logger("audit_stderr")
    import logging

    raw = logging.getLogger("arlogi.json.audit_stderr")
    assert len(raw.handlers) == 1
    assert isinstance(raw.handlers[0], JSONHandler)
    assert stderr_logger is raw


def test_builder_with_json_console_only_clears_base_dir():
    config = (
        LoggingConfigBuilder().with_json_file("a.jsonl").with_json_base_dir("/tmp").with_json_console_only().build()
    )
    assert config.json_file_name is None
    assert config.json_file_base_dir is None
    assert config.json_file_only is True


@pytest.mark.parametrize("bad_base_dir", ["", "   ", 123, True, "\x00"])
def test_invalid_json_file_base_dir_rejected_without_side_effects(tmp_path, monkeypatch, bad_base_dir):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError, match="base_dir"):
        LoggingConfig(json_file_name="app.jsonl", json_file_base_dir=bad_base_dir)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="base_dir"):
        LoggingConfigBuilder().with_json_file("app.jsonl").with_json_base_dir(bad_base_dir).build()  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="base_dir"):
        get_json_logger("audit_bad_base", "app.jsonl", base_dir=bad_base_dir)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="base_dir"):
        JSONFileHandler("app.jsonl", base_dir=bad_base_dir)  # type: ignore[arg-type]

    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("bad_name", ["", "   ", 123, "\x00"])
def test_json_file_handler_rejects_invalid_filename_without_base_dir(tmp_path, monkeypatch, bad_name):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="non-empty"):
        JSONFileHandler(bad_name)  # type: ignore[arg-type]
    assert list(tmp_path.iterdir()) == []
