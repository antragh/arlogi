# Arlogi Core Source Code

---

## FILE: src/arlogi/__init__.py

```py
from .config import LoggingConfig, get_default_level, is_test_mode
from .factory import (
    LoggerFactory,
    cleanup_json_logger,
    cleanup_syslog_logger,
    get_json_logger,
    get_logger,
    get_syslog_logger,
    rotate_json_logger,
    setup_logging,
)
from .handler_factory import HandlerFactory
from .levels import TRACE_LEVEL_NUM as TRACE
from .types import LoggerProtocol

__all__ = [
    # Public API
    "get_logger",
    "get_json_logger",
    "get_syslog_logger",
    "cleanup_json_logger",
    "cleanup_syslog_logger",
    "rotate_json_logger",
    "setup_logging",
    "TRACE",
    # Advanced / Internal API
    "LoggerFactory",
    "LoggerProtocol",
    "LoggingConfig",
    "HandlerFactory",
    "is_test_mode",
    "get_default_level",
]

```

---

## FILE: src/arlogi/config.py

```py
"""Logging configuration dataclass for type-safe setup.

This module provides a structured, validated configuration for logging setup,
following the Builder pattern for flexible construction.
"""

import logging
import os
import sys
from dataclasses import dataclass
from typing import Any, Literal

RotateSchedule = Literal["hour", "day", "week", "month"]


@dataclass(frozen=True)
class LoggingConfig:
    """Immutable configuration for arlogi logging setup.

    Attributes:
        level: Global root log level (int or string like "INFO")
        module_levels: Per-module level overrides (e.g., {"app.db": "DEBUG"})
        json_file_name: Path to JSON log file (None for no JSON file logging)
        json_file_only: If True, only output to JSON (no console)
        use_syslog: Enable syslog output
        syslog_address: Syslog server address (default: "/dev/log")
        rotate_schedule: Optional time-window schedule for file rotation
        rotate_retention_count: Optional retention count for rotated files
        show_time: Show timestamps in console output
        show_level: Show log levels in console output
        show_path: Show file paths in console output
    """

    level: int | str = logging.INFO
    module_levels: dict[str, str | int] | None = None
    json_file_name: str | None = None
    json_file_only: bool = False
    use_syslog: bool = False
    syslog_address: str | tuple[str, int] = "/dev/log"
    rotate_schedule: RotateSchedule | None = None
    rotate_retention_count: int | None = None
    show_time: bool = False
    show_level: bool = True
    show_path: bool = True

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        # Validate level
        self._validate_level(self.level)

        # Validate module levels if provided
        if self.module_levels:
            for name, m_level in self.module_levels.items():
                if not isinstance(name, str) or not name:
                    raise ValueError(f"Invalid module name: {name!r}")
                self._validate_level(m_level)

        # Validate rotation schedule
        if self.rotate_schedule is not None:
            valid_schedules = {"hour", "day", "week", "month"}
            if self.rotate_schedule not in valid_schedules:
                raise ValueError(
                    f"Invalid rotate_schedule: {self.rotate_schedule!r}. "
                    f"Valid values: {', '.join(sorted(valid_schedules))}"
                )

        # Validate rotation retention count
        if self.rotate_retention_count is not None and self.rotate_retention_count < 1:
            raise ValueError("rotate_retention_count must be >= 1 when provided")

    @staticmethod
    def _validate_level(level: int | str) -> None:
        """Validate a log level value.

        Args:
            level: Log level as int or str

        Raises:
            ValueError: If level is invalid
        """
        if isinstance(level, str):
            # Check for custom TRACE level (valid but not in logging module)
            if level.upper() == "TRACE":
                return

            try:
                getattr(logging, level.upper())
            except AttributeError as e:
                valid = ", ".join(name for name in dir(logging) if name.isupper() and name not in ("NOTSET",))
                raise ValueError(f"Invalid log level: {level!r}. Valid levels: TRACE, {valid}") from e
        elif not isinstance(level, int):
            raise ValueError(f"Log level must be int or str, got {type(level).__name__}")

    @property
    def resolved_level(self) -> int:
        """Get the global level as an integer.

        Returns:
            The resolved log level as an integer
        """
        if isinstance(self.level, str):
            return getattr(logging, self.level.upper())
        return self.level

    @property
    def show_console(self) -> bool:
        """Determine if console output should be shown.

        Returns:
            True if console output should be displayed
        """
        return not self.json_file_only

    @property
    def has_json_output(self) -> bool:
        """Determine if JSON output is configured.

        Returns:
            True if JSON file or JSON-only output is enabled
        """
        return self.json_file_name is not None or self.json_file_only

    def resolve_module_level(self, name: str, level: str | int) -> int:
        """Resolve a module level to an integer.

        Args:
            name: Module name (for error messages)
            level: Level as string or int

        Returns:
            The level as an integer
        """
        if isinstance(level, str):
            upper_level = level.upper()
            # Handle custom TRACE level
            if upper_level == "TRACE":
                from .levels import TRACE_LEVEL_NUM

                return TRACE_LEVEL_NUM
            return getattr(logging, upper_level)
        # level is already an int
        return level

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to a dictionary.

        Returns:
            Dictionary representation of the configuration
        """
        return {
            "level": self.level,
            "module_levels": self.module_levels,
            "json_file_name": self.json_file_name,
            "json_file_only": self.json_file_only,
            "use_syslog": self.use_syslog,
            "syslog_address": self.syslog_address,
            "rotate_schedule": self.rotate_schedule,
            "rotate_retention_count": self.rotate_retention_count,
            "show_time": self.show_time,
            "show_level": self.show_level,
            "show_path": self.show_path,
        }

    @classmethod
    def from_kwargs(cls, **kwargs: Any) -> "LoggingConfig":
        """Create LoggingConfig from keyword arguments.

        This factory method provides backward compatibility with the
        legacy setup_logging() function signature.

        Args:
            **kwargs: Configuration keyword arguments

        Returns:
            A new LoggingConfig instance

        Raises:
            TypeError: If unknown keyword arguments are provided

        Example:
            >>> config = LoggingConfig.from_kwargs(
            ...     level="INFO", module_levels={"app.db": "DEBUG"}, json_file_name="logs/app.jsonl"
            ... )
        """
        valid_keys = {
            "level",
            "module_levels",
            "json_file_name",
            "json_file_only",
            "use_syslog",
            "syslog_address",
            "rotate_schedule",
            "rotate_retention_count",
            "show_time",
            "show_level",
            "show_path",
        }

        # Check for unknown keys to catch typos early
        unknown = set(kwargs.keys()) - valid_keys
        if unknown:
            raise TypeError(
                f"LoggingConfig() got unknown keyword argument(s): {', '.join(sorted(unknown))}. "
                f"Valid arguments: {', '.join(sorted(valid_keys))}"
            )

        return cls(**kwargs)


def is_test_mode() -> bool:
    """Detect if running under a test runner.

    Checks for pytest, unittest, or the PYTEST_CURRENT_TEST environment
    variable to determine if the code is running in a test context.

    Returns:
        True if running in a test environment
    """
    return "pytest" in sys.modules or "unittest" in sys.modules or os.environ.get("PYTEST_CURRENT_TEST") is not None


def get_default_level() -> int:
    """Get the default log level based on the current environment.

    Returns DEBUG in test mode for better test visibility,
    otherwise returns INFO.

    Returns:
        logging.DEBUG if in test mode, logging.INFO otherwise
    """
    return logging.DEBUG if is_test_mode() else logging.INFO

```

