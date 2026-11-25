<p align="center">
  <img src="https://raw.githubusercontent.com/antragh/arlogi/master/docs/logo.svg" width="200" alt="arlogi logo" loading="lazy">
</p>

# `arlogi` - Advanced Logging Library

`arlogi` is a robust, type-safe logging library for Python that extends the standard logging module with modern features, caller attribution, file rotation, and premium aesthetics.

**[Full Documentation](https://antragh.github.io/arlogi/)**

## Features

- **Caller Attribution**: Track log calls across function boundaries using `caller_depth`.
- **Custom TRACE Level**: Level 5 logging for ultra-detailed debugging.
- **Premium Colored Output**: Uses `rich` for beautiful, readable console logs with automatic traceback support.
- **Structured JSON Logging**: Out-of-the-box support for JSON logging, file rotation, and log retention.
- **Module-Specific Configuration**: Easily set different log levels for different parts of your application.
- **Dedicated Destination Loggers**: Log specific events only to JSON or Syslog without cluttering the console.
- **Type Safety**: Fully type-checked with `LoggerProtocol` and supports modern Python types.

## Installation

```bash
# Using uv (recommended)
uv add arlogi

# Or using pip
pip install arlogi
```

## Usage

### Basic Setup

```python
from arlogi import setup_logging, get_logger

# 1. Initialize logging
setup_logging(level="INFO")

# 2. Get a logger
logger = get_logger("my_app")
logger.info("Application started", caller_depth=0)
logger.trace("This won't be visible because level is INFO")
```

### Module-Specific Levels

```python
from arlogi import setup_logging, TRACE

setup_logging(
    level="INFO",
    module_levels={
        "my_app.db": "DEBUG",
        "my_app.network": TRACE
    }
)
```

### JSON File Rotation and Syslog

```python
from arlogi import setup_logging

setup_logging(
    level="INFO",
    json_file_name="logs/app.jsonl",
    rotate_schedule="day",
    rotate_retention_count=7,
    use_syslog=True,
    syslog_address="/dev/log",
    syslog_format="json",  # "text" (default) or "json" (<name>[<pid>]: {...})
)
```

### Dedicated Loggers

Sometimes you want to log specific data ONLY to a file or a remote system:

```python
from arlogi import get_json_logger, get_syslog_logger, cleanup_json_logger

# Logs only to JSON, not to console
audit_logger = get_json_logger("audit", "logs/audit.jsonl")
audit_logger.info("User logged in", user_id=123)

# Logs only to Syslog (supports "text" default or structured "json")
syslog_logger = get_syslog_logger("security", syslog_format="json")
syslog_logger.warning("Failed login attempt", user_id=123)

# Resource cleanup when done
cleanup_json_logger("audit")
```

> **Tip:** `syslog_format="json"` uses `SyslogJSONFormatter` to emit `<name>[<pid>]: {...}` single-line JSON frames. When sending large JSON records or stack traces, prefer a local Unix socket (`/dev/log`) or TCP (`ArlogiSyslogHandler(..., socktype=socket.SOCK_STREAM)`) to avoid UDP MTU truncation.

## Integration with Other Libraries

`arlogi` works seamlessly with any third‑party library that uses the standard `logging` module.

### Default INFO when `arlogi` is not imported

If your application never imports `arlogi`, the standard `logging` defaults (WARNING) remain unchanged. To get a simple INFO level without pulling in `arlogi`, add a tiny bootstrap:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

### Overriding the level when you _do_ use `arlogi`

Initialize `arlogi` with `setup_logging()` early in your program. `setup_logging()` allows fine-grained control over levels and handlers.

### Making third‑party libraries respect the chosen level

All libraries that obtain a logger via `logging.getLogger(name)` inherit the level from the nearest ancestor – usually the root logger configured via `setup_logging()`. If a library forces its own level, reset it:

```python
import logging
logging.getLogger("some_lib").setLevel(logging.NOTSET)  # inherit from root
```

### Quick bootstrap example

```python
# bootstrap.py
import os, logging
from arlogi import setup_logging

def configure_logging():
    if os.getenv("USE_ARLOGI", "0") == "1":
        level = os.getenv("ARLOGI_LEVEL", "INFO").upper()
        setup_logging(level=level)
    else:
        logging.basicConfig(level=logging.INFO)

# main.py
from bootstrap import configure_logging
configure_logging()
```

With this pattern you get:

- **Default INFO** when `arlogi` is absent.
- **Full control** over the log level when you import `arlogi`.
- **Automatic inheritance** for any library that uses `logging`.

### Using TRACE in your library

If you are developing a library and want to use the **TRACE** level:

1. **The Safe Way (Recommended)**: Use `logger.log(TRACE, ...)`
   This works regardless of when your library is imported relative to `arlogi` setup.

   ```python
   import logging
   try:
       from arlogi import TRACE
   except ImportError:
       TRACE = 5

   logger = logging.getLogger(__name__)

   def complex_operation():
       logger.log(TRACE, "Step 1 of complex operation...")
   ```

2. **The method way**: `logger.trace(...)`
   This **only** works if `arlogi` is configured before your library creates its logger instance.

### Lazy Initialization (Safe Use of .trace)

If you _must_ use `.trace()` in your library but aren't sure if `arlogi` is setup yet, you can use lazy initialization with `LoggerProtocol` for type safety:

```python
from arlogi import LoggerProtocol, get_logger

_logger: LoggerProtocol | None = None

def log() -> LoggerProtocol:
    """Get or create the logger for this module lazily."""
    global _logger
    if _logger is None:
        _logger = get_logger("my_lib.cache")
    return _logger
```

## Advanced Configuration

### Centralized Logging Setup

For full control over console output, file paths, and remote handlers:

```python
from arlogi import setup_logging

setup_logging(
    level="INFO",
    module_levels={"app.db": "DEBUG"},
    json_file_name="logs/app.jsonl",
    show_time=True,
    show_level=True,
    show_path=False
)
```

### Direct Factory API and Fluent Builder

Alternatively, `LoggingConfigBuilder`, `LoggerFactory.apply_config(config)`, and `LoggerFactory.setup(...)` provide fluent and object-based configuration with optional `json_file_base_dir` path containment:

```python
from arlogi import LoggerFactory, LoggingConfigBuilder, get_json_logger, rotate_json_logger

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

audit = get_json_logger("audit", "audit.jsonl", base_dir="/var/log/myapp")
audit.info("Audit event")
rotate_json_logger("audit")
```

### Color Schemes

`arlogi` comes with a refined default color scheme:

- **TRACE / DEBUG**: `grey37`
- **INFO**: `grey75`
- **WARNING**: `yellow`
- **ERROR**: `red`
- **CRITICAL**: `bold red`

## OpenTelemetry helpers (`arlogi[otel]`)

```python
from arlogi.otel import (
    install_log_correlation,
    set_trace_modules,
    setup_metrics,
    setup_tracing,
    shutdown_metrics,
    shutdown_tracing,
    traced,
)

setup_tracing("my-service", file_dir="logs")   # owns the TracerProvider
setup_metrics("my-service", file_dir="logs")   # owns the MeterProvider
install_log_correlation()                      # stamps trace_id / span_id onto logs

@traced                                        # span per call
def work(): ...

@traced(name="custom.op", attrs={"component": "billing"})
async def handle(): ...

@traced                                        # async & sync generators: one span
async def stream():                            # covering the full iteration
    yield ...

# Gate spans per module subtree (longest dotted prefix wins; default: on).
set_trace_modules({"myapp": True, "myapp.noisy": False})

# Clean in-process teardown (supports subsequent setup_tracing() / setup_metrics() restart)
shutdown_tracing()
shutdown_metrics()
```

`arlogi.otel` also exports `RotatingJsonlSpanExporter` and `RotatingJsonlMetricExporter` for custom SDK pipelines, and lazily loads all SDK-backed helpers via `__getattr__` so bare `import arlogi.otel` and `from arlogi.otel.decorator import set_trace_modules, traced` depend only on `opentelemetry-api`:

```python
from arlogi.otel.decorator import set_trace_modules, traced
```

## Development

Run tests with pytest:

```bash
uv run pytest
```

Check linting and code formatting:

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

Build local documentation with strict link checking:

```bash
uv run mkdocs build --strict
```

## License

MIT License - see [LICENSE](LICENSE) file for details.
