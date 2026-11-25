"""Logging handlers for arlogi.

This module provides custom logging handlers including:
- ColoredConsoleHandler: Rich-based colored console output
- JSONHandler/JSONFileHandler: Structured JSON logging
- ArlogiSyslogHandler: Syslog integration with fallback support
"""

import json
import logging
import logging.handlers
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.logging import RichHandler


class ColoredConsoleHandler(RichHandler):
    """A logging handler that uses rich for colored console output.

    Features:
    - Automatic project root detection for relative file paths (cached)
    - Customizable color schemes per log level
    - Rich traceback support
    - Compact single-character level indicators (T, D, I, W, E, C)
    """

    # Class-level cache for project root to avoid repeated filesystem operations
    _project_root_cache: str | None = None

    def __init__(
        self,
        show_time: bool = False,
        show_level: bool = True,
        show_path: bool = True,
        level_styles: dict[str, str] | None = None,
        project_root: str | None = None,
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize the colored console handler.

        Args:
            show_time: Whether to show timestamps in output
            show_level: Whether to show log levels
            show_path: Whether to show file paths
            level_styles: Custom color styles per level (e.g., {"info": "blue"})
            project_root: Project root for relative path calculation
            *args: Additional positional arguments for RichHandler
            **kwargs: Additional keyword arguments for RichHandler
        """
        # Default level styles: INFO is lighter (grey75) than DEBUG/TRACE (grey37)
        default_styles = {
            "trace": "grey37",
            "debug": "grey37",
            "info": "grey75",
            "warning": "yellow",
            "error": "red",
            "critical": "bold red",
        }
        if level_styles:
            default_styles.update(level_styles)

        # Default to a console that supports colors and directed to stdout
        if "console" not in kwargs:
            kwargs["console"] = Console(force_terminal=True, file=sys.stdout)

        # Enable rich tracebacks by default for enhanced error display
        kwargs.setdefault("rich_tracebacks", True)
        # Render log messages literally by default: message text may carry
        # attacker-influenced content, so Rich markup must not be enabled
        # unless the application explicitly opts in.
        kwargs.setdefault("markup", False)

        super().__init__(
            *args,
            show_time=show_time,
            show_level=show_level,
            show_path=show_path,
            **kwargs,
        )

        # Set level styles after initialization (for compatibility with older rich versions)
        self.level_styles = default_styles

        # Store project root for relative path calculation (use cache if available)
        self.project_root = project_root or self._find_project_root()

    def _find_project_root(self) -> str:
        """Find the project root by looking for common indicators.

        Searches upward from the current directory for files like
        .git, pyproject.toml, setup.py, etc.

        Result is cached at class level to avoid repeated filesystem operations.

        Returns:
            The absolute path to the project root, or current directory if not found
        """
        # Return cached value if available
        if ColoredConsoleHandler._project_root_cache is not None:
            return ColoredConsoleHandler._project_root_cache

        current = os.getcwd()

        # Common project root indicators
        indicators = [
            ".git",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "requirements.txt",
            "Pipfile",
            "poetry.lock",
            ".hg",
            ".svn",
        ]

        # Walk up the directory tree looking for indicators
        while current != os.path.dirname(current):  # Stop at filesystem root
            for indicator in indicators:
                if os.path.exists(os.path.join(current, indicator)):
                    ColoredConsoleHandler._project_root_cache = os.path.abspath(current)
                    return ColoredConsoleHandler._project_root_cache
            current = os.path.dirname(current)

        # If no indicators found, fall back to current working directory
        ColoredConsoleHandler._project_root_cache = os.getcwd()
        return ColoredConsoleHandler._project_root_cache

    def render(
        self,
        *,
        record: logging.LogRecord,
        traceback: Any,
        message_renderable: Any,
    ) -> Any:
        """Override render method to show relative paths from project root.

        Args:
            record: The log record to render
            traceback: Optional traceback information
            message_renderable: The formatted message

        Returns:
            A renderable object for Rich to display
        """
        from pathlib import Path

        # Calculate relative path instead of just filename
        try:
            relpath = os.path.relpath(record.pathname, self.project_root)
            path = relpath
        except (ValueError, OSError):
            # Fallback to filename if relative path calculation fails
            path = Path(record.pathname).name

        level = self.get_level_text(record)
        time_format = None if self.formatter is None else self.formatter.datefmt
        from datetime import datetime

        log_time = datetime.fromtimestamp(record.created)

        log_renderable = self._log_render(
            self.console,
            [message_renderable] if not traceback else [message_renderable, traceback],
            log_time=log_time,
            time_format=time_format,
            level=level,
            path=path,
            line_no=record.lineno,
            link_path=None,  # Disable links to avoid file:// URLs
        )
        return log_renderable

    def get_level_text(self, record: logging.LogRecord) -> Any:
        """Get level text as a single character with styling.

        Args:
            record: The log record

        Returns:
            A Rich Text object with the level character
        """
        from rich.text import Text

        level_name = record.levelname
        # Map TRACE to T, DEBUG to D, etc.
        char = level_name[0]

        style = self.level_styles.get(level_name.lower(), "default")
        # Compact single character indicator
        return Text(f"{char} ", style=style)

    def render_message(self, record: logging.LogRecord, message: str) -> Any:
        """Render message text with level-specific styling.

        Args:
            record: The log record
            message: The message to render

        Returns:
            A Rich Text object with the styled message
        """
        use_markup = getattr(record, "markup", self.markup)
        attribution = record.__dict__.get("_arlogi_attribution")
        if use_markup and isinstance(attribution, str):
            from rich.markup import escape

            raw_suffix = f"[{attribution}]"
            if message.endswith(raw_suffix):
                message = message[: -len(raw_suffix)] + escape(raw_suffix)

        message_text = super().render_message(record, message)

        # Apply style to the entire message text
        level_name = record.levelname.lower()
        style = self.level_styles.get(level_name, "default")

        message_text.style = style
        return message_text


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured log output.

    Outputs log records as JSON with standard fields plus any extra
    fields added via the `extra` parameter.

    Includes robust error handling for JSON serialization failures.
    """

    _PROTECTED_ENVELOPE_KEYS = frozenset(
        {
            "timestamp",
            "level",
            "logger_name",
            "message",
            "module",
            "function",
            "line_number",
            "exception",
        }
    )

    _STANDARD_RECORD_ATTRS = frozenset(
        {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
            "taskName",
        }
    )

    @staticmethod
    def _safe_str(value: Any) -> str:
        """Convert value to string without raising."""
        try:
            return str(value)
        except Exception:
            return f"<unrepresentable {type(value).__name__}>"

    def _merge_extra_fields(self, record: logging.LogRecord, log_data: dict[str, Any]) -> None:
        """Merge non-standard record attributes into log_data without clobbering envelope keys."""
        collisions: dict[str, Any] = {}
        has_user_extra = False
        user_extra: Any = None

        for key, value in record.__dict__.items():
            if key in self._STANDARD_RECORD_ATTRS or key.startswith("_"):
                continue
            if key == "extra":
                has_user_extra = True
                user_extra = value
            elif key in self._PROTECTED_ENVELOPE_KEYS:
                collisions[key] = value
            else:
                log_data[key] = value

        if collisions:
            if has_user_extra:
                collisions["extra"] = user_extra
            log_data["extra"] = collisions
        elif has_user_extra:
            log_data["extra"] = user_extra

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: The log record to format

        Returns:
            JSON string representation of the log record

        Note:
            If JSON serialization fails, falls back to a basic format
            with error information to prevent logging crashes.
        """
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        try:
            message = record.getMessage()
        except Exception:
            message = self._safe_str(record.msg)

        log_data: dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger_name": record.name,
            "message": message,
            "module": record.module,
            "function": record.funcName,
            "line_number": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        self._merge_extra_fields(record, log_data)

        try:
            return json.dumps(log_data, default=str)
        except Exception as e:
            return json.dumps(
                {
                    "timestamp": timestamp,
                    "level": record.levelname,
                    "logger_name": record.name,
                    "message": self._safe_str(message),
                    "module": record.module,
                    "function": record.funcName,
                    "line_number": record.lineno,
                    "error": f"JSON serialization failed: {self._safe_str(e)}",
                },
                default=str,
            )


class JSONHandler(logging.StreamHandler):
    """A logging handler that outputs log records as JSON to a stream.

    Defaults to stderr for compatibility with log aggregation tools.

    Properly manages custom streams to prevent resource leaks.
    """

    def __init__(self, stream: Any = None):
        """Initialize the JSON stream handler.

        Args:
            stream: The stream to write to (defaults to sys.stderr if None)

        Note:
            Custom streams are tracked and closed when the handler is closed.
            System streams (sys.stderr, sys.stdout) are not closed.
        """
        # Track whether we own the stream for cleanup purposes
        self._owns_stream = stream is not None
        self._closed = False
        super().__init__(stream)
        self.setFormatter(JSONFormatter())

    def close(self):
        """Close the handler and the stream if we own it.

        Only closes custom streams, not system streams like sys.stderr.
        """
        self.acquire()
        try:
            if self._closed:
                return
            self._closed = True
            try:
                stream = self.stream
                if stream is not None and not getattr(stream, "closed", False):
                    self.flush()

                if self._owns_stream and stream is not None and hasattr(stream, "close"):
                    if stream not in (sys.stderr, sys.stdout):
                        if not getattr(stream, "closed", False):
                            stream.close()
                        self.stream = None
            finally:
                super().close()
        finally:
            self.release()


class JSONFileHandler(logging.FileHandler):
    """A logging handler that outputs log records as JSON to a file.

    Automatically creates parent directories if they don't exist.
    """

    def __init__(
        self,
        filename: str,
        mode: str = "a",
        encoding: str | None = None,
        delay: bool = False,
        rotate_schedule: str | None = None,
        rotate_retention_count: int | None = None,
        base_dir: str | Path | None = None,
    ):
        """Initialize the JSON file handler.

        Args:
            filename: Path to the log file
            mode: File open mode (default: "a" for append)
            encoding: File encoding (default: None for system default)
            delay: Whether to delay file opening until first emit
            rotate_schedule: Optional rotation schedule (hour/day/week/month)
            rotate_retention_count: Optional retention count for rotated files
            base_dir: Optional base directory the log file must stay within.
                When provided, the resolved log path must remain inside
                ``base_dir``; traversal (``..``) outside of it is rejected.

        Note:
            Thread-safe: Uses exist_ok=True to safely handle concurrent
            directory creation from multiple threads.

        Raises:
            ValueError: If ``base_dir`` is set and the resolved log path
                escapes it (directory traversal attempt).
        """
        if base_dir is not None:
            resolved = self._resolve_within_base(filename, base_dir)
        else:
            resolved = os.path.abspath(filename)

        # Ensure parent directory exists
        # Thread-safe: exist_ok=True handles race conditions where multiple
        # threads might try to create the same directory
        parent_dir = os.path.dirname(resolved)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        super().__init__(resolved, mode, encoding, delay)
        self._closed = False
        self.rotate_schedule = rotate_schedule
        # Retention default is only applied when schedule is enabled.
        self.rotate_retention_count = (
            rotate_retention_count if rotate_retention_count is not None else (7 if rotate_schedule else None)
        )
        self._active_period_key = self._compute_period_key(self._now_local()) if self.rotate_schedule else None
        self.setFormatter(JSONFormatter())

    def close(self) -> None:
        """Close the handler and mark it closed so it will not reopen."""
        self.acquire()
        try:
            self._closed = True
            super().close()
        finally:
            self.release()

    @staticmethod
    def _resolve_within_base(filename: str, base_dir: str | Path) -> str:
        """Resolve ``filename`` against ``base_dir``, rejecting escapes.

        Args:
            filename: Log file path as supplied by the caller
            base_dir: Base directory the resolved path must stay within

        Returns:
            The resolved absolute path inside ``base_dir``

        Raises:
            ValueError: If ``filename`` is empty, equals ``base_dir``, or
                escapes ``base_dir``
        """
        if not filename or not filename.strip():
            raise ValueError("JSONFileHandler: filename must be a non-empty path")
        base = os.path.realpath(os.path.abspath(str(base_dir)))
        candidate = os.path.normpath(filename) if os.path.isabs(filename) else os.path.join(base, filename)
        resolved = os.path.realpath(candidate)
        if resolved == base or os.path.commonpath([base, resolved]) != base:
            raise ValueError(f"JSONFileHandler: log path {filename!r} escapes base directory {str(base_dir)!r}")
        return resolved

    def _now_local(self) -> datetime:
        """Get current local datetime.

        This indirection keeps schedule checks testable.
        """
        return datetime.now()

    def _compute_period_key(self, now_local: datetime) -> str:
        """Compute the period key for the configured schedule."""
        if self.rotate_schedule == "hour":
            return now_local.strftime("%Y-%m-%d-%H")
        if self.rotate_schedule == "day":
            return now_local.strftime("%Y-%m-%d")
        if self.rotate_schedule == "week":
            # %U is Sunday-based week number with Sunday as week boundary.
            return now_local.strftime("%Y-W%U")
        if self.rotate_schedule == "month":
            return now_local.strftime("%Y-%m")
        raise ValueError(f"Unsupported rotate_schedule: {self.rotate_schedule!r}")

    def _build_rotated_path(self, period_key: str) -> str:
        """Build target path for a rotated file."""
        root, ext = os.path.splitext(self.baseFilename)
        return f"{root}-{period_key}{ext}"

    def _build_collision_safe_path(self, base_target: str) -> str:
        """Return a unique rotated path by appending numeric suffixes when needed."""
        if not os.path.exists(base_target):
            return base_target

        root, ext = os.path.splitext(base_target)
        suffix = 1
        while True:
            candidate = f"{root}.{suffix}{ext}"
            if not os.path.exists(candidate):
                return candidate
            suffix += 1

    def _prune_rotated_files(self) -> None:
        """Prune old rotated files based on retention count."""
        if self.rotate_retention_count is None:
            return

        parent_dir = os.path.dirname(self.baseFilename) or "."
        stem, ext = os.path.splitext(os.path.basename(self.baseFilename))
        archive_pattern = re.compile(
            rf"^{re.escape(stem)}-(?:\d{{4}}-\d{{2}}(?:-\d{{2}}(?:-\d{{2}})?)?|\d{{4}}-W\d{{2}})"
            rf"(?:\.\d+)?{re.escape(ext)}$"
        )
        base_abs = os.path.abspath(self.baseFilename)

        try:
            candidates: list[tuple[float, str]] = []
            with os.scandir(parent_dir) as entries:
                for entry in entries:
                    if not archive_pattern.match(entry.name):
                        continue
                    if os.path.abspath(entry.path) == base_abs:
                        continue
                    try:
                        candidates.append((entry.stat().st_mtime, entry.path))
                    except OSError:
                        continue

            if len(candidates) <= self.rotate_retention_count:
                return

            candidates.sort(key=lambda item: item[0], reverse=True)
            for _, old_path in candidates[self.rotate_retention_count :]:
                try:
                    os.remove(old_path)
                except OSError:
                    # Pruning failures should never fail application logging.
                    continue
        except OSError:
            return

    def _rotation_key_for_emit(self) -> tuple[str, str] | None:
        """Return (archive_period_key, next_active_period_key) when emit should rotate."""
        if not self.rotate_schedule:
            return None

        current_key = self._compute_period_key(self._now_local())
        if self._active_period_key is None:
            self._active_period_key = current_key
            return None
        if current_key != self._active_period_key:
            return self._active_period_key, current_key
        return None

    def _ensure_stream_open(self) -> None:
        """Ensure file stream is available for writing."""
        if self.stream is None:
            self.stream = self._open()

    def _try_ensure_stream_open(self) -> None:
        """Best-effort stream reopen that never raises out of rotation recovery."""
        try:
            self._ensure_stream_open()
        except OSError:
            self._report_rotation_error()

    def _report_rotation_error(self) -> None:
        """Report an internal rotation error via handleError."""
        self.handleError(
            logging.LogRecord(
                name=__name__,
                level=logging.ERROR,
                pathname=__file__,
                lineno=0,
                msg="JSONFileHandler rotation failed",
                args=(),
                exc_info=sys.exc_info(),
            )
        )

    def _has_rotatable_content(self) -> bool:
        """Return True when base file has content that can be rotated."""
        try:
            return os.path.getsize(self.baseFilename) > 0
        except OSError:
            return False

    def _rotate_now_locked(
        self,
        period_key: str | None = None,
        *,
        next_active_period_key: str | None = None,
    ) -> bool:
        """Rotate current file under lock. Returns True on successful rotation."""
        if period_key is None:
            if self.rotate_schedule:
                period_key = self._compute_period_key(self._now_local())
            elif self._active_period_key:
                period_key = self._active_period_key
            else:
                period_key = self._now_local().strftime("%Y-%m-%d-%H")

        next_key = next_active_period_key if next_active_period_key is not None else period_key

        if not self._has_rotatable_content():
            self._active_period_key = next_key
            self._try_ensure_stream_open()
            return False

        target = self._build_collision_safe_path(self._build_rotated_path(period_key))

        try:
            self.flush()
            if self.stream is not None:
                self.stream.close()
                self.stream = None

            os.replace(self.baseFilename, target)
            self.stream = self._open()
            self._active_period_key = next_key
            self._prune_rotated_files()
            return True
        except PermissionError:
            # Windows: OS briefly holds the file after close (antivirus, open reader).
            # Rotation skipped this cycle; will retry on the next emit boundary.
            self._try_ensure_stream_open()
            return False
        except Exception:
            # Keep logging alive by restoring stream best-effort.
            self._try_ensure_stream_open()
            self._report_rotation_error()
            return False

    def rotate_now(self) -> bool:
        """Force immediate file rotation.

        Returns:
            True if rotation completed, False for no-op/failure.
        """
        self.acquire()
        try:
            if getattr(self, "_closed", False):
                return False
            return self._rotate_now_locked()
        finally:
            self.release()

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record, rotating first when schedule boundary changed."""
        if getattr(self, "_closed", False):
            return
        try:
            rotation_keys = self._rotation_key_for_emit()
            if rotation_keys is not None:
                archive_key, next_key = rotation_keys
                self._rotate_now_locked(period_key=archive_key, next_active_period_key=next_key)
            super().emit(record)
        except Exception:
            self.handleError(record)


class ArlogiSyslogHandler(logging.handlers.SysLogHandler):
    """A robust syslog handler with standard formatting and automatic fallback.

    Features:
    - Standard arlogi formatting for consistent syslog messages
    - Automatic fallback to UDP on localhost:514 if /dev/log fails
    - Graceful degradation - won't crash the application if syslog is unavailable
    """

    def __init__(
        self,
        address: str | tuple[str, int] = "/dev/log",
        facility: int | str = logging.handlers.SysLogHandler.LOG_USER,
        socktype: int | None = None,
    ):
        """Initialize the syslog handler.

        Args:
            address: Syslog server address (default: "/dev/log" for Unix socket)
            facility: Syslog facility (default: LOG_USER)
            socktype: Socket type (SOCK_STREAM or SOCK_DGRAM)
        """
        self._failed = False
        target_address = address
        # Proactively check /dev/log so systems without it fall back to localhost:514
        if address == "/dev/log" and not os.path.exists("/dev/log"):
            target_address = ("localhost", 514)

        try:
            super().__init__(address=target_address, facility=facility, socktype=socktype)
            self.setFormatter(logging.Formatter("%(name)s[%(process)d]: %(levelname)s: %(message)s"))
        except Exception as e:
            if address == "/dev/log":
                if target_address != ("localhost", 514):
                    try:
                        super().__init__(address=("localhost", 514), facility=facility, socktype=socktype)
                        self.setFormatter(logging.Formatter("%(name)s[%(process)d]: %(levelname)s: %(message)s"))
                        return
                    except Exception:
                        pass
                logging.Handler.__init__(self)
                self._failed = True
            else:
                raise e

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a record, silently dropping it if syslog is unavailable."""
        if getattr(self, "_failed", False):
            return
        try:
            super().emit(record)
        except Exception:
            self._failed = True

    def close(self) -> None:
        """Close the handler safely even if initialization failed."""
        if getattr(self, "_failed", False):
            logging.Handler.close(self)
            return
        super().close()
