"""Rotating JSONL file writer shared by the span and metric exporters."""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import IO

logger = logging.getLogger(__name__)


class _RotatingJsonlWriter:
    """Appends lines to `<directory>/<prefix>-YYYYMMDD-HHMMSS.jsonl`.

    A new file is started when the current one is older than `rotate_hours`;
    afterwards only the newest `retention_count` matching files are kept.
    I/O errors mark the writer broken (one warning, then silent no-op) —
    telemetry must never break the host application.
    """

    def __init__(self, directory: str | Path, prefix: str, rotate_hours: int, retention_count: int) -> None:
        self._directory = Path(directory)
        self._prefix = prefix
        self._rotate_seconds = rotate_hours * 3600
        self._retention_count = retention_count
        self._stream: IO[str] | None = None
        self._opened_at = 0.0
        self._broken = False

    def _now(self) -> float:
        """Test seam, mirroring JSONFileHandler._now_local."""
        return time.time()

    def write_line(self, line: str) -> bool:
        if self._broken:
            return False
        try:
            if self._stream is None or self._stream.closed or self._now() - self._opened_at >= self._rotate_seconds:
                self._open_new_file()
            assert self._stream is not None
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
        self._opened_at = self._now()
        self._prune()

    def _prune(self) -> None:
        files = sorted(
            self._directory.glob(f"{self._prefix}-*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for old in files[self._retention_count :]:
            try:
                old.unlink()
            except OSError:
                continue  # pruning failures must never break telemetry

    def close(self) -> None:
        if self._stream is not None and not self._stream.closed:
            try:
                self._stream.close()
            except OSError:
                pass
        self._stream = None
