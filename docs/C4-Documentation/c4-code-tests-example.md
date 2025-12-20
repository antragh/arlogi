# C4 Code Level: tests-example

## Overview

- **Name**: Tests Example Directory
- **Description**: Example implementation demonstrating `arlogi` library usage patterns
- **Location**: `/opt/Code/2026/_Libs/arlogi/tests/example`
- **Language**: Python 3.8+
- **Purpose**: Demonstrates comprehensive logging features including module-specific levels, dedicated loggers, caller attribution, and cross-module logging

## Code Elements

### Functions/Methods

#### example.py

- `main() -> None`
  - Description: Main entry point that demonstrates comprehensive arlogi functionality including environment-based log levels, module-specific levels, dedicated loggers, and caller attribution
  - Location: `/opt/Code/2026/_Libs/arlogi/tests/example/example.py:8`
  - Dependencies: `os.environ`, `worker` module, `arlogi.TRACE`, `arlogi.get_json_logger`, `arlogi.get_logger`, `arlogi.get_syslog_logger`, `arlogi.setup_logging`

- `worker_function() -> None`
  - Description: Nested function demonstrating caller attribution with different depth levels (0, 1) to show function call stack context
  - Location: `/opt/Code/2026/_Libs/arlogi/tests/example/example.py:72`
  - Dependencies: `logger` (arlogi instance), `worker.do_work()`

#### worker.py

- `do_work(depth: int = 0) -> None`
  - Description: Worker function that performs logging operations with caller attribution showing cross-module call stack depth
  - Location: `/opt/Code/2026/_Libs/arlogi/tests/example/worker.py:5`
  - Dependencies: `logger` (arlogi instance)

### Classes/Modules

#### example.py

- `module: example`
  - Description: Main example module demonstrating arlogi library capabilities
  - Location: `/opt/Code/2026/_Libs/arlogi/tests/example/example.py`
  - Methods: `main()`, `worker_function()` (nested)
  - Dependencies: `os`, `worker`, `arlogi`

#### worker.py

- `module: worker`
  - Description: Worker module demonstrating cross-module logging and caller attribution
  - Location: `/opt/Code/2026/_Libs/arlogi/tests/example/worker.py`
  - Methods: `do_work()`
  - Dependencies: `arlogi`

#### **init**.py

- `package: tests.example`
  - Description: Package initialization file for tests.example module
  - Location: `/opt/Code/2026/_Libs/arlogi/tests/example/__init__.py`
  - Dependencies: None

## Dependencies

### Internal Dependencies

- `worker` module - Imported in example.py for cross-module logging demonstration

### External Dependencies

- `os` - Python standard library for environment variable access
- `arlogi` - Custom logging library used throughout the example code
  - `TRACE` - Custom log level constant
  - `get_json_logger` - Creates JSON-formatted logger instance
  - `get_logger` - Creates standard logger instance
  - `get_syslog_logger` - Creates syslog logger instance
  - `setup_logging` - Configures global logging settings

## Relationships

The example demonstrates a functional programming pattern with module-level logger instances and function-based logging operations. Here's the data flow showing how logging requests flow through the system:

```mermaid
---
title: Logging Data Flow for Tests Example
---
flowchart TB
    subgraph Environment Configuration
        ENV[LOG_LEVEL Environment Variable]
    end

    subgraph Main Module
        MAIN[example.py]
        SETUP[setup_logging()]
        LOGGERS["Loggers:<br>- app.main<br>- app.network<br>- app.database<br>- audit<br>- security"]
    end

    subgraph Worker Module
        WORKER[worker.py<br>do_work()]
    end

    subgraph External Services
        SYSLOG[Syslog Service]
        JSON[JSON Output]
    end

    ENV --> SETUP
    MAIN --> SETUP
    MAIN --> LOGGERS
    MAIN --> WORKER
    LOGGERS --> SYSLOG
    LOGGERS --> JSON
    WORKER --> LOGGERS
```

## Notes

- This example serves as both documentation and test suite for the arlogi library
- Demonstrates advanced logging features including custom TRACE level, module-specific log levels, and caller attribution
- Shows how to use different logger types (standard, JSON, syslog) for different use cases
- Illustrates cross-module logging where worker.py logs to "app.worker" while example.py logs to various application modules
