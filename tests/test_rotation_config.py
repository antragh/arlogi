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
