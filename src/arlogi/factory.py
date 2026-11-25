"""Factory for creating logger instances with caller attribution support.

This module provides the LoggerFactory class for creating and configuring
loggers, along with the TraceLogger class that adds custom TRACE level
and caller attribution features.
"""

import logging
import threading
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .config import LoggingConfig, get_default_level, is_test_mode
from .handler_factory import HandlerFactory
from .handlers import ArlogiSyslogHandler, JSONFileHandler, JSONHandler
from .levels import TRACE_LEVEL_NUM, register_trace_level
from .types import LoggerProtocol

_SETUP_DEFAULTS: dict[str, Any] = {
    "level": logging.INFO,
    "module_levels": None,
    "json_file_name": None,
    "json_file_base_dir": None,
    "json_file_only": False,
    "use_syslog": False,
    "syslog_address": "/dev/log",
    "rotate_schedule": None,
    "rotate_retention_count": None,
    "show_time": False,
    "show_level": True,
    "show_path": True,
}


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
            # 1: _apply_caller_attribution
            # 2: _process_params
            # 3: info/debug/... (wrapper method)
            # 4: actual call site (depth 0)
            # 5: caller of call site (depth 1)
            frame = sys._getframe(depth + 4)
            module = frame.f_globals.get("__name__", "unknown")
            name = frame.f_code.co_name
            return module, name
        except (ValueError, AttributeError):
            return "unknown", "unknown"

    def _apply_caller_attribution(self, msg: Any, caller_depth_val: Any) -> tuple[Any, str | None]:
        """Append caller attribution suffix to msg when caller_depth is provided."""
        if caller_depth_val is None:
            return msg, None
        try:
            depth = int(caller_depth_val)
            m0, _ = self._get_caller_info(0)
            mN, nN = self._get_caller_info(depth)

            if depth >= 1:
                attribution = f"from .{nN}()" if mN == m0 else f"from {mN}.{nN}()"
            else:
                attribution = f"{nN}()"

            suffix = f"\n[{attribution}]"
            return (msg if isinstance(msg, str) else str(msg)) + suffix, attribution
        except (ValueError, TypeError):
            return msg, None

    def _process_params(self, msg: Any, kwargs: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        """Process caller attribution and move arbitrary kwargs to 'extra'.

        Args:
            msg: The log message
            kwargs: Keyword arguments including optional caller_depth

        Returns:
            Tuple of (processed_message, processed_kwargs)
        """
        msg, attribution = self._apply_caller_attribution(msg, kwargs.pop("caller_depth", None))

        # Move unknown kwargs to 'extra' without mutating caller dicts
        standard_kwargs = {"exc_info", "stack_info", "stacklevel", "extra"}
        extra = kwargs.get("extra")

        custom_kwargs = {key: kwargs.pop(key) for key in list(kwargs.keys()) if key not in standard_kwargs}
        if attribution is not None:
            custom_kwargs["_arlogi_attribution"] = attribution

        if custom_kwargs:
            if extra is None:
                kwargs["extra"] = dict(custom_kwargs)
            elif isinstance(extra, Mapping):
                kwargs["extra"] = {**extra, **custom_kwargs}
            else:
                kwargs["extra"] = {"_original_extra": extra, **custom_kwargs}

        raw_sl = kwargs.get("stacklevel", 1)
        kwargs["stacklevel"] = (raw_sl + 1) if isinstance(raw_sl, int) and not isinstance(raw_sl, bool) else 2
        return msg, kwargs

    # Standard logging methods with caller attribution support
    def trace(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log a message with TRACE level (below DEBUG).

        Args:
            msg: The message to log
            *args: Format arguments for the message
            **kwargs: Optional caller_depth for caller attribution
        """
        if self.isEnabledFor(TRACE_LEVEL_NUM):
            msg, kwargs = self._process_params(msg, kwargs)
            self._log(TRACE_LEVEL_NUM, msg, args, **kwargs)

    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        if self.isEnabledFor(logging.DEBUG):
            msg, kwargs = self._process_params(msg, kwargs)
            super().debug(msg, *args, **kwargs)

    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        if self.isEnabledFor(logging.INFO):
            msg, kwargs = self._process_params(msg, kwargs)
            super().info(msg, *args, **kwargs)

    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        if self.isEnabledFor(logging.WARNING):
            msg, kwargs = self._process_params(msg, kwargs)
            super().warning(msg, *args, **kwargs)

    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        if self.isEnabledFor(logging.ERROR):
            msg, kwargs = self._process_params(msg, kwargs)
            super().error(msg, *args, **kwargs)

    def critical(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        if self.isEnabledFor(logging.CRITICAL):
            msg, kwargs = self._process_params(msg, kwargs)
            super().critical(msg, *args, **kwargs)

    def fatal(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log a fatal (critical) message."""
        if self.isEnabledFor(logging.CRITICAL):
            msg, kwargs = self._process_params(msg, kwargs)
            super().critical(msg, *args, **kwargs)

    def exception(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log an exception with traceback."""
        if self.isEnabledFor(logging.ERROR):
            kwargs.setdefault("exc_info", True)
            msg, kwargs = self._process_params(msg, kwargs)
            super().error(msg, *args, **kwargs)

    def log(self, level: int, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log a message at the specified level."""
        if not isinstance(level, int) or isinstance(level, bool):
            if logging.raiseExceptions:
                raise TypeError("level must be an integer")
            return
        if self.isEnabledFor(level):
            msg, kwargs = self._process_params(msg, kwargs)
            super().log(level, msg, *args, **kwargs)


class LoggerFactory:
    """Factory for creating and configuring logger instances.

    This factory manages the global logging configuration and provides
    methods to get logger instances with various configurations.
    """

    _initialized = False
    _global_logger: TraceLogger | None = None
    _init_lock = threading.RLock()
    _dedicated_lock = threading.RLock()

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
        *,
        json_file_base_dir: str | None = None,
        config: LoggingConfig | None = None,
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
            json_file_base_dir: Optional base directory the JSON log file must stay within
            config: Optional pre-built LoggingConfig (cannot be combined with explicit overrides)
        """
        raw_params: dict[str, Any] = {
            "level": level,
            "module_levels": module_levels,
            "json_file_name": json_file_name,
            "json_file_base_dir": json_file_base_dir,
            "json_file_only": json_file_only,
            "use_syslog": use_syslog,
            "syslog_address": syslog_address,
            "rotate_schedule": rotate_schedule,
            "rotate_retention_count": rotate_retention_count,
            "show_time": show_time,
            "show_level": show_level,
            "show_path": show_path,
        }
        if config is not None:
            overridden = [
                k for k, v in raw_params.items() if v != _SETUP_DEFAULTS[k] or type(v) is not type(_SETUP_DEFAULTS[k])
            ]
            if overridden:
                raise ValueError(f"Cannot combine 'config' with explicit keyword arguments: {', '.join(overridden)}")
            cls.apply_config(config)
            return

        with cls._init_lock:
            built_config = LoggingConfig.from_kwargs(**raw_params)
            cls._apply_configuration(built_config)

    @classmethod
    def apply_config(cls, config: LoggingConfig) -> None:
        """Apply a pre-built LoggingConfig to the root logger under lock.

        Args:
            config: The validated LoggingConfig instance to apply
        """
        with cls._init_lock:
            cls._apply_configuration(config)

    @classmethod
    def _apply_configuration(cls, config: LoggingConfig) -> None:
        """Apply a LoggingConfig to the root logger.

        Args:
            config: The logging configuration to apply
        """
        with cls._init_lock:
            cls._initialize_trace_level()
            if not is_test_mode():
                cls._clear_and_add_handlers(config)
            cls._configure_root_logger(config)
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
        """Clear existing handlers and add configured ones atomically.

        Constructs replacement handlers first so a configuration or I/O error
        never leaves the root logger without its existing working handlers.

        Args:
            config: The logging configuration
        """
        root = logging.getLogger()
        new_handlers = HandlerFactory.create_handlers(config)
        old_handlers = root.handlers[:]

        for handler in old_handlers:
            root.removeHandler(handler)

        for handler in new_handlers:
            root.addHandler(handler)

        for handler in old_handlers:
            try:
                handler.close()
            except Exception:
                pass

    @staticmethod
    def _get_existing_logger(logger_name: str) -> logging.Logger | None:
        """Return an already-created logger without instantiating a placeholder."""
        existing = logging.Logger.manager.loggerDict.get(logger_name)
        if isinstance(existing, logging.Logger):
            return existing
        return None

    @staticmethod
    def _replace_logger_handlers(logger: logging.Logger, new_handler: logging.Handler) -> None:
        """Detach old handlers, attach replacement, then close old handlers."""
        old_handlers = logger.handlers[:]
        for handler in old_handlers:
            logger.removeHandler(handler)
        logger.addHandler(new_handler)
        for handler in old_handlers:
            try:
                handler.close()
            except Exception:
                pass

    @staticmethod
    def _detach_and_close_handlers(logger: logging.Logger) -> None:
        """Detach all handlers from a logger before closing them."""
        old_handlers = logger.handlers[:]
        for handler in old_handlers:
            logger.removeHandler(handler)
        for handler in old_handlers:
            try:
                handler.close()
            except Exception:
                pass

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

        Checks solely whether ``pytest`` or ``unittest`` is loaded in
        ``sys.modules``. ``PYTEST_CURRENT_TEST`` is intentionally ignored.

        Returns:
            True if pytest or unittest is loaded in sys.modules
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
            with cls._init_lock:
                if not cls._initialized:
                    cls.setup(level=get_default_level())

        logger = logging.getLogger(name)
        if level is not None:
            logger.setLevel(level)

        return logger  # type: ignore

    @classmethod
    def get_json_logger(
        cls,
        name: str = "json",
        json_file_name: str | None = None,
        base_dir: str | Path | None = None,
    ) -> LoggerProtocol:
        """Get a logger that only outputs to JSON, bypassing root handlers.

        Args:
            name: Logger name suffix
            json_file_name: Optional file path for JSON output
            base_dir: Optional base directory the JSON log file must stay within

        Returns:
            A JSON-only logger instance
        """
        with cls._init_lock:
            cls._initialize_trace_level()

        if base_dir is not None and not json_file_name:
            raise ValueError("base_dir cannot be specified when json_file_name is None")

        with cls._dedicated_lock:
            new_handler: logging.Handler = (
                JSONFileHandler(json_file_name, base_dir=base_dir) if json_file_name else JSONHandler()
            )
            logger = logging.getLogger(f"arlogi.json.{name}")
            logger.propagate = False
            cls._replace_logger_handlers(logger, new_handler)
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
        with cls._init_lock:
            cls._initialize_trace_level()

        with cls._dedicated_lock:
            new_handler = ArlogiSyslogHandler(address=address)
            logger = logging.getLogger(f"arlogi.syslog.{name}")
            logger.propagate = False
            cls._replace_logger_handlers(logger, new_handler)
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
        with cls._dedicated_lock:
            logger = cls._get_existing_logger(f"arlogi.json.{name}")
            if logger is not None:
                cls._detach_and_close_handlers(logger)

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
        with cls._dedicated_lock:
            logger = cls._get_existing_logger(f"arlogi.syslog.{name}")
            if logger is not None:
                cls._detach_and_close_handlers(logger)

    @classmethod
    def get_global_logger(cls) -> LoggerProtocol:
        """Get or initialize the global logger instance.

        Returns:
            The global application logger instance
        """
        if cls._global_logger is None:
            with cls._init_lock:
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
    *,
    json_file_base_dir: str | None = None,
    config: LoggingConfig | None = None,
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
        json_file_base_dir: Optional base directory the JSON log file must stay within
        config: Optional pre-built LoggingConfig (cannot be combined with explicit overrides)
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
        json_file_base_dir=json_file_base_dir,
        config=config,
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


def get_json_logger(
    name: str = "json",
    json_file_name: str | None = None,
    base_dir: str | Path | None = None,
) -> LoggerProtocol:
    """Get a dedicated JSON-only logger.

    Args:
        name: Logger name suffix
        json_file_name: Optional file path for JSON output
        base_dir: Optional base directory the JSON log file must stay within

    Returns:
        A JSON-only logger instance
    """
    return LoggerFactory.get_json_logger(name, json_file_name=json_file_name, base_dir=base_dir)


def rotate_json_logger(name: str = "json") -> int:
    """Rotate JSON file handlers attached to the named JSON logger.

    Args:
        name: Logger name suffix (must match get_json_logger usage)

    Returns:
        Number of handlers successfully rotated
    """
    with LoggerFactory._dedicated_lock:
        logger = LoggerFactory._get_existing_logger(f"arlogi.json.{name}")
        if logger is None:
            return 0
        rotated = 0
        for handler in list(logger.handlers):
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
