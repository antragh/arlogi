# Arlogi API Reference

Complete API reference for the arlogi logging library v0.611.25.

---

## Table of Contents

- [Modern Configuration](#modern-configuration)
- [Public API Functions](#public-api-functions)
- [Logger Protocol](#logger-protocol)
- [Handler Classes](#handler-classes)
- [Log Levels](#log-levels)
- [Advanced API](#advanced-api)

---

## Modern Configuration

### `LoggingConfig` and `LoggingConfigBuilder`

The primary way to configure `arlogi` is using `setup_logging(...)`, `LoggerFactory.setup()`, or constructing a `LoggingConfig` (directly or via `LoggingConfigBuilder`) and passing it to `setup_logging(config=...)` or `LoggerFactory.apply_config(config)`.

```python
from arlogi import LoggerFactory, LoggingConfigBuilder, setup_logging

# Keyword-based configuration
setup_logging(
    level="INFO",
    module_levels={"app.db": "DEBUG"},
    json_file_name="app.jsonl",
    json_file_base_dir="logs",
)

# Fluent builder + apply_config()
config = (
    LoggingConfigBuilder()
    .with_level("INFO")
    .with_module_levels({"app.db": "DEBUG"})
    .with_json_file("app.jsonl")
    .with_json_base_dir("/var/log/myapp")
    .with_rotation("day", retention_count=7)
    .build()
)
LoggerFactory.apply_config(config)
```

> **Note:** `json_file_name`, when provided, must be a non-empty, non-whitespace `str`. Passing `config=...` together with any explicit configuration keyword argument to `setup_logging()` or `LoggerFactory.setup()` raises `ValueError`. `LoggingConfigBuilder.with_json_console_only()` clears both `json_file_name` and `json_file_base_dir`.

**Builder Methods (`LoggingConfigBuilder`):**

| Method | Description |
| --- | --- |
| `with_level(level)` | Set global root log level |
| `with_module_levels(levels)` | Set per-module level overrides |
| `with_json_file(file_name, console_also=True)` | Configure JSON file path and console toggle |
| `with_json_base_dir(base_dir)` | Enforce `base_dir` containment for `json_file_name` |
| `with_json_console_only()` | Clear `json_file_name` and `json_file_base_dir` and emit JSON to stderr |
| `with_syslog(address="/dev/log", syslog_format="text")` | Enable syslog output and format |
| `with_console_format(show_time=False, show_level=True, show_path=True)` | Configure Rich console formatting |
| `with_rotation(schedule, retention_count=None)` | Configure JSON file rotation schedule and retention |
| `build()` | Validate and return a frozen `LoggingConfig` |

**Attributes:**

| Attribute        | Type                            | Default        | Description           |
| ---------------- | ------------------------------- | -------------- | --------------------- |
| `level`          | `int \| str`                    | `logging.INFO` | Global root log level |
| `module_levels`  | `Dict[str, str \| int] \| None` | `None`         | Per-module overrides  |
| `json_file_name` | `str \| None`                   | `None`         | JSON log file path    |
| `json_file_base_dir` | `str \| None`               | `None`         | Optional base directory containment for `json_file_name` |
| `json_file_only` | `bool`                          | `False`        | Only JSON output      |
| `use_syslog`     | `bool`                          | `False`        | Enable syslog         |
| `syslog_address` | `str \| tuple[str, int]`        | `"/dev/log"`   | Syslog address        |
| `syslog_format`  | `"text" \| "json"`              | `"text"`       | Syslog output format (`"text"` or `"json"`) |
| `rotate_schedule` | `"hour" \| "day" \| "week" \| "month" \| None` | `None` | Rotation schedule |
| `rotate_retention_count` | `int \| None`           | `None`         | Number of rotated log files to retain |
| `show_time`      | `bool`                          | `False`        | Show timestamps       |
| `show_level`     | `bool`                          | `True`         | Show levels           |
| `show_path`      | `bool`                          | `True`         | Show paths            |

**Methods:**

#### `LoggingConfig.from_kwargs(**kwargs)`

Create a config from keyword arguments. Useful for dynamic configuration from user inputs or environment filters.

#### `LoggingConfig.to_dict()`

Convert configuration to a dictionary for serialization.

#### `LoggingConfig.resolve_module_level(name, level)`

Resolve a module level string to an integer.

```python
level_int = config.resolve_module_level("app.db", "DEBUG")
```

**Properties:**

| Property          | Type   | Description                       |
| ----------------- | ------ | --------------------------------- |
| `resolved_level`  | `int`  | Global level as integer           |
| `show_console`    | `bool` | Whether console output is enabled |
| `has_json_output` | `bool` | Whether JSON output is configured |

---

## Public API Functions

### `setup_logging(..., *, json_file_base_dir=..., syslog_format=..., config=None)`

Configure root logging using either keyword arguments or a pre-built `LoggingConfig` (never both: passing `config` alongside any explicit configuration keyword raises `ValueError`).

```python
from arlogi import LoggingConfigBuilder, setup_logging

setup_logging(
    level="INFO",
    json_file_name="app.jsonl",
    json_file_base_dir="/var/log/myapp",
    rotate_schedule="day",
    rotate_retention_count=7,
)

# Or using a pre-built config:
cfg = LoggingConfigBuilder().with_level("DEBUG").build()
setup_logging(config=cfg)
```

---

### `get_logger(name, level=None)`

Get a logger instance with caller attribution support. When `level` is provided, it accepts `int` (excluding `bool`), case-insensitive level names (`"trace"`, `"debug"`, `"NOTSET"`), or `TRACE`.

```python
from arlogi import get_logger

logger = get_logger("my_app.module")
logger.info("Application started", caller_depth=1)
```

**Parameters:**

| Parameter | Type                 | Default    | Description                        |
| --------- | -------------------- | ---------- | ---------------------------------- |
| `name`    | `str`                | _required_ | Logger name (typically `__name__`) |
| `level`   | `int \| str \| None` | `None`     | Optional level override            |

**Returns:** `LoggerProtocol` - A logger instance

---

### `get_json_logger(name="json", json_file_name=None, base_dir=None)`

Get a logger that only outputs JSON, bypassing root handlers. When `json_file_name` is provided, it must be a non-empty string; `base_dir` enforces path containment within that directory.

```python
from arlogi import get_json_logger

audit_logger = get_json_logger("audit", "audit.jsonl", base_dir="logs")
audit_logger.info("User logged in", extra={"user_id": 123})
```

**Parameters:**

| Parameter        | Type                 | Default  | Description                                       |
| ---------------- | -------------------- | -------- | ------------------------------------------------- |
| `name`           | `str`                | `"json"` | Logger name suffix                                |
| `json_file_name` | `str \| None`        | `None`   | Optional non-empty file path (stderr if `None`)   |
| `base_dir`       | `str \| Path \| None` | `None`  | Optional base directory containment for the file  |

**Returns:** `LoggerProtocol` - A JSON-only logger instance

---

### `rotate_json_logger(name="json")`

Manually rotate all `JSONFileHandler` instances attached to the dedicated JSON logger `arlogi.json.<name>`.

```python
from arlogi import get_json_logger, rotate_json_logger

audit_logger = get_json_logger("audit", "logs/audit.jsonl")
audit_logger.info("Audit event")
rotated = rotate_json_logger("audit")  # Returns number of rotated handlers
```

**Returns:** `int` - Number of handlers successfully rotated

---

### `get_syslog_logger(name="syslog", address="/dev/log", syslog_format="text")`

Get a logger that only outputs to Syslog. Invalid `syslog_format` values raise `ValueError` atomically without detaching any previously attached handler.

```python
from arlogi import get_syslog_logger

syslog_logger = get_syslog_logger("security", syslog_format="json")
syslog_logger.warning("Unauthorized access attempt", ip="203.0.113.10")
```

**Parameters:**

| Parameter       | Type               | Default      | Description                                   |
| --------------- | ------------------ | ------------ | --------------------------------------------- |
| `name`          | `str`              | `"syslog"`   | Logger name suffix                            |
| `address`       | `str \| tuple`     | `"/dev/log"` | Syslog server address                         |
| `syslog_format` | `"text" \| "json"` | `"text"`     | Syslog output format (`"text"` or `"json"`)   |

**Returns:** `LoggerProtocol` - A syslog-only logger instance

---

### `cleanup_json_logger(name)`

Clean up handlers for a JSON logger to free resources.

```python
from arlogi import get_json_logger, cleanup_json_logger

logger = get_json_logger("temp", "logs/temp.json")
logger.info("Done logging")
cleanup_json_logger("temp")  # Close the file handle
```

**Parameters:**

| Parameter | Type     | Default   | Description                           |
| --------- | -------- | --------- | ------------------------------------- |
| `name`    | `str`    | `"json"`  | Logger name suffix (must match name used in get_json_logger) |

---

### `cleanup_syslog_logger(name)`

Clean up handlers for a syslog logger to free resources.

```python
from arlogi import get_syslog_logger, cleanup_syslog_logger

logger = get_syslog_logger("temp")
logger.info("Done logging")
cleanup_syslog_logger("temp")  # Close the socket
```

**Parameters:**

| Parameter | Type     | Default      | Description                           |
| --------- | -------- | ------------ | ------------------------------------- |
| `name`    | `str`    | `"syslog"`   | Logger name suffix                    |

---

## Logger Protocol

### `LoggerProtocol`

Protocol defining the interface for arlogi loggers.

**Methods:**

#### Standard Logging Methods

All methods support caller attribution via the `caller_depth` parameter.

```python
logger.trace(msg, *args, caller_depth=None, **kwargs)
logger.debug(msg, *args, caller_depth=None, **kwargs)
logger.info(msg, *args, caller_depth=None, **kwargs)
logger.warning(msg, *args, caller_depth=None, **kwargs)
logger.error(msg, *args, caller_depth=None, **kwargs)
logger.critical(msg, *args, caller_depth=None, **kwargs)
logger.fatal(msg, *args, caller_depth=None, **kwargs)
logger.exception(msg, *args, caller_depth=None, **kwargs)
logger.log(level, msg, *args, caller_depth=None, **kwargs)
```

**Caller Attribution Parameter:**

| Parameter     | Type          | Description                                  |
| ------------- | ------------- | -------------------------------------------- |
| `caller_depth` | `int \| None` | Stack depth (0=current, 1=caller, 2+=deeper) |

#### Level Management

```python
logger.setLevel(level)      # Set logger level
logger.isEnabledFor(level)  # Check if level is enabled
logger.getEffectiveLevel()  # Get effective level
```

#### Properties

| Property | Type  | Description |
| -------- | ----- | ----------- |
| `name`   | `str` | Logger name |

---

## Handler Classes

### `ColoredConsoleHandler`

Rich-based colored console handler with premium formatting.

```python
from arlogi.handlers import ColoredConsoleHandler

handler = ColoredConsoleHandler(
    show_time=True,
    show_level=True,
    show_path=True,
    level_styles={"info": "blue", "error": "red"}
)
```

**Parameters:**

| Parameter      | Type                     | Default         | Description                                     |
| -------------- | ------------------------ | --------------- | ----------------------------------------------- |
| `show_time`    | `bool`                   | `False`         | Show timestamps                                 |
| `show_level`   | `bool`                   | `True`          | Show log levels                                 |
| `show_path`    | `bool`                   | `True`          | Show file paths                                 |
| `markup`       | `bool`                   | `False`         | Enable Rich markup in messages (default: False) |
| `level_styles` | `Dict[str, str] \| None` | `None`          | Custom level colors                             |
| `project_root` | `str \| None`            | `auto-detected` | Project root for paths                          |

**Level Color Options:**

| Level    | Default Color | Alternative Colors            |
| -------- | ------------- | ----------------------------- |
| TRACE    | `grey37`      | `dim cyan`, `dim blue`        |
| DEBUG    | `grey37`      | `dim cyan`, `grey50`          |
| INFO     | `grey75`      | `white`, `green`              |
| WARNING  | `yellow`      | `orange`, `bold yellow`       |
| ERROR    | `red`         | `bold red`, `bright_red`      |
| CRITICAL | `bold red`    | `red on white`, `reverse red` |

---

### `JSONHandler` and `JSONFormatter`

Stream handler that outputs structured JSON to stderr (or a caller-provided stream). `JSONFormatter` protects canonical top-level envelope keys (`timestamp`, `level`, `logger_name`, `message`, `module`, `function`, `line_number`, `exception`) by routing colliding user `extra` or keyword keys into a nested `"extra"` object, and emits valid fallback JSON if serialization raises.

```python
from arlogi.handlers import JSONHandler

handler = JSONHandler()
```

**JSON Output Format:**

```json
{
  "timestamp": "2025-12-28T10:30:00.123456",
  "level": "INFO",
  "logger_name": "my_app",
  "message": "User logged in",
  "module": "main",
  "function": "login",
  "line_number": 42,
  "user_id": 123,
  "ip": "192.168.1.1"
}
```

---

### `JSONFileHandler`

File handler that outputs JSON to a file, with optional schedule rotation, retention pruning, and `base_dir` path containment.

```python
from arlogi.handlers import JSONFileHandler

handler = JSONFileHandler(
    filename="app.jsonl",
    mode="a",
    encoding="utf-8",
    rotate_schedule="day",
    rotate_retention_count=7,
    base_dir="logs",
)
```

**Parameters:**

| Parameter                | Type                  | Default    | Description                                                    |
| ------------------------ | --------------------- | ---------- | -------------------------------------------------------------- |
| `filename`               | `str`                 | _required_ | Path to log file                                               |
| `mode`                   | `str`                 | `"a"`      | File open mode                                                 |
| `encoding`               | `str \| None`         | `None`     | File encoding                                                  |
| `delay`                  | `bool`                | `False`    | Delay file opening                                             |
| `rotate_schedule`        | `str \| None`         | `None`     | Rotation schedule (`"hour"`, `"day"`, `"week"`, `"month"`)     |
| `rotate_retention_count` | `int \| None`         | `None`     | Number of rotated archives to retain (`>= 1`, defaults to `7` when scheduled) |
| `base_dir`               | `str \| Path \| None` | `None`     | Base directory the resolved log path must remain within        |

**Note:** Parent directories are created automatically after validating parameters and `base_dir` containment.

---

### `SyslogJSONFormatter`

Subclass of `JSONFormatter` used by `ArlogiSyslogHandler` when `syslog_format="json"`. Formats each record as a single-line RFC 3164 TAG+JSON frame (`<record.name>[<record.process>]: <json_payload>`), preserving `JSONFormatter`'s canonical envelope protection, nested `"extra"` routing, OpenTelemetry `trace_id`/`span_id` correlation fields, and non-raising fallback JSON.

```python
from arlogi.handlers import SyslogJSONFormatter

formatter = SyslogJSONFormatter()
```

---

### `ArlogiSyslogHandler`

Syslog handler with automatic fallback support for the default `/dev/log` socket.

```python
from arlogi.handlers import ArlogiSyslogHandler

handler = ArlogiSyslogHandler(
    address="/dev/log",  # or ("localhost", 514)
    facility="user",
    socktype=None,
    syslog_format="text",  # or "json"
)
```

**Parameters:**

| Parameter       | Type               | Default      | Description                                 |
| --------------- | ------------------ | ------------ | ------------------------------------------- |
| `address`       | `str \| tuple`     | `"/dev/log"` | Syslog server address                       |
| `facility`      | `int \| str`       | `LOG_USER`   | Syslog facility                             |
| `socktype`      | `int \| None`      | `None`       | Socket type                                 |
| `syslog_format` | `"text" \| "json"` | `"text"`     | Syslog output format (`"text"` or `"json"`) |

**Formatting & Fallback Behavior:**

1. Validates `syslog_format` eagerly (exact lowercase `"text"` or `"json"`) before probing `/dev/log` or opening any socket; invalid values raise `ValueError`.
2. `"text"` emits `%(name)s[%(process)d]: %(levelname)s: %(message)s"`; `"json"` attaches `SyslogJSONFormatter` emitting single-line `<name>[<pid>]: {...}` frames.
3. When using the default `address="/dev/log"`, if `/dev/log` is missing or fails, falls back to UDP on `("localhost", 514)`, and degrades silently (`_failed = True`) if both fail while preserving the configured formatter.
4. For custom addresses (such as a remote `(host, port)`), initialization errors (for example `OSError` / `socket.gaierror`) are raised to the caller instead of being swallowed.
5. For large JSON records or stack traces, prefer a local Unix socket (`/dev/log`) or TCP (`socktype=socket.SOCK_STREAM`) to avoid UDP MTU truncation.

---

## Log Levels

### Standard Python Levels

```python
import logging

logging.DEBUG    # 10
logging.INFO     # 20
logging.WARNING  # 30
logging.ERROR    # 40
logging.CRITICAL # 50
```

### Custom Arlogi Level

```python
from arlogi import TRACE

TRACE  # 5 - Below DEBUG for ultra-detailed logging
```

### Level Usage Guidelines

| Level    | Value | Use Case                            |
| -------- | ----- | ----------------------------------- |
| TRACE    | 5     | Function entry/exit, variable dumps |
| DEBUG    | 10    | Detailed troubleshooting info       |
| INFO     | 20    | General application flow            |
| WARNING  | 30    | Unexpected but recoverable issues   |
| ERROR    | 40    | Errors that don't stop execution    |
| CRITICAL | 50    | Serious failures, possible shutdown |

---

## Advanced API

### `LoggerFactory`

Factory for creating and configuring loggers.

```python
from arlogi import LoggerFactory

# Direct setup
LoggerFactory.setup(level="INFO")

# Get logger
logger = LoggerFactory.get_logger("my_app")

# Get dedicated loggers
json_logger = LoggerFactory.get_json_logger("audit")
syslog_logger = LoggerFactory.get_syslog_logger("security")
```

**Class Methods:**

| Method                                  | Description                                      |
| --------------------------------------- | ------------------------------------------------ |
| `setup(**kwargs)`                       | Configure logging (public entry)                 |
| `apply_config(config)`                  | Apply a pre-built `LoggingConfig` under lock     |
| `get_logger(name, level)`               | Get a logger                                     |
| `get_json_logger(name, file, base_dir)` | Get JSON-only logger with optional containment   |
| `get_syslog_logger(name, addr, syslog_format)` | Get syslog-only logger                    |
| `cleanup_json_logger(name)`             | Clean up JSON logger handlers                    |
| `cleanup_syslog_logger(name)`           | Clean up syslog logger handlers                  |
| `is_test_mode()`                        | Check if in test environment                     |
| `get_global_logger()`                   | Get global application logger                    |

**Internal Methods:**

| Method                             | Description           |
| ---------------------------------- | --------------------- |
| `_initialize_trace_level()`        | Register TRACE level  |
| `_configure_root_logger(config)`   | Set root logger level |
| `_clear_and_add_handlers(config)`  | Configure handlers    |
| `_configure_module_levels(config)` | Set module levels     |

---

### `HandlerFactory`

Factory for creating log handlers.

```python
from arlogi import HandlerFactory, LoggingConfig

config = LoggingConfig(show_time=True, show_level=True)

# Create individual handlers
console = HandlerFactory.create_console(config)
json_file = HandlerFactory.create_json_file(config)
syslog = HandlerFactory.create_syslog(config)

# Create all handlers at once
handlers = HandlerFactory.create_handlers(config)
```

**Static Methods:**

| Method                        | Returns                 | Description              |
| ----------------------------- | ----------------------- | ------------------------ |
| `create_console(config)`      | `ColoredConsoleHandler` | Console handler          |
| `create_json_stream()`        | `JSONHandler`           | Stream JSON handler      |
| `create_json_file(config)`    | `JSONFileHandler`       | File JSON handler        |
| `create_json_handler(config)` | `Handler`               | Appropriate JSON handler |
| `create_syslog(config)`       | `ArlogiSyslogHandler`   | Syslog handler           |
| `create_handlers(config)`     | `List[Handler]`         | All configured handlers  |

---

### Utility Functions

#### `is_test_mode()`

Detect if running under a test runner.

```python
from arlogi import is_test_mode

if is_test_mode():
    logger.debug("Test mode detected")
```

**Returns:** `bool` - True if `pytest` or `unittest` is loaded in `sys.modules` (`PYTEST_CURRENT_TEST` is intentionally ignored)

---

#### `get_default_level()`

Get the default log level based on environment.

```python
from arlogi import get_default_level

level = get_default_level()  # DEBUG in tests, INFO otherwise
```

**Returns:** `int` - `logging.DEBUG` if in test mode, `logging.INFO` otherwise

---

## Optional OpenTelemetry API (`arlogi.otel`)

When installed with `arlogi[otel]`, `arlogi.otel` exports:

- `setup_tracing(service_name, service_version=None, *, file_dir, file_prefix="traces", rotate_hours=24, retention_count=20, otlp_endpoint=None, otlp_timeout=5) -> TracerProvider`
- `shutdown_tracing() -> None`
- `setup_metrics(service_name, service_version=None, *, file_dir, file_prefix="metrics", rotate_hours=24, retention_count=20, otlp_endpoint=None, otlp_timeout=5, export_interval_millis=60_000) -> MeterProvider`
- `shutdown_metrics() -> None`
- `install_log_correlation() -> None`
- `set_trace_modules(rules: dict[str, bool] | None) -> None`
- `traced` (sync, async, sync generator, and async generator decorator; `opentelemetry-api`-only)
- `RotatingJsonlSpanExporter` / `RotatingJsonlMetricExporter`

Bare `import arlogi.otel` and `import arlogi.otel.decorator` never eagerly import `opentelemetry.sdk`.

---

## Type Hints

### LoggerProtocol

```python
from typing import Protocol, Any

@runtime_checkable
class LoggerProtocol(Protocol):
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

---

## Examples

### Modern Basic Usage

```python
from arlogi import setup_logging, get_logger

setup_logging(level="INFO")

logger = get_logger("my_app")
logger.info("Application started")
```

### Caller Attribution

```python
def outer_function():
    logger.info("Processing data", caller_depth=1)

def inner_function():
    logger.debug("Step 1")  # Shows inner_function (default caller_depth=None)
    logger.debug("Step 2", caller_depth=1)  # Shows outer_function
```

### Advanced Module Configuration

```python
from arlogi import setup_logging

setup_logging(
    level="INFO",
    module_levels={
        "app.database": "DEBUG",
        "app.network": "TRACE",
        "app.security": "WARNING"
    }
)
```

### JSON Logging

```python
from arlogi import setup_logging, get_json_logger

# With console + JSON file
setup_logging(json_file_name="logs/app.jsonl")

# JSON only to console
setup_logging(json_file_only=True)

# Dedicated JSON logger
audit = get_json_logger("audit", "logs/audit.jsonl")
audit.info("User action", extra={"user_id": 123})
```

### Syslog

```python
from arlogi import setup_logging, get_syslog_logger

# Add syslog to root logger
setup_logging(use_syslog=True)

# Dedicated syslog logger
syslog = get_syslog_logger("security")
syslog.warning("Security event")
```

---

## Error Handling

All arlogi functions handle errors gracefully:

- Invalid log levels raise `ValueError` with helpful messages
- Syslog connection failures fall back automatically only for the default `/dev/log` address; explicit custom addresses raise initialization errors to the caller
- JSON file handler creates parent directories automatically
- Test mode detection prevents double logging in pytest

---

## Version History

| Version         | Changes                                                                                                                  |
| --------------- | ------------------------------------------------------------------------------------------------------------------------ |
| 0.611.25        | Security & lifecycle hardening: path confinement, JSON envelope key protection, OTel lifecycle/generator tracing, CI/sdist |
| 0.609.0–0.611.3 | OpenTelemetry `arlogi[otel]` integration, `@traced` sync/async/generator tracing, rotating JSONL exporters, audit fixes  |
| 0.606.22        | Rotation, syslog, and resource cleanup                                                                                   |
| 0.601.04        | Enhanced resource cleanup, improved test mode detection                                                                  |
| 0.601.00        | Added cleanup_json_logger, cleanup_syslog_logger                                                                         |
| 0.512.28        | Added LoggingConfig, HandlerFactory, reduced complexity                                                                  |
| 0.512.20        | Initial caller attribution support                                                                                       |
| 0.512.0         | First stable release                                                                                                     |

---

## License

MIT License - see LICENSE file for details.