---

## FILE: src/arlogi/config_builder.py

```py
"""Builder pattern for LoggingConfig construction.

This module provides a fluent builder API for constructing logging
configurations, making complex configurations more readable and
less error-prone than direct constructor calls.
"""

from .config import LoggingConfig


class LoggingConfigBuilder:
    """Builder for creating LoggingConfig instances with fluent API.

    This builder follows the Builder design pattern to provide a clear,
    readable interface for constructing complex logging configurations.
    It helps prevent configuration errors by making the API self-documenting
    and harder to use incorrectly.

    Example:
        >>> config = LoggingConfigBuilder().with_level("INFO").with_json_file("logs/app.jsonl").with_syslog().build()
    """

    def __init__(self) -> None:
        """Initialize builder with sensible defaults."""
        self._level = "INFO"
        self._module_levels: dict[str, str | int] | None = None
        self._json_file_name: str | None = None
        self._json_file_only = False
        self._use_syslog = False
        self._syslog_address: str | tuple[str, int] = "/dev/log"
        self._rotate_schedule: str | None = None
        self._rotate_retention_count: int | None = None
        self._show_time = False
        self._show_level = True
        self._show_path = True

    def with_level(self, level: str | int) -> "LoggingConfigBuilder":
        """Set the global log level.

        Args:
            level: Log level (e.g., "INFO", logging.DEBUG, "TRACE")

        Returns:
            Self for method chaining

        Example:
            >>> builder.with_level("DEBUG")
        """
        self._level = level
        return self

    def with_module_levels(self, levels: dict[str, str | int]) -> "LoggingConfigBuilder":
        """Set per-module level overrides.

        Allows fine-grained control over logging levels for specific modules.
        Useful for silencing noisy libraries or debugging specific components.

        Args:
            levels: Dictionary mapping module names to levels

        Returns:
            Self for method chaining

        Example:
            >>> builder.with_module_levels({"app.database": "DEBUG", "external_api": "WARNING"})
        """
        self._module_levels = levels
        return self

    def with_json_file(self, file_name: str, console_also: bool = True) -> "LoggingConfigBuilder":
        """Configure JSON file logging.

        Args:
            file_name: Path to JSON log file
            console_also: If True (default), also log to console.
                        If False, disable console output.

        Returns:
            Self for method chaining

        Example:
            >>> # Both file and console
            >>> builder.with_json_file("logs/app.jsonl")
            >>>
            >>> # File only, no console
            >>> builder.with_json_file("logs/app.jsonl", console_also=False)
        """
        self._json_file_name = file_name
        self._json_file_only = not console_also
        return self

    def with_json_console_only(self) -> "LoggingConfigBuilder":
        """Configure JSON output to console only (stderr, no file).

        Returns:
            Self for method chaining

        Example:
            >>> builder.with_json_console_only()
        """
        self._json_file_only = True
        return self

    def with_syslog(self, address: str | tuple[str, int] = "/dev/log") -> "LoggingConfigBuilder":
        """Enable syslog output.

        Args:
            address: Syslog server address (default: "/dev/log" for Unix socket)

        Returns:
            Self for method chaining

        Example:
            >>> # Unix socket
            >>> builder.with_syslog()
            >>>
            >>> # Remote syslog server
            >>> builder.with_syslog(("192.168.1.1", 514))
        """
        self._use_syslog = True
        self._syslog_address = address
        return self

    def with_console_format(
        self, show_time: bool = False, show_level: bool = True, show_path: bool = True
    ) -> "LoggingConfigBuilder":
        """Configure console output format.

        Args:
            show_time: Show timestamps in console output
            show_level: Show log levels (default: True)
            show_path: Show file paths (default: True)

        Returns:
            Self for method chaining

        Example:
            >>> builder.with_console_format(show_time=True, show_level=True, show_path=False)
        """
        self._show_time = show_time
        self._show_level = show_level
        self._show_path = show_path
        return self

    def with_rotation(self, schedule: str, retention_count: int | None = None) -> "LoggingConfigBuilder":
        """Configure optional time-window file rotation.

        Args:
            schedule: Rotation schedule (hour, day, week, month)
            retention_count: Optional number of rotated files to retain

        Returns:
            Self for method chaining

        Example:
            >>> builder.with_rotation("day", retention_count=7)
        """
        self._rotate_schedule = schedule
        self._rotate_retention_count = retention_count
        return self

    def build(self) -> LoggingConfig:
        """Build the LoggingConfig instance.

        Returns:
            A validated LoggingConfig instance

        Raises:
            ValueError: If configuration is invalid

        Example:
            >>> config = LoggingConfigBuilder().with_level("DEBUG").build()
        """
        return LoggingConfig(
            level=self._level,
            module_levels=self._module_levels,
            json_file_name=self._json_file_name,
            json_file_only=self._json_file_only,
            use_syslog=self._use_syslog,
            syslog_address=self._syslog_address,
            rotate_schedule=self._rotate_schedule,
            rotate_retention_count=self._rotate_retention_count,
            show_time=self._show_time,
            show_level=self._show_level,
            show_path=self._show_path,
        )

```

