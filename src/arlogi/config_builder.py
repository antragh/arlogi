"""Builder pattern for LoggingConfig construction.

This module provides a fluent builder API for constructing logging
configurations, making complex configurations more readable and
less error-prone than direct constructor calls.
"""

import logging

from .config import LoggingConfig, RotateSchedule, SyslogFormat


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
        self._level: int | str = logging.INFO
        self._module_levels: dict[str, str | int] | None = None
        self._json_file_name: str | None = None
        self._json_file_base_dir: str | None = None
        self._json_file_only = False
        self._use_syslog = False
        self._syslog_address: str | tuple[str, int] = "/dev/log"
        self._syslog_format: SyslogFormat = "text"
        self._rotate_schedule: RotateSchedule | None = None
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

    def with_json_base_dir(self, base_dir: str | None) -> "LoggingConfigBuilder":
        """Set the base directory that the JSON log file must stay within.

        Args:
            base_dir: Base directory the JSON log file must stay within
                (None to disable containment checks)

        Returns:
            Self for method chaining

        Example:
            >>> builder.with_json_base_dir("/var/log/myapp")
        """
        self._json_file_base_dir = base_dir
        return self

    def with_json_console_only(self) -> "LoggingConfigBuilder":
        """Configure JSON output to console only (stderr, no file).

        Returns:
            Self for method chaining

        Example:
            >>> builder.with_json_console_only()
        """
        self._json_file_name = None
        self._json_file_base_dir = None
        self._json_file_only = True
        return self

    def with_syslog(
        self, address: str | tuple[str, int] = "/dev/log", syslog_format: SyslogFormat = "text"
    ) -> "LoggingConfigBuilder":
        """Enable syslog output.

        Args:
            address: Syslog server address (default: "/dev/log" for Unix socket)
            syslog_format: Syslog output format ("text" or "json", default: "text")

        Returns:
            Self for method chaining

        Example:
            >>> # Unix socket
            >>> builder.with_syslog()
            >>>
            >>> # Remote syslog server with JSON payload
            >>> builder.with_syslog(("192.168.1.1", 514), syslog_format="json")
        """
        self._use_syslog = True
        self._syslog_address = address
        self._syslog_format = syslog_format
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

    def with_rotation(self, schedule: RotateSchedule, retention_count: int | None = None) -> "LoggingConfigBuilder":
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
            json_file_base_dir=self._json_file_base_dir,
            json_file_only=self._json_file_only,
            use_syslog=self._use_syslog,
            syslog_address=self._syslog_address,
            syslog_format=self._syslog_format,
            rotate_schedule=self._rotate_schedule,
            rotate_retention_count=self._rotate_retention_count,
            show_time=self._show_time,
            show_level=self._show_level,
            show_path=self._show_path,
        )
