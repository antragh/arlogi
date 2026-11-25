import glob
import logging
import os
from datetime import datetime

from arlogi import cleanup_json_logger, get_json_logger, rotate_json_logger
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


def test_emit_boundary_rotation_uses_elapsed_period_key(tmp_path):
    log_file = tmp_path / "app.jsonl"
    handler = JSONFileHandler(str(log_file), rotate_schedule="day")

    times = [
        datetime(2026, 6, 10, 23, 59, 59),
        datetime(2026, 6, 10, 23, 59, 59),
        datetime(2026, 6, 11, 0, 0, 1),
        datetime(2026, 6, 11, 12, 0, 0),
    ]
    handler._now_local = lambda: times.pop(0)  # type: ignore[attr-defined]
    handler._active_period_key = handler._compute_period_key(handler._now_local())

    _emit(handler, "june-10-event")
    _emit(handler, "june-11-event")

    assert (tmp_path / "app-2026-06-10.jsonl").exists()
    assert "june-10-event" in (tmp_path / "app-2026-06-10.jsonl").read_text(encoding="utf-8")

    assert handler.rotate_now() is True
    assert (tmp_path / "app-2026-06-11.jsonl").exists()
    assert not (tmp_path / "app-2026-06-11.1.jsonl").exists()
    handler.close()


def test_pruning_preserves_sibling_files_and_works_in_bracketed_dirs(tmp_path):
    bracket_dir = tmp_path / "svc[v2]"
    bracket_dir.mkdir()
    log_file = bracket_dir / "app.jsonl"
    sibling_file = bracket_dir / "app-audit.jsonl"
    sibling_file.write_text('{"msg": "keep"}\n', encoding="utf-8")

    handler = JSONFileHandler(str(log_file), rotate_schedule="hour", rotate_retention_count=1)
    for hour in [10, 11, 12]:
        handler._now_local = lambda h=hour: datetime(2026, 6, 10, h, 0, 0)  # type: ignore[attr-defined]
        _emit(handler, f"hour-{hour}")
        handler.rotate_now()

    assert sibling_file.exists()
    archives = [p.name for p in bracket_dir.iterdir() if p.name.startswith("app-2026-")]
    assert len(archives) == 1
    handler.close()


def test_base_dir_containment_rejects_traversal_and_directory_equal(tmp_path):
    import pytest

    with pytest.raises(ValueError, match="escapes base directory"):
        JSONFileHandler("../escape.jsonl", base_dir=tmp_path)

    with pytest.raises(ValueError, match="escapes base directory"):
        JSONFileHandler(".", base_dir=tmp_path)

    with pytest.raises(ValueError, match="escapes base directory"):
        JSONFileHandler(str(tmp_path), base_dir=tmp_path)


def test_rotate_now_non_fatal_when_reopen_fails(tmp_path):
    from unittest.mock import patch

    log_file = tmp_path / "app.jsonl"
    handler = JSONFileHandler(str(log_file), rotate_schedule="day")
    _emit(handler, "entry")

    with patch.object(handler, "_open", side_effect=OSError("ENOSPC")):
        assert handler.rotate_now() is False
    handler.close()


def test_boundary_rotation_advances_key_and_prunes_when_reopen_fails(tmp_path):
    from unittest.mock import patch

    log_file = tmp_path / "app.jsonl"
    old_archive = tmp_path / "app-2026-06-08.jsonl"
    old_archive.write_text('{"msg": "old"}\n', encoding="utf-8")

    handler = JSONFileHandler(str(log_file), rotate_schedule="day", rotate_retention_count=1)
    times = [
        datetime(2026, 6, 10, 23, 0, 0),
        datetime(2026, 6, 11, 0, 1, 0),
        datetime(2026, 6, 11, 0, 2, 0),
    ]
    handler._now_local = lambda: times.pop(0)  # type: ignore[method-assign]
    handler._active_period_key = "2026-06-10"

    _emit(handler, "day1-msg")

    real_open = handler._open
    open_calls = 0

    def _fail_first_reopen():
        nonlocal open_calls
        open_calls += 1
        if open_calls == 1:
            raise OSError("ENOSPC")
        return real_open()

    with patch.object(handler, "handleError") as mock_err:
        with patch.object(handler, "_open", side_effect=_fail_first_reopen):
            _emit(handler, "day2-msg1")
        assert mock_err.call_count <= 1

    assert handler._active_period_key == "2026-06-11"
    assert not old_archive.exists()
    assert (tmp_path / "app-2026-06-10.jsonl").exists()

    _emit(handler, "day2-msg2")
    handler.close()

    assert (tmp_path / "app-2026-06-10.jsonl").exists()
    assert not (tmp_path / "app-2026-06-10.1.jsonl").exists()


