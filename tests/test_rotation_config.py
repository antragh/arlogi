import subprocess
import sys

import pytest

from arlogi import setup_logging
from arlogi.config import LoggingConfig
from arlogi.config_builder import LoggingConfigBuilder


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
