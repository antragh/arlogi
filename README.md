# `arlogi` - Advanced Logging Library

`arlogi` is a robust, type-safe logging library for Python that extends the standard logging module with modern features and premium aesthetics.

## Features

- **Custom TRACE Level**: Level 5 logging for ultra-detailed debugging.
- **Premium Colored Output**: Uses `rich` for beautiful, readable console logs with automatic traceback support.
- **Structured JSON Logging**: Out-of-the-box support for JSON logging, perfect for log aggregation systems.
- **Module-Specific Configuration**: Easily set different log levels for different parts of your application.
- **Dedicated Destination Loggers**: Log specific events only to JSON or Syslog without cluttering the console.
- **Type Safety**: Fully type-checked with `LoggerProtocol` and supports modern Python types.
- **SOLID Principles**: Focused on maintainability and clear separation of concerns.

## Usage

### Basic Setup

```python
import logging
from arlogi import setup_logging, get_logger, TRACE

# Initialize with global INFO level
setup_logging(level=logging.INFO)

logger = get_logger("my_app")
logger.info("Application started")
logger.trace("This won't be visible because level is INFO")
```

### Module-Specific Levels

```python
setup_logging(
    level=logging.INFO,
    module_levels={
        "my_app.db": "DEBUG",
        "my_app.network": TRACE
    }
)
```

### JSON and Syslog

```python
setup_logging(
    use_json=True,
    use_syslog=True,
    syslog_address="/dev/log"
)
```

### Dedicated Loggers

Sometimes you want to log specific data ONLY to a file or a remote system:

```python
# Logs only to JSON, not to console
audit_logger = get_json_logger("audit")
audit_logger.info("User logged in", extra={"user_id": 123})

# Logs only to Syslog
syslog_logger = get_syslog_logger("security")
syslog_logger.warning("Failed login attempt")
```

## Advanced Configuration

`arlogi` is highly configurable via the `LoggerFactory.setup()` or `setup_logging()` helper.

- `level`: Global root log level.
- `module_levels`: Dictionary of `module_name: level`.
- `use_json`: Enable JSON output for the root logger.
- `use_syslog`: Enable Syslog output for the root logger.
- `syslog_address`: Address for syslog (path or `(host, port)`).

### Console Styling

By default, `arlogi` uses a clean, modern style for console output. You can further customize this:

```python
setup_logging(
    show_time=True,       # Enable/disable timestamp
    show_level=True,      # Enable/disable level name
    show_path=False,      # Enable/disable source file path
)
```

To make logs start from the very beginning of the line, `arlogi` defaults `show_time` to `False`.

### Color Schemes

`arlogi` comes with a refined default color scheme:

- **TRACE / DEBUG**: Grey
- **INFO**: Bright White
- **WARNING**: Yellow
- **ERROR / CRITICAL**: Red

You can customize these by instantiating `ColoredConsoleHandler` with a `level_styles` dictionary, or by modifying the default behavior in `setup_logging` (coming soon as a direct parameter).

## Development

Run tests with pytest:

```bash
uv run pytest
```

Check types:

```bash
uv run ty check src/
```