---

## FILE: src/arlogi/factory.py

```py
"""Factory for creating logger instances with caller attribution support.

This module provides the LoggerFactory class for creating and configuring
loggers, along with the TraceLogger class that adds custom TRACE level
and caller attribution features.
"""

import logging
from typing import Any

from .config import LoggingConfig, get_default_level, is_test_mode
from .handler_factory import HandlerFactory
from .handlers import ArlogiSyslogHandler, JSONFileHandler, JSONHandler
from .levels import TRACE_LEVEL_NUM, register_trace_level
from .types import LoggerProtocol


class TraceLogger(logging.Logger):
    """Custom logger class with trace() and caller attribution support.

    This logger extends the standard Python Logger with:
    - A custom TRACE level (below DEBUG)
    - Caller attribution via caller_depth parameter
    - Automatic extra field handling from unknown kwargs
    """

    def _get_caller_info(self, depth: int) -> tuple[str, str]:
        """Find the name of the module and function at the specified depth.

        Args:
            depth: Stack depth to inspect (0 = current function)

        Returns:
            Tuple of (module_name, function_name)
        """
        try:
            import sys

            # Stack frame offsets:
            # 0: _get_caller_info
            # 1: _process_params
            # 2: info/debug/... (wrapper method)
            # 3: actual call site (depth 0)
            # 4: caller of call site (depth 1)
            frame = sys._getframe(depth + 3)
            module = frame.f_globals.get("__name__", "unknown")
            name = frame.f_code.co_name
            return module, name
        except (ValueError, AttributeError):
            return "unknown", "unknown"

    def _process_params(self, msg: Any, kwargs: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        """Process caller attribution and move arbitrary kwargs to 'extra'.

        Args:
            msg: The log message
            kwargs: Keyword arguments including optional caller_depth

        Returns:
            Tuple of (processed_message, processed_kwargs)
        """
        # 1. Handle caller attribution
        caller_depth_val = kwargs.pop("caller_depth", None)

        if caller_depth_val is not None:
            try:
                from rich.markup import escape

                depth = int(caller_depth_val)
                m0, _ = self._get_caller_info(0)
                mN, nN = self._get_caller_info(depth)

                # Format based on depth:
                # 0: [function_name()]
                # 1+: [from .function_name()] (same module)
                #     [from module.function_name()] (different module)
                if depth >= 1:
                    if mN == m0:
                        attribution = f"from .{nN}()"
                    else:
                        attribution = f"from {mN}.{nN}()"
                else:
                    attribution = f"{nN}()"

                # Add attribution as suffix (RichHandler indents multi-line)
                safe_attribution = escape(f"[{attribution}]")
                suffix = f"\n{safe_attribution}"

                if isinstance(msg, str):
                    msg = msg + suffix
                else:
                    msg = str(msg) + suffix
            except (ValueError, TypeError, ImportError):
                pass

        # 2. Move unknown kwargs to 'extra' for structured logging
        standard_kwargs = {"exc_info", "stack_info", "stacklevel", "extra"}
        extra = kwargs.get("extra", {})

        # Collect unknown kwargs
        custom_kwargs = {}
        for key in list(kwargs.keys()):
            if key not in standard_kwargs:
                custom_kwargs[key] = kwargs.pop(key)

        if custom_kwargs:
            if not isinstance(extra, dict):
                extra = {"_original_extra": extra}
            extra.update(custom_kwargs)
            kwargs["extra"] = extra

        # Ensure log entries point to user's code, not this wrapper
        kwargs.setdefault("stacklevel", 2)
        return msg, kwargs

    # Standard logging methods with caller attribution support
    def trace(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log a message with TRACE level (below DEBUG).

        Args:
            msg: The message to log
            *args: Format arguments for the message
            **kwargs: Optional caller_depth for caller attribution
        """
        msg, kwargs = self._process_params(msg, kwargs)
        if self.isEnabledFor(TRACE_LEVEL_NUM):
            self._log(TRACE_LEVEL_NUM, msg, args, **kwargs)

    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        msg, kwargs = self._process_params(msg, kwargs)
        super().debug(msg, *args, **kwargs)

    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        msg, kwargs = self._process_params(msg, kwargs)
        super().info(msg, *args, **kwargs)

    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        msg, kwargs = self._process_params(msg, kwargs)
        super().warning(msg, *args, **kwargs)

    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        msg, kwargs = self._process_params(msg, kwargs)
        super().error(msg, *args, **kwargs)

    def critical(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        msg, kwargs = self._process_params(msg, kwargs)
        super().critical(msg, *args, **kwargs)

    def exception(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log an exception with traceback."""
        msg, kwargs = self._process_params(msg, kwargs)
        super().exception(msg, *args, **kwargs)

    def log(self, level: int, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log a message at the specified level."""
        msg, kwargs = self._process_params(msg, kwargs)
        super().log(level, msg, *args, **kwargs)


class LoggerFactory:
    """Factory for creating and configuring logger instances.

    This factory manages the global logging configuration and provides
    methods to get logger instances with various configurations.
    """

    _initialized = False
    _global_logger: TraceLogger | None = None

    @classmethod
    def setup(
        cls,
        level: int | str = logging.INFO,
        module_levels: dict[str, str | int] | None = None,
        json_file_name: str | None = None,
        json_file_only: bool = False,
        use_syslog: bool = False,
        syslog_address: str | tuple[str, int] = "/dev/log",
        rotate_schedule: str | None = None,
        rotate_retention_count: int | None = None,
        show_time: bool = False,
        show_level: bool = True,
        show_path: bool = True,
    ) -> None:
        """Centralized logging setup for arlogi.

        This method configures the root logger with the specified handlers
        and levels. It can be called multiple times to update configuration.

        Args:
            level: Global root log level
            module_levels: Per-module level overrides
            json_file_name: Path to JSON log file
            json_file_only: If True, only output JSON (no console)
            use_syslog: Enable syslog output
            syslog_address: Syslog server address
            rotate_schedule: Optional rotation schedule for JSON file logging
            rotate_retention_count: Optional number of rotated files to retain
            show_time: Show timestamps in console output
            show_level: Show log levels in console output
            show_path: Show file paths in console output
        """
        config = LoggingConfig.from_kwargs(
            level=level,
            module_levels=module_levels,
            json_file_name=json_file_name,
            json_file_only=json_file_only,
            use_syslog=use_syslog,
            syslog_address=syslog_address,
            rotate_schedule=rotate_schedule,
            rotate_retention_count=rotate_retention_count,
            show_time=show_time,
            show_level=show_level,
            show_path=show_path,
        )
        cls._apply_configuration(config)

    @classmethod
    def _apply_configuration(cls, config: LoggingConfig) -> None:
        """Apply a LoggingConfig to the root logger.

        Args:
            config: The logging configuration to apply
        """
        cls._initialize_trace_level()
        cls._configure_root_logger(config)

        if not is_test_mode():
            cls._clear_and_add_handlers(config)

        cls._configure_module_levels(config)
        cls._initialized = True

    @classmethod
    def _initialize_trace_level(cls) -> None:
        """Register the custom TRACE level with Python's logging module."""
        register_trace_level()
        logging.setLoggerClass(TraceLogger)

    @classmethod
    def _configure_root_logger(cls, config: LoggingConfig) -> None:
        """Configure the root logger level.

        Args:
            config: The logging configuration
        """
        root = logging.getLogger()
        root.setLevel(config.resolved_level)

    @classmethod
    def _clear_and_add_handlers(cls, config: LoggingConfig) -> None:
        """Clear existing handlers and add configured ones.

        Args:
            config: The logging configuration
        """
        root = logging.getLogger()

        # Remove existing handlers
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # Add configured handlers via factory
        handlers = HandlerFactory.create_handlers(config)
        for handler in handlers:
            root.addHandler(handler)

    @classmethod
    def _configure_module_levels(cls, config: LoggingConfig) -> None:
        """Apply module-specific log level overrides.

        Args:
            config: The logging configuration
        """
        if config.module_levels:
            for name, m_level in config.module_levels.items():
                logger = logging.getLogger(name)
                resolved_level = config.resolve_module_level(name, m_level)
                logger.setLevel(resolved_level)
                # Ensure propagation to root for inherited settings
                logger.propagate = True

    @staticmethod
    def is_test_mode() -> bool:
        """Detect if running under a test runner.

        Returns:
            True if pytest, unittest, or PYTEST_CURRENT_TEST is detected
        """
        return is_test_mode()

    @classmethod
    def get_logger(cls, name: str, level: int | str | None = None) -> LoggerProtocol:
        """Get a logger instance conforming to LoggerProtocol.

        Auto-initializes with default settings if called before setup().

        Args:
            name: Logger name (typically __name__ of the module)
            level: Optional level override for this logger

        Returns:
            A logger instance supporting caller attribution
        """
        if not cls._initialized:
            cls.setup(level=get_default_level())

        logger = logging.getLogger(name)
        if level is not None:
            logger.setLevel(level)

        return logger  # type: ignore

    @classmethod
    def get_json_logger(cls, name: str = "json", json_file_name: str | None = None) -> LoggerProtocol:
        """Get a logger that only outputs to JSON, bypassing root handlers.

        Args:
            name: Logger name suffix
            json_file_name: Optional file path for JSON output

        Returns:
            A JSON-only logger instance
        """
        logger = logging.getLogger(f"arlogi.json.{name}")
        logger.propagate = False

        # Close existing handlers to prevent resource leaks
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

        if json_file_name:
            logger.addHandler(JSONFileHandler(json_file_name))
        else:
            logger.addHandler(JSONHandler())

        logger.setLevel(logging.DEBUG)
        return logger  # type: ignore

    @classmethod
    def get_syslog_logger(cls, name: str = "syslog", address: str | tuple[str, int] = "/dev/log") -> LoggerProtocol:
        """Get a logger that only outputs to Syslog, bypassing root handlers.

        Args:
            name: Logger name suffix
            address: Syslog server address

        Returns:
            A syslog-only logger instance
        """
        logger = logging.getLogger(f"arlogi.syslog.{name}")
        logger.propagate = False

        # Close existing handlers to prevent resource leaks
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

        logger.addHandler(ArlogiSyslogHandler(address=address))
        logger.setLevel(logging.DEBUG)
        return logger  # type: ignore

    @classmethod
    def cleanup_json_logger(cls, name: str = "json") -> None:
        """Clean up handlers for a JSON logger to free resources.

        This method closes all handlers associated with the named JSON logger
        and removes them from the logger. Use this to explicitly release file
        handles and other resources when you're done with a logger.

        Args:
            name: Logger name suffix (must match the name used in get_json_logger)

        Example:
            >>> logger = get_json_logger("temp", "logs/temp.json")
            >>> logger.info("Done logging")
            >>> cleanup_json_logger("temp")  # Close the file handle
        """
        logger_name = f"arlogi.json.{name}"
        logger = logging.getLogger(logger_name)

        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

    @classmethod
    def cleanup_syslog_logger(cls, name: str = "syslog") -> None:
        """Clean up handlers for a syslog logger to free resources.

        Args:
            name: Logger name suffix

        Example:
            >>> logger = get_syslog_logger("temp")
            >>> logger.info("Done logging")
            >>> cleanup_syslog_logger("temp")  # Close the socket
        """
        logger_name = f"arlogi.syslog.{name}"
        logger = logging.getLogger(logger_name)

        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

    @classmethod
    def get_global_logger(cls) -> LoggerProtocol:
        """Get or initialize the global logger instance.

        Returns:
            The global application logger instance
        """
        if cls._global_logger is None:
            cls._global_logger = cls.get_logger("app")  # type: ignore
        return cls._global_logger  # type: ignore


# Public API helper functions


def setup_logging(
    level: int | str = logging.INFO,
    module_levels: dict[str, str | int] | None = None,
    json_file_name: str | None = None,
    json_file_only: bool = False,
    use_syslog: bool = False,
    syslog_address: str | tuple[str, int] = "/dev/log",
    rotate_schedule: str | None = None,
    rotate_retention_count: int | None = None,
    show_time: bool = False,
    show_level: bool = True,
    show_path: bool = True,
) -> None:
    """Set up arlogi logging with the specified configuration.

    This is a convenience wrapper around LoggerFactory.setup().

    Args:
        level: Global root log level
        module_levels: Per-module level overrides
        json_file_name: Path to JSON log file
        json_file_only: If True, only output JSON (no console)
        use_syslog: Enable syslog output
        syslog_address: Syslog server address
        rotate_schedule: Optional rotation schedule for JSON file logging
        rotate_retention_count: Optional number of rotated files to retain
        show_time: Show timestamps in console output
        show_level: Show log levels in console output
        show_path: Show file paths in console output
    """
    LoggerFactory.setup(
        level=level,
        module_levels=module_levels,
        json_file_name=json_file_name,
        json_file_only=json_file_only,
        use_syslog=use_syslog,
        syslog_address=syslog_address,
        rotate_schedule=rotate_schedule,
        rotate_retention_count=rotate_retention_count,
        show_time=show_time,
        show_level=show_level,
        show_path=show_path,
    )


def get_logger(name: str, level: int | str | None = None) -> LoggerProtocol:
    """Get a logger instance with caller attribution support.

    Args:
        name: Logger name (typically __name__)
        level: Optional level override

    Returns:
        A logger instance
    """
    return LoggerFactory.get_logger(name, level)


def get_json_logger(name: str = "json", json_file_name: str | None = None) -> LoggerProtocol:
    """Get a dedicated JSON-only logger.

    Args:
        name: Logger name suffix
        json_file_name: Optional file path for JSON output

    Returns:
        A JSON-only logger instance
    """
    return LoggerFactory.get_json_logger(name, json_file_name=json_file_name)


def rotate_json_logger(name: str = "json") -> int:
    """Rotate JSON file handlers attached to the named JSON logger.

    Args:
        name: Logger name suffix (must match get_json_logger usage)

    Returns:
        Number of handlers successfully rotated
    """
    logger_name = f"arlogi.json.{name}"
    logger = logging.getLogger(logger_name)
    rotated = 0

    for handler in logger.handlers:
        if isinstance(handler, JSONFileHandler) and handler.rotate_now():
            rotated += 1

    return rotated


def get_syslog_logger(name: str = "syslog", address: str | tuple[str, int] = "/dev/log") -> LoggerProtocol:
    """Get a dedicated syslog-only logger.

    Args:
        name: Logger name suffix
        address: Syslog server address

    Returns:
        A syslog-only logger instance
    """
    return LoggerFactory.get_syslog_logger(name, address)


def cleanup_json_logger(name: str = "json") -> None:
    """Clean up handlers for a JSON logger to free resources.

    This function closes all handlers associated with the named JSON logger
    and removes them from the logger. Use this to explicitly release file
    handles and other resources when you're done with a logger.

    Args:
        name: Logger name suffix (must match the name used in get_json_logger)

    Example:
        >>> logger = get_json_logger("temp", "logs/temp.json")
        >>> logger.info("Done logging")
        >>> cleanup_json_logger("temp")  # Close the file handle
    """
    LoggerFactory.cleanup_json_logger(name)


def cleanup_syslog_logger(name: str = "syslog") -> None:
    """Clean up handlers for a syslog logger to free resources.

    Args:
        name: Logger name suffix

    Example:
        >>> logger = get_syslog_logger("temp")
        >>> logger.info("Done logging")
        >>> cleanup_syslog_logger("temp")  # Close the socket
    """
    LoggerFactory.cleanup_syslog_logger(name)

```

