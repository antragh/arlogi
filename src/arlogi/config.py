"""Logging configuration dataclass for type-safe setup.

This module provides a structured, validated configuration for logging setup,
following the Builder pattern for flexible construction.
"""

import logging
import sys
from dataclasses import dataclass, fields
from typing import Any, Literal

from .levels import TRACE_LEVEL_NUM

RotateSchedule = Literal["hour", "day", "week", "month"]


@dataclass(frozen=True)
class LoggingConfig:
    """Immutable configuration for arlogi logging setup.

    Attributes:
        level: Global root log level (int or string like "INFO")
        module_levels: Per-module level overrides (e.g., {"app.db": "DEBUG"})
        json_file_name: Path to JSON log file (None for no JSON file logging)
        json_file_base_dir: Optional base directory that the JSON log file must stay within (None = no containment)
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
    json_file_base_dir: str | None = None
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
        if self.rotate_retention_count is not None and (
            isinstance(self.rotate_retention_count, bool)
            or not isinstance(self.rotate_retention_count, int)
            or self.rotate_retention_count < 1
        ):
            raise ValueError("rotate_retention_count must be >= 1 when provided")

    @staticmethod
    def _parse_level(level: int | str) -> int:
        """Parse and validate a log level value into an integer.

        Args:
            level: Log level as int (excluding bool) or str

        Returns:
            The resolved log level as an integer

        Raises:
            ValueError: If level is invalid
        """
        if isinstance(level, bool):
            raise ValueError(f"Log level must be int or str, got {type(level).__name__}")
        if isinstance(level, int):
            return level
        if isinstance(level, str):
            upper_level = level.upper()
            if upper_level == "TRACE":
                return TRACE_LEVEL_NUM
            level_map = {
                name: val
                for name, val in logging.getLevelNamesMapping().items()
                if name != "NOTSET" and isinstance(val, int) and not isinstance(val, bool)
            }
            if upper_level in level_map:
                return level_map[upper_level]
            valid = ", ".join(sorted(level_map))
            raise ValueError(f"Invalid log level: {level!r}. Valid levels: TRACE, {valid}")
        raise ValueError(f"Log level must be int or str, got {type(level).__name__}")

    @staticmethod
    def _validate_level(level: int | str) -> None:
        """Validate a log level value.

        Args:
            level: Log level as int or str

        Raises:
            ValueError: If level is invalid
        """
        LoggingConfig._parse_level(level)

    @property
    def resolved_level(self) -> int:
        """Get the global level as an integer.

        Returns:
            The resolved log level as an integer
        """
        return self._parse_level(self.level)

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
        return self._parse_level(level)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to a dictionary.

        Returns:
            Dictionary representation of the configuration
        """
        return {f.name: getattr(self, f.name) for f in fields(self)}

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
        valid_keys = {f.name for f in fields(cls)}

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

    Checks solely whether ``pytest`` or ``unittest`` is loaded in
    ``sys.modules``. Environment variables such as ``PYTEST_CURRENT_TEST``
    are intentionally ignored because they are externally controllable and
    spoofable in production processes.

    Returns:
        True if running in a test environment
    """
    return "pytest" in sys.modules or "unittest" in sys.modules


def get_default_level() -> int:
    """Get the default log level based on the current environment.

    Returns DEBUG in test mode for better test visibility,
    otherwise returns INFO.

    Returns:
        logging.DEBUG if in test mode, logging.INFO otherwise
    """
    return logging.DEBUG if is_test_mode() else logging.INFO
