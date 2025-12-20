import json
import logging
import logging.handlers
import sys
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.logging import RichHandler


class ColoredConsoleHandler(RichHandler):
    """A logging handler that uses rich for colored console output."""

    def __init__(
        self,
        show_time: bool = False,
        show_level: bool = True,
        show_path: bool = True,
        level_styles: dict[str, str] | None = None,
        *args: Any,
        **kwargs: Any,
    ):
        # Default level styles: INFO is lighter (grey69) than DEBUG/TRACE (grey37)
        default_styles = {
            "trace": "grey37",
            "debug": "grey37",
            "info": "grey69",
            "warning": "yellow",
            "error": "red",
            "critical": "bold red",
        }
        if level_styles:
            default_styles.update(level_styles)

        # Default to a console that supports colors and directed to stdout
        if "console" not in kwargs:
            kwargs["console"] = Console(force_terminal=True, file=sys.stdout)

        # Enable rich tracebacks by default for the "wow" factor
        kwargs.setdefault("rich_tracebacks", True)
        kwargs.setdefault("markup", True)

        super().__init__(
            *args,
            show_time=show_time,
            show_level=show_level,
            show_path=show_path,
            **kwargs,
        )

        # Set level styles after initialization (for compatibility with older rich versions)
        self.level_styles = default_styles

    def get_level_text(self, record: logging.LogRecord) -> Any:
        """Custom level text: use only the first character."""
        from rich.text import Text

        level_name = record.levelname
        # Map TRACE to T, DEBUG to D, etc.
        char = level_name[0]

        style = self.level_styles.get(level_name.lower(), "default")
        # Compact single character indicator
        return Text(f"{char} ", style=style)

    def render_message(self, record: logging.LogRecord, message: str) -> Any:
        """Render message text with level-specific styling."""
        message_text = super().render_message(record, message)

        # Apply style to the entire message text
        level_name = record.levelname.lower()
        style = self.level_styles.get(level_name, "default")

        message_text.style = style
        return message_text


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured log output."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger_name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line_number": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from the record
        # Standard logging adds these to the record __dict__
        # We want to exclude standard attributes
        standard_attrs = {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "message"
        }

        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith("_"):
                log_data[key] = value

        return json.dumps(log_data, default=str)


class JSONHandler(logging.StreamHandler):
    """A logging handler that outputs log records as JSON to a stream (default: stderr)."""

    def __init__(self, stream: Any = None):
        super().__init__(stream)
        self.setFormatter(JSONFormatter())


class JSONFileHandler(logging.FileHandler):
    """A logging handler that outputs log records as JSON to a file."""

    def __init__(self, filename: str, mode: str = "a", encoding: str | None = None, delay: bool = False):
        # Ensure parent directory exists
        import os
        parent_dir = os.path.dirname(os.path.abspath(filename))
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        super().__init__(filename, mode, encoding, delay)
        self.setFormatter(JSONFormatter())


class ArlogiSyslogHandler(logging.handlers.SysLogHandler):
    """A robust syslog handler with standard formatting."""

    def __init__(
        self,
        address: str | tuple[str, int] = "/dev/log",
        facility: int | str = logging.handlers.SysLogHandler.LOG_USER,
        socktype: int | None = None,
    ):
        try:
            super().__init__(address=address, facility=facility, socktype=socktype)
            self.setFormatter(logging.Formatter("%(name)s[%(process)d]: %(levelname)s: %(message)s"))
        except Exception as e:
            # Fallback for systems without /dev/log (e.g., macOS or some containers)
            if address == "/dev/log":
                # Try UDP on localhost as a last resort
                try:
                    super().__init__(address=("localhost", 514), facility=facility, socktype=socktype)
                except Exception:
                    # If everything fails, just use a NullHandler-like behavior or a warning
                    # but we shouldn't crash the app for logging setup failure
                    pass
            else:
                raise e