---

## FILE: src/arlogi/handler_factory.py

```py
"""Handler factory for creating logging handlers.

This module provides a centralized factory for creating log handlers,
following the Factory pattern for consistent handler creation and
easier testing.
"""

import logging

from .config import LoggingConfig
from .handlers import (
    ArlogiSyslogHandler,
    ColoredConsoleHandler,
    JSONFileHandler,
    JSONHandler,
)


class HandlerFactory:
    """Factory for creating logging handlers.

    This class encapsulates the creation logic for all handler types,
    making it easier to test and extend with new handler types.
    """

    @staticmethod
    def create_console(config: LoggingConfig) -> ColoredConsoleHandler:
        """Create a colored console handler.

        Args:
            config: Logging configuration

        Returns:
            A configured ColoredConsoleHandler instance

        Example:
            >>> handler = HandlerFactory.create_console(LoggingConfig(show_time=True, show_level=True))
        """
        return ColoredConsoleHandler(
            show_time=config.show_time,
            show_level=config.show_level,
            show_path=config.show_path,
        )

    @staticmethod
    def create_json_stream() -> JSONHandler:
        """Create a JSON stream handler (outputs to stderr).

        Returns:
            A JSONHandler instance configured for stream output

        Example:
            >>> handler = HandlerFactory.create_json_stream()
        """
        return JSONHandler()

    @staticmethod
    def create_json_file(config: LoggingConfig) -> JSONFileHandler:
        """Create a JSON file handler.

        Args:
            config: Logging configuration with json_file_name set

        Returns:
            A JSONFileHandler instance

        Raises:
            ValueError: If json_file_name is not set in config

        Example:
            >>> config = LoggingConfig(json_file_name="logs/app.jsonl")
            >>> handler = HandlerFactory.create_json_file(config)
        """
        if not config.json_file_name:
            raise ValueError("json_file_name must be set in config")

        return JSONFileHandler(
            config.json_file_name,
            rotate_schedule=config.rotate_schedule,
            rotate_retention_count=config.rotate_retention_count,
        )

    @staticmethod
    def create_json_handler(config: LoggingConfig) -> logging.Handler:
        """Create the appropriate JSON handler based on configuration.

        Creates either a JSONFileHandler (if json_file_name is set)
        or a JSONHandler for stream output.

        Args:
            config: Logging configuration

        Returns:
            Either JSONFileHandler or JSONHandler based on config

        Example:
            >>> # File handler
            >>> config1 = LoggingConfig(json_file_name="logs/app.jsonl")
            >>> handler1 = HandlerFactory.create_json_handler(config1)
            >>>
            >>> # Stream handler
            >>> config2 = LoggingConfig(json_file_only=True)
            >>> handler2 = HandlerFactory.create_json_handler(config2)
        """
        if config.json_file_name:
            return HandlerFactory.create_json_file(config)
        return HandlerFactory.create_json_stream()

    @staticmethod
    def create_syslog(config: LoggingConfig) -> ArlogiSyslogHandler:
        """Create a syslog handler.

        Args:
            config: Logging configuration with syslog settings

        Returns:
            An ArlogiSyslogHandler instance

        Example:
            >>> config = LoggingConfig(use_syslog=True, syslog_address="/dev/log")
            >>> handler = HandlerFactory.create_syslog(config)
        """
        return ArlogiSyslogHandler(address=config.syslog_address)

    @classmethod
    def create_handlers(cls, config: LoggingConfig) -> list[logging.Handler]:
        """Create all handlers based on configuration.

        This is the main factory method that orchestrates the creation
        of all configured handlers.

        Args:
            config: Complete logging configuration

        Returns:
            List of configured handler instances

        Example:
            >>> config = LoggingConfig(json_file_name="logs/app.jsonl", use_syslog=True)
            >>> handlers = HandlerFactory.create_handlers(config)
            >>> for handler in handlers:
            ...     logger.addHandler(handler)
        """
        handlers: list[logging.Handler] = []

        # JSON file handler
        if config.json_file_name:
            handlers.append(cls.create_json_file(config))

        # Console handler (show unless json_file_only)
        if config.show_console:
            handlers.append(cls.create_console(config))
        elif config.json_file_only and not config.json_file_name:
            # JSON on console when json_file_only=True but no file specified
            handlers.append(cls.create_json_stream())

        # Syslog handler
        if config.use_syslog:
            handlers.append(cls.create_syslog(config))

        return handlers

```

