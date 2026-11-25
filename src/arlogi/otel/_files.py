"""Rotating JSONL file writer shared by the span and metric exporters."""

import errno
import logging
import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import IO

from .._rotation import prune_archives

logger = logging.getLogger(__name__)

_FORBIDDEN_PREFIX_CHARS = frozenset({"\x00", "/", "\\", "*", "?", "[", "]"})
_MAX_COLLISION_SUFFIX = 1000


def _validate_prefix(prefix: str) -> str:
    """Validate that prefix is a safe single filename component."""
    if not isinstance(prefix, str) or not prefix or prefix in (".", ".."):
        raise ValueError(f"Invalid telemetry file prefix: {prefix!r}")
    if ".." in prefix or any(ch in _FORBIDDEN_PREFIX_CHARS for ch in prefix) or Path(prefix).name != prefix:
        raise ValueError(f"Invalid telemetry file prefix: {prefix!r}")
    return prefix


def _validate_positive_int(value: int, name: str) -> int:
    """Validate that value is a non-boolean integer >= 1."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be an integer >= 1, got {value!r}")
    return value


class _RotatingJsonlWriter:
    """Appends lines to `<directory>/<prefix>-YYYYMMDD-HHMMSS.jsonl`.

    A new file is started when the current one is older than `rotate_hours`;
    afterwards only the newest `retention_count` matching files are kept.
    I/O errors mark the writer broken (one warning, then silent no-op) —
    telemetry must never break the host application.
    """

    def __init__(self, directory: str | Path, prefix: str, rotate_hours: int, retention_count: int) -> None:
        self._directory = Path(directory)
        self._prefix = _validate_prefix(prefix)
        validated_hours = _validate_positive_int(rotate_hours, "rotate_hours")
        self._rotate_seconds = validated_hours * 3600
        self._retention_count = _validate_positive_int(retention_count, "retention_count")
        self._archive_pattern = re.compile(
            rf"^{re.escape(self._prefix)}-(?P<stamp>\d{{8}}-\d{{6}})(?:\.(?P<suffix>\d+))?\.jsonl$"
        )
        self._stream: IO[str] | None = None
        self._active_path: Path | None = None
        self._opened_at = 0.0
        self._broken = False
        self._closed = False
        self._lock = threading.Lock()

    def _now(self) -> float:
        """Test seam, mirroring JSONFileHandler._now_local."""
        return time.time()

    def _close_stream_locked(self) -> None:
        """Best-effort close and clear self._stream while holding self._lock."""
        if self._stream is not None and not self._stream.closed:
            try:
                self._stream.close()
            except OSError:
                pass
        self._stream = None

    def write_line(self, line: str) -> bool:
        if self._broken or self._closed:
            return False
        with self._lock:
            if self._broken or self._closed:
                return False
            try:
                if self._stream is None or self._stream.closed or self._now() - self._opened_at >= self._rotate_seconds:
                    self._open_new_file()
                if self._stream is None:
                    self._broken = True
                    logger.warning("Telemetry file writer stream is None after opening file")
                    return False
                self._stream.write(line + "\n")
                self._stream.flush()
                return True
            except OSError as exc:
                self._broken = True
                self._close_stream_locked()
                logger.warning("Telemetry file writer disabled after I/O error: %s", exc)
                return False

    def _open_new_file(self) -> None:
        if self._stream is not None and not self._stream.closed:
            self._stream.close()
        self._directory.mkdir(parents=True, exist_ok=True)
        stamp = datetime.fromtimestamp(self._now()).strftime("%Y%m%d-%H%M%S")
        flags = (
            os.O_WRONLY
            | os.O_APPEND
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_BINARY", 0)
        )
        target = self._directory / f"{self._prefix}-{stamp}.jsonl"
        fd: int | None = None
        for suffix in range(_MAX_COLLISION_SUFFIX + 1):
            name = f"{self._prefix}-{stamp}.jsonl" if suffix == 0 else f"{self._prefix}-{stamp}.{suffix}.jsonl"
            target = self._directory / name
            try:
                fd = os.open(target, flags, 0o666)
                break
            except (FileExistsError, IsADirectoryError):
                continue
            except OSError as exc:
                if exc.errno == errno.ELOOP:
                    continue
                raise
        if fd is None:
            raise OSError(
                errno.EEXIST, "no free telemetry file name", str(self._directory / f"{self._prefix}-{stamp}.jsonl")
            )
        try:
            self._stream = os.fdopen(fd, "a", encoding="utf-8")
        except Exception:
            os.close(fd)
            raise
        self._active_path = target.resolve()
        self._opened_at = self._now()
        self._prune()

    def _prune(self) -> None:
        archived_keep = max(0, self._retention_count - 1) if self._active_path is not None else self._retention_count
        prune_archives(self._directory, self._archive_pattern, archived_keep, active_path=self._active_path)

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._active_path = None
            self._close_stream_locked()
