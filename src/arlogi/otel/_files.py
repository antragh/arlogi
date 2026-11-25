"""Rotating JSONL file writer shared by the span and metric exporters."""

import logging
import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import IO

logger = logging.getLogger(__name__)

_FORBIDDEN_PREFIX_CHARS = frozenset({"\x00", "/", "\\", "*", "?", "[", "]"})


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
        self._archive_pattern = re.compile(rf"^{re.escape(self._prefix)}-\d{{8}}-\d{{6}}(?:\.\d+)?\.jsonl$")
        self._stream: IO[str] | None = None
        self._active_path: Path | None = None
        self._opened_at = 0.0
        self._broken = False
        self._lock = threading.Lock()

    def _now(self) -> float:
        """Test seam, mirroring JSONFileHandler._now_local."""
        return time.time()

    def write_line(self, line: str) -> bool:
        if self._broken:
            return False
        with self._lock:
            if self._broken:
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
                logger.warning("Telemetry file writer disabled after I/O error: %s", exc)
                return False

    def _open_new_file(self) -> None:
        if self._stream is not None and not self._stream.closed:
            self._stream.close()
        self._directory.mkdir(parents=True, exist_ok=True)
        stamp = datetime.fromtimestamp(self._now()).strftime("%Y%m%d-%H%M%S")
        target = self._directory / f"{self._prefix}-{stamp}.jsonl"
        suffix = 1
        while target.exists():
            target = self._directory / f"{self._prefix}-{stamp}.{suffix}.jsonl"
            suffix += 1
        self._stream = target.open("a", encoding="utf-8")
        self._active_path = target.resolve()
        self._opened_at = self._now()
        self._prune()

    def _prune(self) -> None:
        try:
            candidates: list[tuple[float, Path]] = []
            with os.scandir(self._directory) as entries:
                for entry in entries:
                    if not self._archive_pattern.match(entry.name):
                        continue
                    entry_path = Path(entry.path)
                    if self._active_path is not None:
                        try:
                            if entry_path.resolve() == self._active_path:
                                continue
                        except OSError:
                            pass
                    try:
                        candidates.append((entry.stat().st_mtime, entry_path))
                    except OSError:
                        continue

            candidates.sort(key=lambda item: item[0], reverse=True)
            archived_keep = (
                max(0, self._retention_count - 1) if self._active_path is not None else self._retention_count
            )
            for _, old in candidates[archived_keep:]:
                try:
                    old.unlink()
                except OSError:
                    continue  # pruning failures must never break telemetry
        except OSError:
            return

    def close(self) -> None:
        with self._lock:
            if self._stream is not None and not self._stream.closed:
                try:
                    self._stream.close()
                except OSError:
                    pass
            self._stream = None