---

## FILE: src/arlogi/handlers.py

```py
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
import sys
from datetime import datetime
from glob import glob
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

        # Add extra fields from the record (excluding standard logging attributes)
        standard_attrs = {
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
        }

        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith("_"):
                log_data[key] = value

        # Try to serialize with error handling
        try:
            return json.dumps(log_data, default=str)
        except (TypeError, ValueError) as e:
            # Fallback to basic format on serialization failure
            return json.dumps(
                {
                    "timestamp": log_data.get("timestamp"),
                    "level": log_data.get("level"),
                    "logger_name": log_data.get("logger_name"),
                    "message": str(log_data.get("message", "")),
                    "module": log_data.get("module"),
                    "function": log_data.get("function"),
                    "line_number": log_data.get("line_number"),
                    "error": f"JSON serialization failed: {e}",
                }
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
        super().__init__(stream)
        self.setFormatter(JSONFormatter())

    def close(self):
        """Close the handler and the stream if we own it.

        Only closes custom streams, not system streams like sys.stderr.
        """
        try:
            # Flush before closing
            self.flush()

            # Close custom stream if we own it
            if self._owns_stream and self.stream and hasattr(self.stream, "close"):
                # Don't close system streams
                if self.stream not in (sys.stderr, sys.stdout):
                    self.stream.close()
        finally:
            # Always call parent close
            super().close()


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
    ):
        """Initialize the JSON file handler.

        Args:
            filename: Path to the log file
            mode: File open mode (default: "a" for append)
            encoding: File encoding (default: None for system default)
            delay: Whether to delay file opening until first emit
            rotate_schedule: Optional rotation schedule (hour/day/week/month)
            rotate_retention_count: Optional retention count for rotated files

        Note:
            Thread-safe: Uses exist_ok=True to safely handle concurrent
            directory creation from multiple threads.
        """
        # Ensure parent directory exists
        # Thread-safe: exist_ok=True handles race conditions where multiple
        # threads might try to create the same directory
        parent_dir = os.path.dirname(os.path.abspath(filename))
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        super().__init__(filename, mode, encoding, delay)
        self.rotate_schedule = rotate_schedule
        # Retention default is only applied when schedule is enabled.
        self.rotate_retention_count = (
            rotate_retention_count if rotate_retention_count is not None else (7 if rotate_schedule else None)
        )
        self._active_period_key = self._compute_period_key(self._now_local()) if self.rotate_schedule else None
        self.setFormatter(JSONFormatter())

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

        root, ext = os.path.splitext(self.baseFilename)
        rotated_files = [
            path for path in glob(f"{root}-*{ext}") if os.path.abspath(path) != os.path.abspath(self.baseFilename)
        ]

        if len(rotated_files) <= self.rotate_retention_count:
            return

        rotated_files.sort(key=os.path.getmtime, reverse=True)
        for old_path in rotated_files[self.rotate_retention_count :]:
            try:
                os.remove(old_path)
            except OSError:
                # Pruning failures should never fail application logging.
                continue

    def _rotation_key_for_emit(self) -> str | None:
        """Return the new period key when an emit should trigger rotation."""
        if not self.rotate_schedule:
            return None

        current_key = self._compute_period_key(self._now_local())
        if self._active_period_key is None:
            self._active_period_key = current_key
            return None
        if current_key != self._active_period_key:
            return current_key
        return None

    def _ensure_stream_open(self) -> None:
        """Ensure file stream is available for writing."""
        if self.stream is None:
            self.stream = self._open()

    def _has_rotatable_content(self) -> bool:
        """Return True when base file has content that can be rotated."""
        return os.path.exists(self.baseFilename) and os.path.getsize(self.baseFilename) > 0

    def _rotate_now_locked(self, period_key: str | None = None) -> bool:
        """Rotate current file under lock. Returns True on successful rotation."""
        if period_key is None:
            if self.rotate_schedule:
                period_key = self._compute_period_key(self._now_local())
            elif self._active_period_key:
                period_key = self._active_period_key
            else:
                period_key = self._now_local().strftime("%Y-%m-%d-%H")

        if not self._has_rotatable_content():
            self._active_period_key = period_key
            self._ensure_stream_open()
            return False

        target = self._build_collision_safe_path(self._build_rotated_path(period_key))

        try:
            self.flush()
            if self.stream is not None:
                self.stream.close()
                self.stream = None

            os.replace(self.baseFilename, target)
            self.stream = self._open()
            self._active_period_key = period_key
            self._prune_rotated_files()
            return True
        except PermissionError:
            # Windows: OS briefly holds the file after close (antivirus, open reader).
            # Rotation skipped this cycle; will retry on the next emit boundary.
            self._ensure_stream_open()
            return False
        except Exception:
            # Keep logging alive by restoring stream best-effort.
            self._ensure_stream_open()
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
            return False

    def rotate_now(self) -> bool:
        """Force immediate file rotation.

        Returns:
            True if rotation completed, False for no-op/failure.
        """
        self.acquire()
        try:
            return self._rotate_now_locked()
        finally:
            self.release()

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record, rotating first when schedule boundary changed."""
        try:
            rotation_key = self._rotation_key_for_emit()
            if rotation_key is not None:
                self._rotate_now_locked(period_key=rotation_key)
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
                    # If everything fails, silently continue - don't crash
                    # the application just because logging setup failed
                    pass
            else:
                raise e

```

