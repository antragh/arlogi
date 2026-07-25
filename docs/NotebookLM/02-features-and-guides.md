# Arlogi User Guides and API Reference

---

## FILE: docs/USER_GUIDE.md

# Arlogi User Guide

Complete user guide for the arlogi logging library. Learn how to install, configure, and use arlogi effectively.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Basic Usage](#basic-usage)
- [Configuration](#configuration)
- [Caller Attribution](#caller-attribution)
- [Output Handlers](#output-handlers)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

---

## Installation

### Requirements

- Python 3.13 or higher (required)
- `rich` >= 14.2.0 (automatically installed)

Arlogi requires Python 3.13+ as specified in the project configuration.

### Using Pip

```bash
pip install arlogi
```

### Using Uv

```bash
uv add arlogi
```

### From Source

```bash
git clone https://github.com/your-org/arlogi.git
cd arlogi
pip install -e .
```

---

## Quick Start

### Minimal Setup

```python
from arlogi import setup_logging, get_logger

# 1. Configure logging
setup_logging(level="INFO")

# 2. Get a logger
logger = get_logger(__name__)

# 3. Log a message
logger.info("Hello, Arlogi!")
```

**Output:**

```text
I  Hello, Arlogi!    your_module.py:7
```

---

## Basic Usage

### Log Levels

```python
from arlogi import get_logger, TRACE

logger = get_logger(__name__)

# Ultra-detailed debugging
logger.trace("Variable value: x = %s", x, caller_depth=0)

# Detailed information for troubleshooting
logger.debug("SQL query: %s", query, caller_depth=1)

# General information about application flow
logger.info("User logged in successfully", user_id=123)

# Something unexpected, but application continues
logger.warning("Configuration file not found, using defaults")

# Error occurred, application can continue
logger.error("Failed to connect to database", database="users")

# Serious error, application may not continue
logger.critical("Out of memory, shutting down")
```

### Logging Exceptions

```python
from arlogi import get_logger

logger = get_logger(__name__)

def process_data(data):
    try:
        result = complex_operation(data)
        return result
    except Exception as e:
        # Logs exception with full traceback
        logger.exception("Failed to process data", data_id=data.get("id"))
        raise
```

### Structured Logging

```python
from arlogi import get_logger

logger = get_logger(__name__)

# Add extra fields for structured logging
logger.info(
    "API request processed",
    request_id="req-abc-123",
    method="GET",
    path="/api/users",
    status_code=200,
    duration_ms=45
)
```

---

## Configuration

### Basic Configuration

Configure `arlogi` using the `LoggingConfig` pattern. This approach clearly separates configuration data from initialization logic and provides a type-safe interface.

```python
from arlogi import LoggingConfig, LoggerFactory

from arlogi import setup_logging

# Configure logging globally
setup_logging(
    level="INFO",
    module_levels={"app.db": "DEBUG"},
    json_file_name="logs/app.jsonl",
    show_time=True
)
```

> [!TIP]
> This pattern is highly recommended for production applications, especially when configuration is sourced from complex environment logic or external files.

---

### Per-Module Levels

```python
from arlogi import setup_logging

setup_logging(
    level="INFO",
    module_levels={
        "app.database": "DEBUG",      # Verbose database logging
        "app.network": "TRACE",       # Ultra-detailed network logs
        "app.security": "WARNING",    # Only security warnings and above
        "app.performance": "ERROR"    # Only performance errors
    }
)
```

### JSON File Logging

```python
from arlogi import setup_logging

# Console + JSON file
setup_logging(
    level="INFO",
    json_file_name="logs/app.jsonl"
)
```

**JSON Output Format:**

```json
{
  "timestamp": "2025-12-28T10:30:00.123456",
  "level": "INFO",
  "logger_name": "app.main",
  "message": "User logged in",
  "module": "main",
  "function": "login",
  "line_number": 42
}
```

### JSON-Only Output

```python
from arlogi import setup_logging

# JSON output only (no console)
setup_logging(
    level="INFO",
    json_file_only=True
)
```

### Syslog Integration

```python
from arlogi import setup_logging

# Add syslog to root logger
setup_logging(
    level="INFO",
    use_syslog=True,
    syslog_address="/dev/log"  # or ("localhost", 514)
)
```

### Complete Configuration

```python
from arlogi import setup_logging

setup_logging(
    level="INFO",
    module_levels={
        "app.db": "DEBUG",
        "app.api": "TRACE"
    },
    json_file_name="logs/app.jsonl",
    use_syslog=True,
    show_time=True,
    show_level=True,
    show_path=True
)
```

---

## Caller Attribution

### Understanding Depth Values

The `from_` parameter controls which function is shown in the log:

```python
from arlogi import get_logger

logger = get_logger(__name__)

def main():
    logger.info("Main entry point", caller_depth=0)  # Shows: main()
    process_data()

def process_data():
    logger.info("Processing", caller_depth=0)        # Shows: process_data()
    logger.info("Called from main", caller_depth=1)  # Shows: main()
    validate()

def validate():
    logger.info("Validating", caller_depth=0)        # Shows: validate()
    logger.info("From process", caller_depth=1)      # Shows: process_data()
    logger.info("From main", caller_depth=2)         # Shows: main()
```

### Cross-Module Attribution

```python
# file: app/utils.py
from arlogi import get_logger

logger = get_logger(__name__)

def fetch_user(user_id):
    logger.info("Fetching user", caller_depth=1)  # Shows caller
    # ... fetch logic
    return user

# file: app/main.py
from arlogi import get_logger
from app.utils import fetch_user

logger = get_logger(__name__)

def handle_request(user_id):
    logger.info("Request received", caller_depth=0)
    user = fetch_user(user_id)  # utils.py shows: handle_request()
    logger.info("Request complete", caller_depth=0)
```

### Best Practices

| Use Case                | Recommended `caller_depth`        |
| ----------------------- | --------------------------------- |
| Library/Utility code    | `caller_depth=1` (show caller)           |
| Application code        | `caller_depth=0` (show current function) |
| Debugging complex flows | `caller_depth=2+` (show deeper context)  |

---

## Output Handlers

### Console Handler

```python
from arlogi import get_logger
from arlogi.handlers import ColoredConsoleHandler

logger = get_logger(__name__)

# Custom colors
handler = ColoredConsoleHandler(
    show_time=True,
    show_level=True,
    show_path=True,
    level_styles={
        "info": "blue",
        "warning": "yellow",
        "error": "bold red"
    }
)
```

**Available Color Options:**

- `grey37`, `grey50`, `grey75`
- `blue`, `cyan`, `green`, `yellow`, `red`
- `bold blue`, `bold red`, etc.

### JSON Logger

```python
from arlogi import get_json_logger

# JSON to file
audit_logger = get_json_logger("audit", "logs/audit.jsonl")
audit_logger.info("User action", extra={"user_id": 123})

# JSON to stderr
json_logger = get_json_logger()
json_logger.info("Structured log", extra={"key": "value"})
```

### Syslog Logger

```python
from arlogi import get_syslog_logger

# Dedicated syslog logger
security_logger = get_syslog_logger("security")
security_logger.warning("Brute force attempt", extra={"ip": "192.168.1.1"})
```

---

## Common Patterns

### Application Startup

```python
from arlogi import setup_logging, get_logger

def main():
    # 1. Configure logging first
    setup_logging(
        level="INFO",
        module_levels={
            "app.database": "DEBUG",
            "app.network": "TRACE"
        },
        json_file_name="logs/app.jsonl"
    )

    logger = get_logger("app.main")
    logger.info("Application starting up")

    # Initialize components
    # init_database()
    # init_api_server()

    logger.info("Application ready")

if __name__ == "__main__":
    main()
```

### Request/Response Logging

```python
from arlogi import get_logger
import time

logger = get_logger("app.api")

def handle_request(request):
    request_id = generate_id()
    start_time = time.time()

    logger.info(
        "Request received",
        caller_depth=1,
        request_id=request_id,
        method=request.method,
        path=request.path
    )

    try:
        result = process_request(request)
        duration = (time.time() - start_time) * 1000

        logger.info(
            "Request completed",
            caller_depth=1,
            request_id=request_id,
            status_code=200,
            duration_ms=round(duration, 2)
        )
        return result

    except Exception as e:
        duration = (time.time() - start_time) * 1000

        logger.exception(
            "Request failed",
            caller_depth=1,
            request_id=request_id,
            error=str(e),
            duration_ms=round(duration, 2)
        )
        raise
```

### Database Operation Logging

```python
from arlogi import get_logger
import time

logger = get_logger("app.database")

def execute_query(query, params=None):
    start_time = time.time()

    logger.trace(
        "Executing query",
        caller_depth=1,
        query=query,
        params=params
    )

    try:
        result = db.execute(query, params)
        duration = (time.time() - start_time) * 1000

        logger.debug(
            "Query executed successfully",
            caller_depth=1,
            query=truncate(query, 100),
            duration_ms=round(duration, 2),
            rows_affected=result.rowcount
        )

        return result

    except Exception as e:
        duration = (time.time() - start_time) * 1000

        logger.error(
            "Query execution failed",
            caller_depth=1,
            query=query,
            duration_ms=round(duration, 2),
            error=str(e)
        )
        raise
```

### Background Task Logging

```python
from arlogi import get_logger
import asyncio

logger = get_logger("app.tasks")

async def process_task(task_id, data):
    logger.info(
        "Task started",
        caller_depth=1,
        task_id=task_id,
        data_size=len(data)
    )

    try:
        # Process the task
        result = await async_process(data)

        logger.info(
            "Task completed",
            caller_depth=1,
            task_id=task_id,
            result_size=len(result)
        )
        return result

    except Exception as e:
        logger.exception(
            "Task failed",
            caller_depth=1,
            task_id=task_id,
            error=str(e)
        )
        raise
```

---

## Troubleshooting

### Issue: Logs Not Appearing

**Symptoms:** No log output in console

**Solutions:**

1. Check configuration is applied correctly

```python
from arlogi import setup_logging
setup_logging(level="DEBUG")  # Show all logs
```

2. Verify logger name matches module levels

```python
# If module_levels={"app.db": "DEBUG"}
logger = get_logger("app.db")  # Must match exactly
```

3. Check test mode detection

```python
from arlogi import is_test_mode
print(f"Test mode: {is_test_mode()}")
```

### Issue: Duplicate Logs

**Symptoms:** Same message appears multiple times

**Solutions:**

1. Check for multiple configuration calls

```python
# Only apply configuration once at startup
setup_logging(level="INFO")
```

2. Check logger propagation

```python
logger = get_logger("my_module")
logger.propagate = False  # Disable if needed
```

### Issue: Caller Attribution Shows Wrong Function

**Symptoms:** Attribution shows incorrect function name

**Solutions:**

1. Adjust the `from_` depth

```python
logger.info("Message", caller_depth=0)  # Current function
logger.info("Message", caller_depth=1)  # Caller
logger.info("Message", caller_depth=2)  # Caller's caller
```

2. Check for wrapper functions

```python
# If using decorators
@log_decorator
def my_function():
    pass

# Use caller_depth=2 to skip the decorator
```

### Issue: Rich Colors Not Working

**Symptoms:** Console output has no colors

**Solutions:**

1. Install rich dependency

```bash
pip install rich
```

2. Check terminal supports colors

```python
from rich.console import Console
console = Console()
console.print("[bold red]Test colors[/bold red]")
```

### Issue: JSON File Not Created

**Symptoms:** JSON log file doesn't exist

**Solutions:**

1. Check directory permissions

```bash
mkdir -p logs
chmod 755 logs
```

2. Use absolute path

```python
setup_logging(json_file_name="/var/log/myapp/app.jsonl")
```

### Issue: Syslog Not Working

**Symptoms:** Syslog messages not appearing

**Solutions:**

1. Verify syslog address

```python
# For Unix socket
setup_logging(syslog_address="/dev/log", use_syslog=True)

# For network syslog
setup_logging(syslog_address=("localhost", 514), use_syslog=True)
```

2. Check syslog is running

```bash
# Linux
systemctl status rsyslog

# macOS
log show --predicate 'eventMessage contains "test"'
```

---

## Advanced Usage

### Conditional Logging

```python
from arlogi import get_logger

logger = get_logger(__name__)

# Only log if enabled (avoid string formatting overhead)
if logger.isEnabledFor(logging.DEBUG):
    logger.debug("Expensive debug info: %s", expensive_operation())
```

### Context Managers

```python
from contextlib import contextmanager
from arlogi import get_logger

logger = get_logger(__name__)

@contextmanager
def log_context(operation_name):
    logger.info("Starting: %s", operation_name, caller_depth=1)
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(
            "Completed: %s",
            operation_name,
            caller_depth=1,
            duration_ms=round(duration * 1000, 2)
        )

# Usage
with log_context("database_migration"):
    run_migration()
```

### Lazy Log Evaluation

```python
from arlogi import get_logger

logger = get_logger(__name__)

# Use lambda for expensive operations
logger.debug(lambda: expensive_debug_info())
```

---

## Best Practices

### DO

- Use descriptive log messages
- Include context (request IDs, user IDs, etc.)
- Use appropriate log levels
- Log exceptions with `logger.exception()`
- Use `caller_depth=1` in library/utility code

### DON'T

- Log sensitive data (passwords, tokens, PII)
- Use `print()` statements
- Log at inappropriate levels (ERROR for expected conditions)
- Create too many loggers (use module hierarchy)
- Include large objects in log messages

---

## Performance Tips

1. **Use lazy evaluation for expensive operations**

   ```python
   logger.debug(lambda: expensive_debug_info())
   ```

2. **Check log level before complex operations**

   ```python
   if logger.isEnabledFor(logging.DEBUG):
       logger.debug("Complex info: %s", complex_operation())
   ```

3. **Use structured logging for parsing**

   ```python
   logger.info("Event", extra={"structured": "data"})
   ```

4. **Avoid excessive string formatting**

   ```python
   # Good
   logger.info("User %s logged in", user.name)

   # Avoid
   logger.info(f"User {user.name} logged in")  # Formatting happens even if log is disabled
   ```

---

## Getting Help

- **Documentation**: [Documentation Index](index.md)
- **Issues**: [GitHub Issues](https://github.com/your-org/arlogi/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/arlogi/discussions)

---

## License

MIT License - see LICENSE file for details.

---

## FILE: docs/CONFIGURATION_GUIDE.md

# Configuration Guide

Complete guide to configuring arlogi logging for your applications, including global setup, per-module configuration, and advanced handler configuration.

## Quick Configuration

### Basic Setup

Configure `arlogi` using the `LoggingConfig` pattern. This approach clearly separates configuration data from initialization logic and provides a type-safe interface.

```python
from arlogi import setup_logging, get_logger

# 1. Setup logging
setup_logging(
    level="INFO",
    module_levels={"app.db": "DEBUG"},
    json_file_name="logs/app.jsonl"
)

# 2. Use loggers
logger = get_logger("my_app")
logger.info("Application started using setup_logging")
```

### Complete Production Setup

```python
from arlogi import setup_logging, get_logger

setup_logging(
    level="INFO",
    module_levels={
        "app.network": "TRACE",
        "app.database": "DEBUG",
        "app.security": "WARNING"
    },
    json_file_name="logs/app.jsonl",
    json_file_only=False,
    use_syslog=True,
    show_time=False,
    show_level=True,
    show_path=True
)

logger = get_logger("app.main")
logger.info("Production logging configured")
```

## Configuration Reference

### `LoggingConfig` Attributes

| Parameter                | Type                                           | Default      | Description                           |
| ------------------------ | ---------------------------------------------- | ------------ | ------------------------------------- |
| `level`                  | `int \| str`                                   | `"INFO"`     | Global log level for all modules      |
| `module_levels`          | `dict[str, str \| int] \| None`                | `None`       | Per-module log level overrides        |
| `json_file_name`         | `str \| None`                                  | `None`       | JSON log file path                    |
| `json_file_only`         | `bool`                                         | `False`      | Output only to JSON file (no console) |
| `use_syslog`             | `bool`                                         | `False`      | Enable syslog output                  |
| `syslog_address`         | `str \| tuple[str, int]`                       | `"/dev/log"` | Syslog server address                 |
| `rotate_schedule`        | `"hour" \| "day" \| "week" \| "month" \| None` | `None`       | File rotation schedule                |
| `rotate_retention_count` | `int \| None`                                  | `None`       | Number of rotated log files to retain |
| `show_time`              | `bool`                                         | `False`      | Show timestamps in console output     |
| `show_level`             | `bool`                                         | `True`       | Show log levels in console output     |
| `show_path`              | `bool`                                         | `True`       | Show file paths in console output     |

### Log Levels

```python
import logging
from arlogi import TRACE

# Available levels (from lowest to highest)
TRACE     # 5  - Custom ultra-detailed debugging
logging.DEBUG    # 10 - Standard debugging
logging.INFO     # 20 - General information
logging.WARNING  # 30 - Warnings
logging.ERROR    # 40 - Errors
logging.CRITICAL # 50 - Critical failures

# Can use string names in LoggingConfig
config = LoggingConfig(level="INFO")     # Same as logging.INFO
config = LoggingConfig(level="DEBUG")    # Same as logging.DEBUG
config = LoggingConfig(level=TRACE)      # Custom level
```

## Per-Module Configuration

### Module-Level Overrides

```python
from arlogi import LoggingConfig, LoggerFactory

config = LoggingConfig(
setup_logging(
    level="INFO",  # Global level
    module_levels={
        # Ultra-detailed logging for network operations
        "app.network": "TRACE",

        # Detailed logging for database operations
        "app.database": "DEBUG",

        # Quiet security logging (warnings only)
        "app.security": "WARNING"
    }
)
```

### Module Hierarchy Matching

```python
from arlogi import setup_logging

setup_logging(
    level="INFO",
    module_levels={
        # Affects: app.network.http, app.network.tcp, app.network.udp
        "app.network": "TRACE",

        # Affects: app.database.mysql, app.database.postgresql
        "app.database": "DEBUG",

        # Affects: app.cache.redis, app.cache.memory
        "app.cache": "INFO",

        # Specific module override
        "app.network.http.client": "DEBUG"
    }
)

# Examples:
# get_logger("app.network.http") -> TRACE level
# get_logger("app.network.tcp") -> TRACE level
# get_logger("app.database.mysql") -> DEBUG level
# get_logger("app.network.http.client") -> DEBUG level (specific override)
# get_logger("app.other") -> INFO level (global)
```

## Handler Configuration

### Console Handler Configuration

```python
from arlogi import setup_logging

# Basic console configuration
setup_logging(
    level="INFO",
    show_time=True,
    show_level=True,
    show_path=True
)

# Disable console output (JSON file only)
setup_logging(
    level="INFO",
    json_file_name="logs/app.jsonl",
    json_file_only=True
)
```

### JSON File Configuration

```python
from arlogi import setup_logging

# Basic JSON file logging
setup_logging(json_file_name="logs/app.jsonl")

# JSON-only logging
setup_logging(
    level="INFO",
    json_file_name="logs/app.jsonl",
    json_file_only=True
)
```

#### JSON File Structure

```json
{
  "timestamp": "2025-12-20T22:45:30.123456Z",
  "level": "INFO",
  "name": "app.main",
  "message": "User logged in successfully",
  "module": "main",
  "function": "handle_login",
  "line": 42,
  "caller": "auth.authenticate",
  "user_id": 12345,
  "session_id": "sess_abc123"
}
```

#### Custom JSON Handlers

```python
from arlogi import get_logger, get_json_logger
from arlogi.handlers import JSONFileHandler

# Default JSON logger
json_logger = get_json_logger("audit", "logs/audit.jsonl")

# Custom JSON handler with specific configuration
handler = JSONFileHandler(
    filename="logs/custom.jsonl",
    mode="a",           # Append mode
    encoding="utf-8",   # File encoding
    delay=False         # Delay file creation
)

import logging
custom_logger = get_logger("custom")
custom_logger.addHandler(handler)
custom_logger.setLevel(logging.INFO)

custom_logger.info("Custom JSON logging", custom_field="value")
```

### Syslog Configuration (Modern)

```python
from arlogi import setup_logging

# Local syslog
setup_logging(
    level="INFO",
    use_syslog=True,
    syslog_address="/dev/log"  # Default
)

# Remote syslog server
setup_logging(
    level="INFO",
    use_syslog=True,
    syslog_address=("syslog.example.com", 514)
)

# Syslog-only logger
from arlogi import get_syslog_logger
syslog_logger = get_syslog_logger("security")
syslog_logger.error("Security event detected")
```

#### Syslog Handler Details

```python
from arlogi.handlers import ArlogiSyslogHandler

# Local Unix domain socket
handler = ArlogiSyslogHandler(address="/dev/log")

# Remote UDP syslog
handler = ArlogiSyslogHandler(
    address=("logs.example.com", 514),
    facility="user",
    socktype="UDP"
)

# Remote TCP syslog
handler = ArlogiSyslogHandler(
    address=("logs.example.com", 514),
    facility="daemon",
    socktype="TCP"
)

# Custom facility
import syslog
handler = ArlogiSyslogHandler(
    address="/dev/log",
    facility=syslog.LOG_LOCAL0
)
```

## Application Structure Examples

### Microservice Configuration

```python
# config/logging.py
from arlogi import setup_logging

def setup_service_logging(service_name, environment="production"):
    """Configure logging for microservice"""

    if environment == "development":
        # Development: verbose console logging
        setup_logging(
            level="DEBUG",
            show_time=True,
            show_level=True,
            show_path=True
        )
    elif environment == "testing":
        # Testing: JSON-only for automated analysis
        setup_logging(
            level="INFO",
            json_file_name=f"logs/{service_name}.jsonl",
            json_file_only=True
        )
    else:
        # Production: console + JSON + syslog
        setup_logging(
            level="INFO",
            module_levels={
                f"{service_name}.network": "DEBUG",
                f"{service_name}.database": "DEBUG"
            },
            json_file_name=f"logs/{service_name}.jsonl",
            use_syslog=True,
            show_time=False,
            show_level=True,
            show_path=True
        )

# main.py
from config.logging import setup_service_logging
from arlogi import get_logger

setup_service_logging("user-service", environment="production")

logger = get_logger("user-service.main")
logger.info("User service started")
```

### Web Application Configuration

```python
# app/config.py
from arlogi import setup_logging

class LoggingSetup:
    @staticmethod
    def configure(app_name, environment="development"):
        """Configure logging for web application"""

        module_levels = {
            f"{app_name}.network": "DEBUG",
            f"{app_name}.database": "DEBUG",
            f"{app_name}.auth": "INFO",
            f"{app_name}.api": "INFO"
        }

        if environment == "development":
            setup_logging(
                level="DEBUG",
                show_time=True,
                show_path=True,
                module_levels=module_levels
            )

        elif environment == "staging":
            setup_logging(
                level="INFO",
                json_file_name=f"logs/{app_name}-staging.jsonl",
                use_syslog=True,
                syslog_address=("staging-logs.company.com", 514),
                module_levels=module_levels
            )

        elif environment == "production":
            setup_logging(
                level="WARNING",  # Less verbose in production
                module_levels={
                    f"{app_name}.auth": "ERROR",      # Only auth errors
                    f"{app_name}.api": "WARNING",     # API warnings
                    f"{app_name}.business": "INFO",   # Business events
                    **module_levels
                },
                json_file_name=f"logs/{app_name}.jsonl",
                use_syslog=True,
                syslog_address=("logs.company.com", 514)
            )

# app.py
from app.config import LoggingSetup
from arlogi import get_logger

LoggingSetup.configure("myapp", environment="production")

app_logger = get_logger("myapp.app")
app_logger.info("Web application started")
```

### CLI Application Configuration

```python
# cli/config.py
import os
from arlogi import setup_logging

def setup_cli_logging(verbosity=0, log_file=None):
    """Configure logging for CLI application"""

    if verbosity >= 2:
        # Very verbose: DEBUG level with console details
        setup_logging(
            level="DEBUG",
            show_time=True,
            show_level=True,
            show_path=True,
            json_file_name=log_file
        )
    elif verbosity >= 1:
        # Verbose: INFO level with basic console
        setup_logging(
            level="INFO",
            show_time=False,
            show_level=True,
            show_path=False,
            json_file_name=log_file
        )
    else:
        # Quiet: ERROR level only
        setup_logging(
            level="ERROR",
            json_file_name=log_file,
            json_file_only=not log_file
        )

# cli/main.py
import argparse
from cli.config import setup_cli_logging
from arlogi import get_logger

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("--log-file", help="Log to file")
    args = parser.parse_args()

    setup_cli_logging(args.verbose, args.log_file)

    logger = get_logger("cli.main")
    logger.info("CLI application started", verbose=args.verbose)

if __name__ == "__main__":
    main()
```

## Environment-Specific Configuration

### Development Environment

```python
from arlogi import setup_logging

def configure_development():
    """Development: maximum verbosity for debugging"""
    setup_logging(
        level="DEBUG",
        module_levels={"app.*": "TRACE"},
        show_time=True
    )
```

### Testing Environment

```python
from arlogi import setup_logging

def configure_testing():
    """Testing: structured logs for automated analysis"""
    setup_logging(
        level="INFO",
        json_file_name="logs/tests.jsonl",
        json_file_only=True
    )
```

### Staging Environment

```python
from arlogi import setup_logging

def configure_staging():
    """Staging: production-like with extra debugging"""
    setup_logging(
        level="INFO",
        module_levels={
            "app.auth": "DEBUG",      # Debug authentication
            "app.payments": "DEBUG",  # Debug payments
            "app.api": "INFO"
        },
        json_file_name="logs/staging.jsonl",
        use_syslog=True,
        syslog_address=("staging-logs.company.com", 514),
        show_time=False,
        show_level=True,
        show_path=False
    )
```

### Production Environment

```python
from arlogi import setup_logging

def configure_production():
    """Production: essential logging only"""
    setup_logging(
        level="WARNING",
        module_levels={
            "app.auth": "ERROR",
            "app.business": "INFO",
        },
        json_file_name="logs/production.jsonl",
        use_syslog=True
    )
```

## Dynamic Configuration

### Runtime Level Adjustment

```python
from arlogi import get_logger

# Get logger and adjust level at runtime
logger = get_logger("app.module")

# Check current level
print(f"Current level: {logger.level}")

# Adjust level dynamically
logger.setLevel("DEBUG")
logger.info("Level changed to DEBUG")

# Or use numeric levels
import logging
logger.setLevel(logging.INFO)
logger.info("Level changed to INFO")
```

### Configuration from Environment Variables

```python
import os
from arlogi import setup_logging

def configure_from_env():
    """Configure logging from environment variables"""

    # Basic configuration
    level = os.getenv("LOG_LEVEL", "INFO")
    json_file = os.getenv("LOG_FILE", None)
    syslog_enabled = os.getenv("LOG_SYSLOG", "false").lower() == "true"

    config_kwargs = {
        "level": level,
        "json_file_name": json_file,
        "use_syslog": syslog_enabled
    }

    # Console formatting from environment
    if os.getenv("LOG_SHOW_TIME", "false").lower() == "true":
        config_kwargs["show_time"] = True

    if os.getenv("LOG_SHOW_PATH", "true").lower() == "false":
        config_kwargs["show_path"] = False

    # Module levels from environment (comma-separated)
    module_levels_str = os.getenv("LOG_MODULE_LEVELS", "")
    if module_levels_str:
        module_levels = {}
        for item in module_levels_str.split(","):
            if ":" in item:
                module, level = item.strip().split(":", 1)
                module_levels[module.strip()] = level.strip()
        config_kwargs["module_levels"] = module_levels

    setup_logging(**config_kwargs)

# Usage
configure_from_env()
```

### Configuration File Support

```python
import json
import yaml
from pathlib import Path
from arlogi import setup_logging

def load_config_from_file(config_path):
    """Load logging configuration from JSON or YAML file"""

    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    if config_file.suffix.lower() == '.json':
        with open(config_file, 'r') as f:
            data = json.load(f)
    elif config_file.suffix.lower() in ['.yaml', '.yml']:
        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)
    else:
        raise ValueError(f"Unsupported config file format: {config_file.suffix}")

    setup_logging(**data)

# config.json example:
# {
#   "level": "INFO",
#   "module_levels": {
#     "app.database": "DEBUG",
#     "app.auth": "WARNING"
#   },
#   "json_file_name": "logs/app.jsonl",
#   "show_time": false,
#   "show_level": true,
#   "show_path": true
# }

# Usage
load_config_from_file("config/logging.json")
```

## Advanced Handler Configuration

### Multiple JSON Files

```python
from arlogi import get_logger
from arlogi.handlers import JSONFileHandler
import logging

# Create separate loggers for different purposes
app_logger = get_logger("app")
security_logger = get_logger("security")
audit_logger = get_logger("audit")

# Add separate JSON handlers
security_handler = JSONFileHandler("logs/security.jsonl")
audit_handler = JSONFileHandler("logs/audit.jsonl")

security_logger.addHandler(security_handler)
security_logger.setLevel(logging.WARNING)

audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)

# Usage
app_logger.info("Application message")          # Goes to console/default
security_logger.warning("Security event")      # Goes to security.jsonl
audit_logger.info("Audit trail entry")         # Goes to audit.jsonl
```

### Custom Formatters

```python
import logging
from arlogi.handlers import ColoredConsoleHandler

# Create custom console handler
handler = ColoredConsoleHandler(
    show_time=True,
    show_level=True,
    show_path=True,
    level_styles={
        "TRACE": "dim blue",
        "DEBUG": "dim cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold red"
    }
)

# Add to specific logger
logger = get_logger("custom")
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

logger.info("Custom formatted message")
```

### Filtering Logs

```python
import logging

class BusinessEventFilter(logging.Filter):
    """Filter to only allow business event logs"""

    def filter(self, record):
        return hasattr(record, 'event_type')

# Create logger with filter
logger = get_logger("business")
business_filter = BusinessEventFilter()

# Add filter to all handlers
for handler in logger.handlers:
    handler.addFilter(business_filter)

# These will be logged
logger.info("User registered", event_type="user_signup")
logger.info("Order placed", event_type="order_created")

# These will be filtered out
logger.info("Debug message")
logger.debug("Technical details")
```

## Configuration Validation

### Validate Configuration

```python
from arlogi import setup_logging, get_logger
import logging

def validate_logging_config():
    """Validate and test logging configuration"""

    # Configure logging
    setup_logging(level="DEBUG")

    try:
        # Test basic logging
        logger = get_logger("validation")
        logger.info("Configuration validation started")

        # Test all log levels
        logger.trace("TRACE level test")
        logger.debug("DEBUG level test")
        logger.info("INFO level test")
        logger.warning("WARNING level test")
        logger.error("ERROR level test")

        # Test caller attribution
        logger.info("Caller attribution test", caller_depth=0)

        # Test structured logging
        logger.info("Structured data test", key="value", number=42)

        # Test exception logging
        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("Exception test")

        print("✅ Logging configuration validated successfully")
        return True

    except Exception as e:
        print(f"❌ Logging configuration validation failed: {e}")
        return False

# Usage
if validate_logging_config():
    print("Ready to start application")
else:
    print("Fix logging configuration before starting")
```

## Performance Optimization

### High-Performance Configuration

```python
from arlogi import setup_logging

def configure_high_performance():
    """Optimize for high-performance applications"""

    setup_logging(
        level="WARNING",  # Minimal logging
        json_file_name="logs/perf.jsonl",
        show_time=False,  # Fast console output
        show_level=False,
        show_path=False
    )

def configure_balanced():
    """Balance between performance and observability"""

    setup_logging(
        level="INFO",
        module_levels={
            "app.critical": "DEBUG",  # Only critical modules verbose
        },
        json_file_name="logs/balanced.jsonl",
        show_time=False,  # Faster console
        show_level=True,
        show_path=False
    )
```

### Conditional Logging

```python
import os
from arlogi import setup_logging

DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"

if DEBUG_MODE:
    # Development configuration
    setup_logging(
        level="DEBUG",
        show_time=True,
        show_path=True
    )
else:
    # Production configuration
    setup_logging(
        level="INFO",
        json_file_name="logs/production.jsonl"
    )

# Usage in code
from arlogi import get_logger

logger = get_logger("performance")

def expensive_operation():
    if DEBUG_MODE:
        logger.debug("Starting expensive operation", caller_depth=1,
                    debug_data=get_debug_info())

    # Expensive operation here
    result = perform_calculation()

    if DEBUG_MODE:
        logger.debug("Expensive operation completed", caller_depth=1,
                    result=result)

    return result
```

This comprehensive configuration guide covers all aspects of setting up arlogi logging for different application types and environments.

---

## FILE: docs/CALLER_ATTRIBUTION_EXAMPLES.md

# Caller Attribution Examples

Comprehensive examples demonstrating arlogi's caller attribution feature using the `caller_depth` parameter.

## Modern Setup

Before using caller attribution, ensure arlogi is configured using the `LoggingConfig` pattern:

```python
from arlogi import setup_logging, get_logger

# Configure arlogi
setup_logging(level="INFO")

# Get logger
logger = get_logger("example")
```

---

## Basic Caller Attribution

### Using `caller_depth=0` (Current Function)

Shows the function where the log call is made:

```python
from arlogi import get_logger

logger = get_logger("example")

def process_data(data):
    # Shows [process_data()] - the current function
    logger.info("Processing data started", caller_depth=0)

    result = data * 2

    # Shows [process_data()] - still the current function
    logger.info("Processing completed", caller_depth=0, result=result)

    return result

process_data(42)
```

**Output:**

```text
INFO    [process_data()]                          Processing data started
INFO    [process_data()]                          Processing completed, result=84
```

### Using `caller_depth=1` (Immediate Caller)

Shows the function that called the current function:

```python
from arlogi import get_logger

logger = get_logger("example")

def helper_function():
    # Shows [from main_function()] - the function that called helper_function
    logger.info("Helper operation completed", caller_depth=1)
    logger.info("Helper operation details", caller_depth=1, operation_type="compute")

def main_function():
    logger.info("Main started", caller_depth=0)

    # This call will show main_function as the caller
    helper_function()

    logger.info("Main completed", caller_depth=0)

main_function()
```

**Output:**

```text
INFO    [main_function()]                        Main started
INFO    [from main_function()]                   Helper operation completed
INFO    [from main_function()]                   Helper operation details, operation_type=compute
INFO    [main_function()]                        Main completed
```

### Using `caller_depth=2` (Caller's Caller)

Shows the function that called the caller:

```python
from arlogi import get_logger

logger = get_logger("example")

def deep_function():
    # Shows [from top_function()] - two levels up the call stack
    logger.info("Deep operation", caller_depth=2)
    logger.info("Deep details", caller_depth=2, depth="deep")

def middle_function():
    logger.info("Middle function", caller_depth=0)
    deep_function()

def top_function():
    logger.info("Top function", caller_depth=0)
    middle_function()

top_function()
```

**Output:**

```text
INFO    [top_function()]                        Top function
INFO    [middle_function()]                      Middle function
INFO    [from top_function()]                   Deep operation
INFO    [from top_function()]                   Deep details, depth=deep
```

## Cross-Module Attribution

### Same Module Attribution

```python
# file: app.py
from arlogi import get_logger

logger = get_logger("app")

def helper_function():
    # Shows [from main_function()] - same module, relative path
    logger.info("Helper completed", caller_depth=1)

def main_function():
    logger.info("Main started", caller_depth=0)
    helper_function()
    logger.info("Main completed", caller_depth=0)

main_function()
```

**Output:**

```text
INFO    [main_function()]                        Main started
INFO    [from main_function()]                   Helper completed
INFO    [main_function()]                        Main completed
```

### Cross-Module Attribution

```python
# file: utils/helpers.py
from arlogi import get_logger

logger = get_logger("utils.helpers")

def process_data(data):
    # Shows [from app.main_function()] - different module, full path
    logger.info("Processing data", caller_depth=1, data_id=data.get("id"))
    return {"status": "processed"}

# file: app/main.py
from utils.helpers import process_data
from arlogi import get_logger

logger = get_logger("app.main")

def main_function():
    logger.info("Starting main", caller_depth=0)
    result = process_data({"id": 123, "content": "test"})
    logger.info("Main completed", caller_depth=0, result=result)

main_function()
```

**Output:**

```text
INFO    [app.main_function()]                    Starting main
INFO    [from app.main_function()]               Processing data, data_id=123
INFO    [app.main_function()]                    Main completed, result={'status': 'processed'}
```

## Real-World Application Examples

### Web API Handler

```python
from arlogi import get_logger

logger = get_logger("api.handlers")

def handle_request(request):
    request_id = generate_request_id()

    logger.info(
        "Request received",
        caller_depth=1,  # Shows the API endpoint that called this handler
        request_id=request_id,
        method=request.method,
        path=request.path
    )

    try:
        result = process_business_logic(request)

        logger.info(
            "Request processed successfully",
            caller_depth=1,  # Still shows the API endpoint
            request_id=request_id,
            status_code=200
        )

        return result

    except Exception as e:
        logger.exception(
            "Request processing failed",
            caller_depth=1,  # Shows the API endpoint
            request_id=request_id,
            error_type=type(e).__name__
        )
        raise

def user_endpoint(request):
    # The handler call above will show [from user_endpoint()]
    return handle_request(request)

def product_endpoint(request):
    # The handler call above will show [from product_endpoint()]
    return handle_request(request)
```

### Database Operations

```python
from arlogi import get_logger

logger = get_logger("database.operations")

def execute_query(query, params=None):
    start_time = time.time()

    # Show the business function that initiated the query
    logger.trace(
        "Executing query",
        caller_depth=1,
        query=query,
        params=params
    )

    try:
        cursor = db.cursor()
        cursor.execute(query, params or [])
        result = cursor.fetchall()
        duration = (time.time() - start_time) * 1000

        # Show the business function for the result
        logger.debug(
            "Query completed",
            caller_depth=1,
            query=query,
            duration_ms=round(duration, 2),
            rows_affected=len(result)
        )

        return result

    except Exception as e:
        duration = (time.time() - start_time) * 1000

        # Show the business function for the error
        logger.error(
            "Query failed",
            caller_depth=1,
            query=query,
            duration_ms=round(duration, 2),
            error=str(e)
        )
        raise

def get_user_profile(user_id):
    logger.info("Fetching user profile", caller_depth=1, user_id=user_id)

    query = "SELECT * FROM users WHERE id = %s"
    params = (user_id,)

    # execute_query will log this as [from get_user_profile()]
    return execute_query(query, params)

def authenticate_user(username, password):
    logger.info("Authenticating user", caller_depth=1, username=username)

    query = "SELECT * FROM users WHERE username = %s AND password_hash = %s"
    params = (username, hash_password(password))

    # execute_query will log this as [from authenticate_user()]
    return execute_query(query, params)
```

### Background Job Processing

```python
from arlogi import get_logger

logger = get_logger("jobs.processor")

def process_job(job_data):
    job_id = job_data.get("id")
    job_type = job_data.get("type")

    # Show the job queue that dispatched this job
    logger.info(
        "Job processing started",
        caller_depth=1,
        job_id=job_id,
        job_type=job_type
    )

    try:
        if job_type == "email":
            result = send_email_job(job_data)
        elif job_type == "report":
            result = generate_report_job(job_data)
        elif job_type == "cleanup":
            result = cleanup_job(job_data)
        else:
            raise ValueError(f"Unknown job type: {job_type}")

        # Show the job queue for completion
        logger.info(
            "Job processing completed",
            caller_depth=1,
            job_id=job_id,
            result_status=result.get("status")
        )

        return result

    except Exception as e:
        # Show the job queue for failure
        logger.exception(
            "Job processing failed",
            caller_depth=1,
            job_id=job_id,
            error_type=type(e).__name__
        )
        raise

def email_job_dispatcher():
    # process_job will show [from email_job_dispatcher()]
    process_job({
        "id": "job-123",
        "type": "email",
        "to": "user@example.com",
        "subject": "Welcome"
    })

def report_job_dispatcher():
    # process_job will show [from report_job_dispatcher()]
    process_job({
        "id": "job-456",
        "type": "report",
        "format": "pdf",
        "date_range": "2025-01-01:2025-12-31"
    })
```

### Class Method Attribution

```python
from arlogi import get_logger

logger = get_logger("services.user")

class UserService:
    def __init__(self):
        logger.info("UserService instance created", caller_depth=0)

    def create_user(self, user_data):
        logger.info("Creating user", caller_depth=1, email=user_data.get("email"))

        user_id = self._generate_user_id()
        self._save_user(user_id, user_data)
        self._send_welcome_email(user_data)

        logger.info("User created successfully", caller_depth=1, user_id=user_id)
        return user_id

    def _generate_user_id(self):
        # Shows [from create_user()] - parent method
        logger.trace("Generating user ID", caller_depth=1)
        return f"user_{uuid.uuid4().hex[:8]}"

    def _save_user(self, user_id, user_data):
        # Shows [from create_user()] - grandparent method
        logger.debug("Saving user to database", caller_depth=2, user_id=user_id)
        # Database save logic here

    def _send_welcome_email(self, user_data):
        # Shows [from create_user()] - grandparent method
        logger.info("Sending welcome email", caller_depth=2, email=user_data.get("email"))
        # Email sending logic here

# Usage
def application_logic():
    logger.info("Application started", caller_depth=0)

    service = UserService()

    # create_user will show [from application_logic()]
    user_id = service.create_user({
        "email": "newuser@example.com",
        "name": "New User"
    })

    logger.info("Application completed", caller_depth=0, user_id=user_id)
```

### Error Handling and Exception Tracking

```python
from arlogi import get_logger

logger = get_logger("error.tracking")

def risky_operation(data):
    logger.info("Starting risky operation", caller_depth=1, data_id=data.get("id"))

    try:
        result = process_data(data)
        logger.info("Operation successful", caller_depth=1, result=result)
        return result

    except ValueError as e:
        # Show the caller function for the error
        logger.warning(
            "Invalid data format",
            caller_depth=1,
            error=str(e),
            data_type=type(data).__name__
        )
        raise

    except ConnectionError as e:
        # Show the caller function for connection error
        logger.error(
            "Network connection failed",
            caller_depth=1,
            error=str(e),
            retry_possible=True
        )
        raise

    except Exception as e:
        # Show the caller function for unexpected errors
        logger.exception(
            "Unexpected error in operation",
            caller_depth=1,
            error_type=type(e).__name__
        )
        raise

def business_process():
    try:
        # risky_operation will show [from business_process()]
        risky_operation({"id": 123, "value": "test"})
    except Exception:
        # business_process will be shown as the caller
        logger.error("Business process failed", caller_depth=0)
        raise

def user_interface():
    try:
        # risky_operation will show [from user_interface()]
        risky_operation({"id": 456, "invalid": "data"})
    except Exception:
        # user_interface will be shown as the caller
        logger.error("UI operation failed", caller_depth=0)
        raise
```

## Performance Considerations

### Efficient Caller Attribution

```python
from arlogi import get_logger

logger = get_logger("performance.example")

def high_frequency_function():
    # Standard logging without caller attribution (fast)
    for i in range(1000):
        logger.debug("Processing item %d", i)

    # Caller attribution only when needed
    logger.info("Batch processing started", caller_depth=1, total=1000)

    for i in range(1000):
        # More expensive logging with caller attribution
        if i % 100 == 0:  # Log every 100th item
            logger.debug("Progress update", caller_depth=1, progress=i)

def optimized_error_tracking():
    try:
        # Standard logging for normal operations
        logger.info("Normal operation")

        # Caller attribution only for debugging
        if DEBUG_MODE:
            logger.debug("Detailed debug info", caller_depth=1, complex_data=data)

    except Exception as e:
        # Always use caller attribution for errors
        logger.exception("Error occurred", caller_depth=1, error_type=type(e).__name__)
```

## Testing with Caller Attribution

### Unit Test Examples

```python
import pytest
from arlogi import get_logger

def test_function_call_attribution(caplog):
    logger = get_logger("test_module")

    def test_function():
        logger.info("Test message", caller_depth=1)

    with caplog.at_level("INFO"):
        test_function()

        # Check that the log contains caller attribution
        assert "from test_function_call_attribution" in caplog.text

def test_deep_call_attribution(caplog):
    logger = get_logger("test_module")

    def deep_function():
        logger.info("Deep message", caller_depth=2)

    def middle_function():
        deep_function()

    def top_function():
        middle_function()

    with caplog.at_level("INFO"):
        top_function()

        # Check that the log shows top_function as caller
        assert "from test_deep_call_attribution" in caplog.text
```

## Best Practices

### Recommended Patterns

```python
from arlogi import get_logger

logger = get_logger("my_module")

# ✅ GOOD: Use caller_depth=0 for function entry/exit
def my_function():
    logger.info("Function started", caller_depth=0)
    # Function logic
    logger.info("Function completed", caller_depth=0)

# ✅ GOOD: Use caller_depth=1 to show business context
def helper_function():
    logger.info("Helper operation", caller_depth=1, operation_type="compute")

# ✅ GOOD: Use caller attribution for errors
def risky_operation():
    try:
        # Operation logic
        pass
    except Exception as e:
        logger.exception("Operation failed", caller_depth=1, error=str(e))
        raise

# ❌ AVOID: Overusing deep caller attribution
def deep_function():
    # caller_depth=3+ is rarely useful and adds overhead
    logger.info("Deep operation", caller_depth=3)
```

### Recommended Caller Attribution Depth

- `caller_depth=0`: Function boundaries and state changes
- `caller_depth=1`: Business operations and user actions
- `caller_depth=2`: Rare cases for debugging complex call chains
- `caller_depth=3+`: Generally avoid unless specific debugging needs

These examples demonstrate the power and flexibility of arlogi's caller attribution feature for creating maintainable, debuggable applications.

---

## FILE: docs/DEVELOPER_GUIDE.md

# Arlogi Developer Guide

This guide is for contributors and maintainers of the arlogi library.

---

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Release Process](#release-process)
- [Contributing](#contributing)

---

## Development Setup

### Prerequisites

- Python 3.13 or higher (required by project configuration)
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Clone Repository

```bash
git clone https://github.com/your-org/arlogi.git
cd arlogi
```

### Install Dependencies

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync
```

### Development Commands

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/arlogi --cov-report=html

# Run linter
uv run ruff check src/arlogi tests

# Format code
uv run ruff format src/arlogi tests

# Check with radon (complexity analysis)
uv run radon cc src/arlogi -a -nb
```

---

## Project Structure

```text
arlogi/
├── src/
│   └── arlogi/
│       ├── __init__.py              # Public API exports
│       ├── config.py                # LoggingConfig dataclass
│       ├── config_builder.py        # Configuration builder utilities
│       ├── factory.py               # LoggerFactory, TraceLogger
│       ├── handler_factory.py       # HandlerFactory
│       ├── handlers.py              # Handler implementations
│       ├── levels.py                # TRACE level registration
│       └── types.py                 # LoggerProtocol
├── tests/
│   ├── test_core.py                 # Core functionality tests
│   ├── test_features.py             # Feature tests
│   ├── test_resource_management.py  # Resource cleanup tests
│   ├── test_thread_safety.py        # Thread safety tests
│   └── example/
│       └── example.py               # Example usage
├── docs/
│   ├── API_REFERENCE.md             # Complete API documentation
│   ├── ARCHITECTURE.md              # Architecture diagrams
│   ├── USER_GUIDE.md                # User guide
│   ├── CONFIGURATION_GUIDE.md       # Configuration reference
│   ├── CALLER_ATTRIBUTION_EXAMPLES.md # Caller attribution examples
│   ├── index.md                     # Documentation index
│   └── DEVELOPER_GUIDE.md           # This file
├── pyproject.toml                   # Project configuration
├── uv.lock                          # Dependency lock file
├── .ruff.toml                       # Ruff linter configuration
└── README.md                        # Project README
```

### Module Responsibilities

| Module               | Responsibility                     | Complexity Target |
| -------------------- | ---------------------------------- | ----------------- |
| `config.py`          | Configuration validation & storage | < 5 per method    |
| `factory.py`         | Logger creation & orchestration    | < 5 per method    |
| `handler_factory.py` | Handler creation                   | < 3 per method    |
| `handlers.py`        | Output handlers                    | < 10 per method   |
| `levels.py`          | TRACE level registration           | N/A (simple)      |
| `types.py`           | Protocol definitions               | N/A (declarative) |

---

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_core.py

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=src/arlogi --cov-report=term-missing
```

### Coverage Requirements

| Module               | Target Coverage | Status |
| -------------------- | --------------- | ------ |
| `config.py`          | 80%             | 80%    |
| `factory.py`         | 80%             | 75%    |
| `handler_factory.py` | 70%             | 49%    |
| `handlers.py`        | 60%             | 36%    |
| `levels.py`          | 90%             | 85%    |

### Test Categories

#### Unit Tests

Test individual functions and methods in isolation.

```python
def test_logging_config_validation():
    """Test that invalid log levels raise ValueError."""
    with pytest.raises(ValueError):
        LoggingConfig(level="INVALID")

def test_direct_config_apply():
    """Test that direct LoggingConfig application works."""
    config = LoggingConfig(level="DEBUG")
    LoggerFactory._apply_configuration(config)
    assert logging.getLogger().level == logging.DEBUG
```

#### Integration Tests

Test interactions between components.

```python
def test_setup_with_json_file():
    """Test that configuration creates JSON file handler."""
    LoggerFactory.setup(json_file_name="logs/test.jsonl")
    root = logging.getLogger()
    assert any(isinstance(h, JSONFileHandler) for h in root.handlers)
```

#### Feature Tests

Test end-to-end functionality.

```python
def test_caller_attribution():
    """Test that caller attribution shows correct function."""
    logger = get_logger("test")
    logger.info("Test message", caller_depth=1)
    # Verify output contains parent function name
```

### Writing Tests

#### Test Structure

```python
import pytest
from arlogi import LoggingConfig, LoggerFactory, get_logger

class TestLoggerFactory:
    """Tests for LoggerFactory class."""

    def setup_method(self):
        """Reset logging state before each test."""
        # Clear existing handlers
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a valid logger."""
        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "test"

    @pytest.mark.parametrize("level", ["DEBUG", "INFO", "WARNING"])
    def test_logger_respects_level(self, level):
        """Test that logger respects configured level."""
        LoggerFactory.setup(level=level)
        logger = get_logger("test")
        assert logger.getEffectiveLevel() == getattr(logging, level)
```

#### Test Fixtures

```python
@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary log file path."""
    return tmp_path / "test.jsonl"

@pytest.fixture
def configured_logger(temp_log_file):
    """Create a logger configured for testing."""
    LoggerFactory.setup(
        level="DEBUG",
        json_file_name=str(temp_log_file)
    )
    return get_logger("test")
```

### Test Mode Detection

Tests should work correctly with arlogi's test mode detection:

```python
def test_test_mode_detection():
    """Verify is_test_mode() returns True during pytest."""
    from arlogi import is_test_mode
    assert is_test_mode() is True
```

---

## Code Quality

### Linting with Ruff

```bash
# Check for issues
uv run ruff check src/arlogi tests

# Auto-fix issues
uv run ruff check --fix src/arlogi tests

# Format code
uv run ruff format src/arlogi tests
```

### Ruff Configuration

Key rules from `.ruff.toml`:

| Rule | Description           | Severity |
| ---- | --------------------- | -------- |
| C901 | Complexity limit (10) | Error    |
| F401 | Unused imports        | Error    |
| F841 | Unused variables      | Error    |
| SIM  | Simplify code         | Warning  |

### Complexity Limits

| Metric                | Limit     | Enforcement        |
| --------------------- | --------- | ------------------ |
| Cyclomatic Complexity | 10        | Ruff C901          |
| Method Length         | 30 lines  | Code review        |
| Class Length          | 300 lines | Code review        |
| Module Length         | 500 lines | Consider splitting |

### Code Style Guidelines

#### Naming Conventions

```python
# Classes: PascalCase
class LoggingConfig:
    pass

# Functions/Variables: snake_case
def get_logger(name):
    pass

# Constants: UPPER_SNAKE_CASE
TRACE_LEVEL_NUM = 5

# Private methods: _leading_underscore
def _internal_method(self):
    pass
```

#### Docstring Format

```python
def complex_function(arg1, arg2):
    """Brief description of function.

    Longer description if needed.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Raises:
        ValueError: If arg1 is invalid

    Examples:
        >>> complex_function("a", "b")
        "result"
    """
    pass
```

#### Type Hints

```python
from typing import Any, List, Dict, Optional

# Always use type hints for public APIs
def process_data(
    data: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None
) -> List[str]:
    """Process data with options."""
    pass
```

### Pre-commit Hooks

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
set -e

echo "Running ruff check..."
uv run ruff check src/arlogi tests

echo "Running ruff format..."
uv run ruff format --check src/arlogi tests

echo "Running tests..."
uv run pytest tests/ -q

echo "All checks passed!"
```

Make executable:

```bash
chmod +x .git/hooks/pre-commit
```

---

## Release Process

### Version Management

Arlogi uses semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Release Checklist

1. **Update Version**

   ```bash
   # Update pyproject.toml
   version = "0.513.0"
   ```

2. **Update Changelog**

   ```markdown
   ## [0.513.0] - 2025-12-28

   ### Added

   - New feature X

   ### Changed

   - Improved Y

   ### Fixed

   - Bug Z
   ```

3. **Run Full Test Suite**

   ```bash
   uv run pytest --cov=src/arlogi
   ```

4. **Create Git Tag**

   ```bash
   git tag -a v0.513.0 -m "Release v0.513.0"
   git push origin v0.513.0
   ```

5. **Build Distribution**

   ```bash
   uv build
   ```

6. **Publish to PyPI**

   ```bash
   uv publish
   ```

### Release Notes Template

```markdown
# Release {version}

## Summary

{Brief description of release}

## What's New

- Feature 1
- Feature 2

## Breaking Changes

- Breaking change 1 (migration guide)

## Bug Fixes

- Bug fix 1
- Bug fix 2

## Upgrading

See [MIGRATION.md](docs/MIGRATION.md) for upgrade instructions.
```

---

## Contributing

### Contribution Workflow

1. **Fork Repository**

   ```bash
   # Fork on GitHub, then clone
   git clone https://github.com/YOUR_USERNAME/arlogi.git
   cd arlogi
   git remote add upstream https://github.com/original/arlogi.git
   ```

2. **Create Feature Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Write code
   - Add tests
   - Update documentation

4. **Run Quality Checks**

   ```bash
   uv run ruff check src/arlogi tests
   uv run pytest tests/
   ```

5. **Commit Changes**

   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

6. **Push and Create PR**

   ```bash
   git push origin feature/your-feature-name
   # Create PR on GitHub
   ```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```text
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks

**Examples:**

```text
feat(factory): add LoggingConfig support

feat(factory): add cleanup_json_logger and cleanup_syslog_logger

fix(handlers): resolve unused variable warning

docs(api): update handler examples
```

### Pull Request Guidelines

#### PR Title

```text
feat: add async handler support
```

#### PR Description Template

```markdown
## Summary

Brief description of changes.

## Changes

- Added async handler class
- Updated tests
- Updated documentation

## Testing

- Added unit tests for async handler
- Manual testing with asyncio application

## Checklist

- [ ] Tests pass
- [ ] No linting errors
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

### Code Review Criteria

PRs are reviewed against:

1. **Functionality**
   - Does it work as intended?
   - Are edge cases handled?

2. **Code Quality**
   - Is code readable?
   - Are names descriptive?
   - Is complexity acceptable?

3. **Testing**
   - Are tests comprehensive?
   - Is coverage adequate?

4. **Documentation**
   - Are docstrings complete?
   - Is user documentation updated?

5. **Backward Compatibility**
   - Are breaking changes documented?
   - Is migration path clear?

---

## Architecture Decisions

### Current Architecture

Arlogi follows SOLID principles:

- **S**: Each class has single responsibility
- **O**: HandlerFactory is extensible
- **L**: All handlers are substitutable
- **I**: LoggerProtocol is focused
- **D**: Depends on abstractions (Protocol)

### Decision Records

Significant architectural decisions should be documented:

```markdown
# ADR-001: Use Protocol for Logger Interface

## Status

Accepted

## Context

Need type-safe logger interface that doesn't require inheritance.

## Decision

Use `typing.Protocol` for `LoggerProtocol`.

## Consequences

- Pros: Type safety without inheritance
- Cons: Requires Python 3.8+
```

---

## Performance Guidelines

### Performance Targets

| Operation                   | Target | Notes                     |
| --------------------------- | ------ | ------------------------- |
| Log call (no attribution)   | < 1μs  | Standard logging overhead |
| Log call (with attribution) | < 5μs  | Stack frame inspection    |
| Handler emit                | < 10μs | I/O excluded              |

### Profiling

```python
import cProfile
import pstats

def profile_logging():
    pr = cProfile.Profile()
    pr.enable()

    # Logging code
    for _ in range(10000):
        logger.info("Test message")

    pr.disable()
    stats = pstats.Stats(pr)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
```

### Optimization Checklist

- [ ] Avoid expensive string formatting when disabled
- [ ] Use lazy evaluation for complex operations
- [ ] Minimize stack frame inspection depth
- [ ] Cache repeated operations
- [ ] Use efficient data structures

---

## Documentation

### Updating Documentation

1. **API Changes**: Update `API_REFERENCE.md`
2. **New Features**: Update `USER_GUIDE.md`
3. **Architecture Changes**: Update `ARCHITECTURE.md`
4. **Examples**: Update `tests/example/example.py`

### Docstring Standards

All public APIs must have docstrings:

```python
def public_function(arg1: str) -> bool:
    """Brief description.

    Extended description if needed.

    Args:
        arg1: Description

    Returns:
        Description of return

    Raises:
        ValueError: When arg1 is invalid

    Examples:
        >>> public_function("test")
        True
    """
    pass
```

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install dependencies
        run: uv sync
      - name: Run linting
        run: uv run ruff check src/arlogi tests
      - name: Run tests
        run: uv run pytest --cov=src/arlogi
```

---

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/your-org/arlogi/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/arlogi/discussions)
- **Email**: <maintainers@example.com>

---

## License

Contributions are licensed under the MIT License. See LICENSE for details.

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## FILE: docs/API_REFERENCE.md

# Arlogi API Reference

Complete API reference for the arlogi logging library v0.606.22.

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

### `LoggingConfig`

The primary way to configure `arlogi` is using `setup_logging(...)` or `LoggerFactory.setup()`, which construct and apply a `LoggingConfig` dataclass.

```python
from arlogi import setup_logging

# Apply configuration
setup_logging(
    level="INFO",
    module_levels={"app.db": "DEBUG"},
    json_file_name="logs/app.jsonl"
)
```

**Attributes:**

| Attribute        | Type                            | Default        | Description           |
| ---------------- | ------------------------------- | -------------- | --------------------- |
| `level`          | `int \| str`                    | `logging.INFO` | Global root log level |
| `module_levels`  | `Dict[str, str \| int] \| None` | `None`         | Per-module overrides  |
| `json_file_name` | `str \| None`                   | `None`         | JSON log file path    |
| `json_file_only` | `bool`                          | `False`        | Only JSON output      |
| `use_syslog`     | `bool`                          | `False`        | Enable syslog         |
| `syslog_address` | `str \| tuple[str, int]`        | `"/dev/log"`   | Syslog address        |
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

### `get_logger(name, level=None)`

Get a logger instance with caller attribution support.

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

### `get_json_logger(name, json_file_name=None)`

Get a logger that only outputs JSON, bypassing root handlers.

```python
from arlogi import get_json_logger

audit_logger = get_json_logger("audit", "logs/audit.jsonl")
audit_logger.info("User logged in", extra={"user_id": 123})
```

**Parameters:**

| Parameter        | Type          | Default  | Description        |
| ---------------- | ------------- | -------- | ------------------ |
| `name`           | `str`         | `"json"` | Logger name suffix |
| `json_file_name` | `str \| None` | `None`   | Optional file path |

**Returns:** `LoggerProtocol` - A JSON-only logger instance

---

### `get_syslog_logger(name, address="/dev/log")`

Get a logger that only outputs to Syslog.

```python
from arlogi import get_syslog_logger

syslog_logger = get_syslog_logger("security")
syslog_logger.warning("Unauthorized access attempt")
```

**Parameters:**

| Parameter | Type           | Default      | Description           |
| --------- | -------------- | ------------ | --------------------- |
| `name`    | `str`          | `"syslog"`   | Logger name suffix    |
| `address` | `str \| tuple` | `"/dev/log"` | Syslog server address |

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
logger.trace(msg, *args, caller_depth=0, **kwargs)
logger.debug(msg, *args, caller_depth=0, **kwargs)
logger.info(msg, *args, caller_depth=0, **kwargs)
logger.warning(msg, *args, caller_depth=0, **kwargs)
logger.error(msg, *args, caller_depth=0, **kwargs)
logger.critical(msg, *args, caller_depth=0, **kwargs)
logger.exception(msg, *args, caller_depth=0, **kwargs)
logger.log(level, msg, *args, caller_depth=0, **kwargs)
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

| Parameter      | Type                     | Default         | Description            |
| -------------- | ------------------------ | --------------- | ---------------------- |
| `show_time`    | `bool`                   | `False`         | Show timestamps        |
| `show_level`   | `bool`                   | `True`          | Show log levels        |
| `show_path`    | `bool`                   | `True`          | Show file paths        |
| `level_styles` | `Dict[str, str] \| None` | `None`          | Custom level colors    |
| `project_root` | `str \| None`            | `auto-detected` | Project root for paths |

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

### `JSONHandler`

Stream handler that outputs JSON to stderr.

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

File handler that outputs JSON to a file.

```python
from arlogi.handlers import JSONFileHandler

handler = JSONFileHandler(
    filename="logs/app.jsonl",
    mode="a",
    encoding="utf-8"
)
```

**Parameters:**

| Parameter  | Type          | Default    | Description        |
| ---------- | ------------- | ---------- | ------------------ |
| `filename` | `str`         | _required_ | Path to log file   |
| `mode`     | `str`         | `"a"`      | File open mode     |
| `encoding` | `str \| None` | `None`     | File encoding      |
| `delay`    | `bool`        | `False`    | Delay file opening |

**Note:** Parent directories are created automatically.

---

### `ArlogiSyslogHandler`

Syslog handler with automatic fallback support.

```python
from arlogi.handlers import ArlogiSyslogHandler

handler = ArlogiSyslogHandler(
    address="/dev/log",  # or ("localhost", 514)
    facility="user",
    socktype=None
)
```

**Parameters:**

| Parameter  | Type           | Default      | Description           |
| ---------- | -------------- | ------------ | --------------------- |
| `address`  | `str \| tuple` | `"/dev/log"` | Syslog server address |
| `facility` | `int \| str`   | `LOG_USER`   | Syslog facility       |
| `socktype` | `int \| None`  | `None`       | Socket type           |

**Fallback Behavior:**

1. Tries the specified address
2. If `/dev/log` fails, tries UDP on `localhost:514`
3. If all fail, silently continues (won't crash the app)

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

| Method                               | Description                      |
| ------------------------------------ | -------------------------------- |
| `setup(**kwargs)`                    | Configure logging (public entry) |
| `get_logger(name, level)`            | Get a logger                     |
| `get_json_logger(name, file)`        | Get JSON-only logger             |
| `get_syslog_logger(name, addr)`      | Get syslog-only logger           |
| `cleanup_json_logger(name)`          | Clean up JSON logger handlers    |
| `cleanup_syslog_logger(name)`        | Clean up syslog logger handlers  |
| `is_test_mode()`                     | Check if in test environment     |
| `get_global_logger()`                | Get global application logger    |

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

**Returns:** `bool` - True if pytest, unittest, or PYTEST_CURRENT_TEST is detected

---

#### `get_default_level()`

Get the default log level based on environment.

```python
from arlogi import get_default_level

level = get_default_level()  # DEBUG in tests, INFO otherwise
```

**Returns:** `int` - `logging.DEBUG` if in test mode, `logging.INFO` otherwise

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
    logger.debug("Step 1", caller_depth=0)  # Shows inner_function
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
- Syslog connection failures fall back automatically
- JSON file handler creates parent directories automatically
- Test mode detection prevents double logging in pytest

---

## Version History

| Version  | Changes                                                           |
| -------- | ----------------------------------------------------------------- |
| 0.606.22 | Current stable version: rotation, syslog, and resource cleanup    |
| 0.601.04 | Enhanced resource cleanup, improved test mode detection          |
| 0.601.00 | Added cleanup_json_logger, cleanup_syslog_logger                 |
| 0.512.28 | Added LoggingConfig, HandlerFactory, reduced complexity           |
| 0.512.20 | Initial caller attribution support                               |
| 0.512.0  | First stable release                                              |

---

## License

MIT License - see LICENSE file for details.
