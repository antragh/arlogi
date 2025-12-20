import logging
import os
import sys
from typing import Any

from .handlers import ArlogiSyslogHandler, ColoredConsoleHandler, JSONFileHandler, JSONHandler
from .levels import TRACE_LEVEL_NUM, register_trace_level
from .types import LoggerProtocol


class TraceLogger(logging.Logger):
    """Custom logger class with trace() and caller attribution support."""

    def _get_caller_info(self, depth: int) -> tuple[str, str]:
        """Find the name of the module and function at the specified depth."""
        try:
            import sys
            # stack:
            # 0: _get_caller_info
            # 1: _handle_from_caller
            # 2: info/debug/... (wrapper)
            # 3: actual call site (depth 0)
            # 4: caller of call site (depth 1)
            frame = sys._getframe(depth + 3)
            module = frame.f_globals.get("__name__", "unknown")
            name = frame.f_code.co_name
            return module, name
        except (ValueError, AttributeError):
            return "unknown", "unknown"

    def _process_params(self, msg: Any, kwargs: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        """Process from_caller and move arbitrary kwargs to 'extra'."""
        # 1. Handle from_caller attribution
        from_val = kwargs.pop("from", kwargs.pop("from_caller", kwargs.pop("from_", None)))

        if from_val is not None:
            try:
                from rich.markup import escape
                depth = int(from_val)

                m0, _ = self._get_caller_info(0)
                mN, nN = self._get_caller_info(depth)

                # Format logic:
                # 0: [name()]
                # 1+: [from .name()] (same module)
                # 1+: [from module.name()] (different module)
                if depth >= 1:
                    if mN == m0:
                        attribution = f"from .{nN}()"
                    else:
                        attribution = f"from {mN}.{nN}()"
                else:
                    attribution = f"{nN}()"

                # Zero space indent here because RichHandler already indents
                # multi-line messages to align with the start of the message.
                safe_attribution = escape(f"[{attribution}]")
                suffix = f"\n{safe_attribution}"

                if isinstance(msg, str):
                    msg = msg + suffix
                else:
                    msg = str(msg) + suffix
            except (ValueError, TypeError, ImportError):
                pass

        # 2. Move unknown kwargs to 'extra'
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

        # Ensure log entries point to the user's code, not this wrapper
        kwargs.setdefault("stacklevel", 2)
        return msg, kwargs

    def trace(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log a message with TRACE level."""
        msg, kwargs = self._process_params(msg, kwargs)
        if self.isEnabledFor(TRACE_LEVEL_NUM):
            # Already set to 2 in _process_params, but self._log needs 2 relative to here
            # trace -> _log. If stacklevel=2, it points to caller of trace.
            self._log(TRACE_LEVEL_NUM, msg, args, **kwargs)

    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        msg, kwargs = self._process_params(msg, kwargs)
        super().debug(msg, *args, **kwargs)

    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        msg, kwargs = self._process_params(msg, kwargs)
        super().info(msg, *args, **kwargs)

    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        msg, kwargs = self._process_params(msg, kwargs)
        super().warning(msg, *args, **kwargs)

    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        msg, kwargs = self._process_params(msg, kwargs)
        super().error(msg, *args, **kwargs)

    def critical(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        msg, kwargs = self._process_params(msg, kwargs)
        super().critical(msg, *args, **kwargs)

    def exception(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        msg, kwargs = self._process_params(msg, kwargs)
        super().exception(msg, *args, **kwargs)

    def log(self, level: int, msg: Any, *args: Any, **kwargs: Any) -> None:
        msg, kwargs = self._process_params(msg, kwargs)
        super().log(level, msg, *args, **kwargs)


class LoggerFactory:
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
        show_time: bool = False,
        show_level: bool = True,
        show_path: bool = True,
    ) -> None:
        """Centralized logging setup for arlogi.

        Can be called multiple times to update configuration.
        """
        register_trace_level()
        logging.setLoggerClass(TraceLogger)

        # Resolve level after TRACE registration
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)

        # Configure root logger
        root = logging.getLogger()
        root.setLevel(level)

        # Clear existing handlers except in test mode where we want to keep pytest handlers
        if not cls.is_test_mode():
            for handler in root.handlers[:]:
                root.removeHandler(handler)

            # 1. JSON File Output
            if json_file_name:
                root.addHandler(JSONFileHandler(json_file_name))

            # 2. Console Output
            # Show console output if it's NOT json_file_only
            # OR if we explicitly want JSON on terminal (no file specified but json_file_only=True)
            if not json_file_only:
                root.addHandler(
                    ColoredConsoleHandler(
                        show_time=show_time, show_level=show_level, show_path=show_path
                    )
                )
            elif not json_file_name:
                # json_file_only = True but no file -> JSON on console
                root.addHandler(JSONHandler())

            # 3. Syslog Output
            if use_syslog:
                root.addHandler(ArlogiSyslogHandler(address=syslog_address))
        # Note: In test mode, we don't add our own handlers to avoid double logging
        # and to keep pytest's caplog working correctly.

        # Apply module-specific levels
        if module_levels:
            for name, m_level in module_levels.items():
                logger = logging.getLogger(name)
                # Resolve string levels
                if isinstance(m_level, str):
                    m_level = getattr(logging, m_level.upper(), logging.INFO)
                logger.setLevel(m_level)
                # Ensure module loggers propagate to root unless specifically configured otherwise
                logger.propagate = True

        cls._initialized = True

    @staticmethod
    def is_test_mode() -> bool:
        """Detect if running under a test runner."""
        return (
            "pytest" in sys.modules
            or "unittest" in sys.modules
            or os.environ.get("PYTEST_CURRENT_TEST") is not None
        )

    @classmethod
    def get_logger(cls, name: str, level: int | str | None = None) -> LoggerProtocol:
        """Get a logger instance conforming to LoggerProtocol."""
        if not cls._initialized:
            # Auto-setup for convenience if called before setup()
            cls.setup(level=logging.DEBUG if cls.is_test_mode() else logging.INFO)

        logger = logging.getLogger(name)
        if level is not None:
            logger.setLevel(level)

        return logger  # type: ignore

    @classmethod
    def get_json_logger(cls, name: str = "json", json_file_name: str | None = None) -> LoggerProtocol:
        """Get a logger that only outputs to JSON, bypassing root handlers."""
        logger = logging.getLogger(f"arlogi.json.{name}")
        logger.propagate = False
        if json_file_name:
            logger.handlers = [JSONFileHandler(json_file_name)]
        else:
            logger.handlers = [JSONHandler()]
        logger.setLevel(logging.DEBUG)
        return logger  # type: ignore

    @classmethod
    def get_syslog_logger(
        cls, name: str = "syslog", address: str | tuple[str, int] = "/dev/log"
    ) -> LoggerProtocol:
        """Get a logger that only outputs to Syslog, bypassing root handlers."""
        logger = logging.getLogger(f"arlogi.syslog.{name}")
        logger.propagate = False
        logger.handlers = [ArlogiSyslogHandler(address=address)]
        logger.setLevel(logging.DEBUG)
        return logger  # type: ignore

    @classmethod
    def get_global_logger(cls) -> LoggerProtocol:
        """Get or initialize the global logger instance."""
        if cls._global_logger is None:
            cls._global_logger = cls.get_logger("app") # type: ignore
        return cls._global_logger # type: ignore


def setup_logging(
    level: int | str = logging.INFO,
    module_levels: dict[str, str | int] | None = None,
    json_file_name: str | None = None,
    json_file_only: bool = False,
    use_syslog: bool = False,
    syslog_address: str | tuple[str, int] = "/dev/log",
    show_time: bool = False,
    show_level: bool = True,
    show_path: bool = True,
) -> None:
    """Helper function to set up arlogi."""
    LoggerFactory.setup(
        level=level,
        module_levels=module_levels,
        json_file_name=json_file_name,
        json_file_only=json_file_only,
        use_syslog=use_syslog,
        syslog_address=syslog_address,
        show_time=show_time,
        show_level=show_level,
        show_path=show_path,
    )


def get_logger(name: str, level: int | str | None = None) -> LoggerProtocol:
    """Helper function to get a logger."""
    return LoggerFactory.get_logger(name, level)


def get_json_logger(name: str = "json", json_file_name: str | None = None) -> LoggerProtocol:
    """Helper function to get a dedicated JSON logger."""
    return LoggerFactory.get_json_logger(name, json_file_name=json_file_name)


def get_syslog_logger(
    name: str = "syslog", address: str | tuple[str, int] = "/dev/log"
) -> LoggerProtocol:
    """Helper function to get a dedicated Syslog logger."""
    return LoggerFactory.get_syslog_logger(name, address)