---

## FILE: src/arlogi/levels.py

```py
import logging
import threading
from typing import Any

TRACE_LEVEL_NUM = 5
TRACE_LEVEL_NAME = "TRACE"

# Module-level lock and flag for thread-safe TRACE level registration
_trace_lock = threading.Lock()
_trace_registered = False


def register_trace_level() -> None:
    """Register the TRACE level with the standard logging module.

    Thread-safe: Uses double-checked locking to ensure TRACE level is
    registered only once even when called from multiple threads.

    This function is idempotent - multiple calls are safe and will
    only register the TRACE level once.
    """
    global _trace_registered

    # Fast path - already registered
    if _trace_registered:
        return

    # Thread-safe registration with double-checked locking
    with _trace_lock:
        # Check again inside the lock
        if _trace_registered:
            return

        # Check if already registered by someone else (e.g., another library)
        if hasattr(logging, TRACE_LEVEL_NAME):
            _trace_registered = True
            return

        # Register the TRACE level
        logging.addLevelName(TRACE_LEVEL_NUM, TRACE_LEVEL_NAME)
        setattr(logging, TRACE_LEVEL_NAME, TRACE_LEVEL_NUM)

        def trace(self: logging.Logger, message: str, *args: Any, **kws: Any) -> None:
            """Log a message with TRACE level."""
            if self.isEnabledFor(TRACE_LEVEL_NUM):
                self._log(TRACE_LEVEL_NUM, message, args, **kws)

        logging.Logger.trace = trace  # type: ignore
        _trace_registered = True

```

