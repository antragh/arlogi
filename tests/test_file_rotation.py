import glob
import logging
from datetime import datetime

from arlogi import get_json_logger, rotate_json_logger
from arlogi.handlers import JSONFileHandler


def _emit(handler: JSONFileHandler, message: str) -> None:
    handler.emit(
        logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg=message,
            args=(),
            exc_info=None,
        )
    )


def test_period_key_generation(tmp_path):
    log_file = tmp_path / "app.jsonl"

    hour_handler = JSONFileHandler(str(log_file), rotate_schedule="hour")
    assert hour_handler._compute_period_key(datetime(2026, 6, 10, 14, 45)) == "2026-06-10-14"

    day_handler = JSONFileHandler(str(log_file), rotate_schedule="day")
    assert day_handler._compute_period_key(datetime(2026, 6, 10, 14, 45)) == "2026-06-10"

    week_handler = JSONFileHandler(str(log_file), rotate_schedule="week")
    assert week_handler._compute_period_key(datetime(2026, 6, 10, 14, 45)) == "2026-W23"

    month_handler = JSONFileHandler(str(log_file), rotate_schedule="month")
    assert month_handler._compute_period_key(datetime(2026, 6, 10, 14, 45)) == "2026-06"

    hour_handler.close()
    day_handler.close()
    week_handler.close()
    month_handler.close()


def test_rotate_now_moves_to_suffixed_file(tmp_path):
    log_file = tmp_path / "app.jsonl"
    handler = JSONFileHandler(str(log_file), rotate_schedule="day")

    _emit(handler, "before rotate")
    rotated = handler.rotate_now()

    assert rotated is True
    assert log_file.exists()

    rotated_files = glob.glob(str(tmp_path / "app-*.jsonl"))
    assert len(rotated_files) == 1

    handler.close()


def test_rotate_now_is_noop_for_empty_file(tmp_path):
    log_file = tmp_path / "app.jsonl"
    handler = JSONFileHandler(str(log_file), rotate_schedule="day")

    assert handler.rotate_now() is False

    handler.close()


def test_emit_rotates_on_period_boundary(tmp_path):
    log_file = tmp_path / "app.jsonl"
    handler = JSONFileHandler(str(log_file), rotate_schedule="day")

    times = [
        datetime(2026, 6, 10, 23, 59, 59),
        datetime(2026, 6, 10, 23, 59, 59),
        datetime(2026, 6, 11, 0, 0, 1),
    ]

    def fake_now_local() -> datetime:
        return times.pop(0)

    handler._now_local = fake_now_local  # type: ignore[attr-defined]
    handler._active_period_key = handler._compute_period_key(handler._now_local())

    _emit(handler, "day-1")
    _emit(handler, "day-2")

    rotated_files = glob.glob(str(tmp_path / "app-*.jsonl"))
    assert len(rotated_files) == 1

    handler.close()


def test_retention_prunes_old_rotated_files(tmp_path):
    log_file = tmp_path / "app.jsonl"
    handler = JSONFileHandler(
        str(log_file),
        rotate_schedule="hour",
        rotate_retention_count=2,
    )

    for hour in [10, 11, 12, 13]:
        handler._now_local = lambda h=hour: datetime(2026, 6, 10, h, 0, 0)  # type: ignore[attr-defined]
        _emit(handler, f"hour-{hour}")
        handler.rotate_now()

    rotated_files = sorted(glob.glob(str(tmp_path / "app-*.jsonl")))
    assert len(rotated_files) == 2

    handler.close()


def test_rotate_json_logger_helper(tmp_path):
    log_file = tmp_path / "helper.jsonl"
    logger = get_json_logger("rotation-helper", str(log_file))
    logger.info("hello")

    rotated_count = rotate_json_logger("rotation-helper")

    assert rotated_count == 1