def test_pruning_ignores_newer_matching_dir_and_symlink(tmp_path):
    log_file = tmp_path / "app.jsonl"
    real_archive = tmp_path / "app-2026-06-10.jsonl"
    real_archive.write_text('{"msg": "old"}\n', encoding="utf-8")
    os.utime(real_archive, ns=(1_000_000_000, 1_000_000_000))

    newer_dir = tmp_path / "app-2026-06-15.jsonl"
    newer_dir.mkdir()
    os.utime(newer_dir, ns=(5_000_000_000, 5_000_000_000))

    newer_symlink = tmp_path / "app-2026-06-16.jsonl"
    newer_symlink.symlink_to(real_archive)

    handler = JSONFileHandler(str(log_file), rotate_schedule="day", rotate_retention_count=2)
    handler._now_local = lambda: datetime(2026, 6, 17, 12, 0, 0)  # type: ignore[method-assign]
    handler._active_period_key = "2026-06-17"
    _emit(handler, "new")
    assert handler.rotate_now() is True
    handler.close()

    assert real_archive.exists()
    assert (tmp_path / "app-2026-06-17.jsonl").exists()
    assert newer_dir.is_dir()
    assert newer_symlink.is_symlink()


def test_pruning_equal_mtime_keeps_higher_collision_suffixes(tmp_path):
    log_file = tmp_path / "app.jsonl"
    handler = JSONFileHandler(str(log_file), rotate_schedule="day", rotate_retention_count=2)

    equal_ns = 1_700_000_000_000_000_000
    for name in ("app-2026-06-10.jsonl", "app-2026-06-10.1.jsonl"):
        p = tmp_path / name
        p.write_text("old\n", encoding="utf-8")
        os.utime(p, ns=(equal_ns, equal_ns))

    handler._now_local = lambda: datetime(2026, 6, 10, 12, 0, 0)  # type: ignore[method-assign]
    handler._active_period_key = "2026-06-10"
    _emit(handler, "third")
    # Patch os.utime on the newly created .2.jsonl by calling _prune_rotated_files after equalizing mtime
    _emit(handler, "keep-open")
    target2 = tmp_path / "app-2026-06-10.2.jsonl"
    target2.write_text("two\n", encoding="utf-8")
    for name in ("app-2026-06-10.jsonl", "app-2026-06-10.1.jsonl", "app-2026-06-10.2.jsonl"):
        os.utime(tmp_path / name, ns=(equal_ns, equal_ns))

    handler._prune_rotated_files()
    handler.close()

    surviving_archives = sorted(p.name for p in tmp_path.glob("app-2026-*.jsonl"))
    assert surviving_archives == ["app-2026-06-10.1.jsonl", "app-2026-06-10.2.jsonl"]


def test_unscheduled_manual_rotation_uses_current_hour_and_no_frozen_key(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    logger = get_json_logger("audit_unscheduled", str(log_path))
    raw_logger = logging.getLogger("arlogi.json.audit_unscheduled")
    handler = raw_logger.handlers[0]
    assert isinstance(handler, JSONFileHandler)

    try:
        timestamps = [
            datetime(2026, 6, 10, 10, 0, 0),
            datetime(2026, 6, 13, 15, 0, 0),
            datetime(2026, 7, 1, 9, 0, 0),
        ]
        handler._now_local = lambda: timestamps.pop(0)  # type: ignore[method-assign]

        for i in range(3):
            logger.info(f"event-{i}")
            assert rotate_json_logger("audit_unscheduled") == 1

        archives = sorted(p.name for p in tmp_path.glob("audit-*.jsonl"))
        assert archives == [
            "audit-2026-06-10-10.jsonl",
            "audit-2026-06-13-15.jsonl",
            "audit-2026-07-01-09.jsonl",
        ]
        assert handler._active_period_key is None
    finally:
        cleanup_json_logger("audit_unscheduled")


def test_unscheduled_empty_noop_does_not_freeze_archive_name(tmp_path):
    log_path = tmp_path / "audit2.jsonl"
    handler = JSONFileHandler(str(log_path))
    times = [datetime(2026, 6, 10, 10, 0, 0), datetime(2026, 7, 1, 9, 0, 0)]
    handler._now_local = lambda: times.pop(0)  # type: ignore[method-assign]

    assert handler.rotate_now() is False
    assert handler._active_period_key is None

    _emit(handler, "after-noop")
    assert handler.rotate_now() is True
    handler.close()

    assert (tmp_path / "audit2-2026-07-01-09.jsonl").exists()
    assert not (tmp_path / "audit2-2026-06-10-10.jsonl").exists()


def test_scheduled_manual_rotation_after_boundary_uses_elapsed_period_key(tmp_path):
    log_path = tmp_path / "app.jsonl"
    times = [
        datetime(2026, 6, 10, 23, 0, 0),
        datetime(2026, 6, 11, 0, 5, 0),
        datetime(2026, 6, 11, 12, 0, 0),
    ]
    handler = JSONFileHandler(str(log_path), rotate_schedule="day")
    handler._now_local = lambda: times.pop(0)  # type: ignore[method-assign]
    handler._active_period_key = "2026-06-10"

    _emit(handler, "day-one-event")
    assert handler.rotate_now() is True
    handler.close()

    assert (tmp_path / "app-2026-06-10.jsonl").exists()
    assert not (tmp_path / "app-2026-06-11.jsonl").exists()
    assert handler._active_period_key == "2026-06-11"