---

## FILE: src/arlogi/types.py

```py
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LoggerProtocol(Protocol):
    """Protocol defining the interface for the arlogi logger."""

    def trace(self, msg: Any, *args: Any, caller_depth: int | None = None, **kwargs: Any) -> None: ...
    def debug(self, msg: Any, *args: Any, caller_depth: int | None = None, **kwargs: Any) -> None: ...
    def info(self, msg: Any, *args: Any, caller_depth: int | None = None, **kwargs: Any) -> None: ...
    def warning(self, msg: Any, *args: Any, caller_depth: int | None = None, **kwargs: Any) -> None: ...
    def error(self, msg: Any, *args: Any, caller_depth: int | None = None, **kwargs: Any) -> None: ...
    def critical(self, msg: Any, *args: Any, caller_depth: int | None = None, **kwargs: Any) -> None: ...
    def fatal(self, msg: Any, *args: Any, caller_depth: int | None = None, **kwargs: Any) -> None: ...
    def exception(self, msg: Any, *args: Any, caller_depth: int | None = None, **kwargs: Any) -> None: ...
    def log(self, level: int, msg: Any, *args: Any, caller_depth: int | None = None, **kwargs: Any) -> None: ...

    def setLevel(self, level: int | str) -> None: ...
    def isEnabledFor(self, level: int) -> bool: ...
    def getEffectiveLevel(self) -> int: ...

    @property
    def name(self) -> str: ...

```
