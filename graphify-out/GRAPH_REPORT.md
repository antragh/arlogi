# Graph Report - arlogi  (2026-11-25)

## Corpus Check
- 93 files · ~90,557 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2062 nodes · 2705 edges · 158 communities (140 shown, 18 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 283 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3625aff9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Core Factory & Handler Infrastructure
- Handler Implementation & Resource Management
- Thread Safety Tests
- Configuration Management
- Integration Tests
- Builder Pattern Tests
- Configuration Builder
- Logger Naming Consistency Tests
- Deprecation Warning Tests
- Trace Logger Implementation
- SRP Compliance Tests
- Type Safety Tests
- TRACE Level Validation Tests
- Backward Compatibility Tests
- Documentation Generation
- Parameter Validation Tests
- Critical Bug Fix Tests
- Feature Tests
- Core Logging Tests
- Example Applications
- Path Handling Tests
- Level Validation Helper
- Global Level Helper
- Console Output Helper
- JSON Output Helper
- Config Factory Helper
- LoggingConfig
- C4 Architecture Documentation
- .__post_init__
- Integration with Other Libraries
- File Logging Rotation Design
- C4 Code Level: docs/scripts
- C4 Code Level: API Reference Documentation
- 2. Work Breakdown Structure
- C4 Code Level: subdir
- Testing
- factory.py
- ._compute_period_key
- test_thread_safety.py
- Code Quality
- Arlogi Developer Guide
- Arlogi User Guide
- .__init__
- Contributing
- Configuration
- Troubleshooting
- handler_factory.py
- TestMultipleConfigurationChanges
- Development Setup
- Common Patterns
- Installation
- Performance Guidelines
- Release Process
- Advanced Usage
- Basic Usage
- Caller Attribution
- Output Handlers
- Architecture Decisions
- Documentation
- Best Practices
- CLAUDE.md
- config.md
- config_builder.md
- factory.md
- handler_factory.md
- handlers.md
- levels.md
- types.md
- arlogi
- LoggingConfig
- LoggerProtocol
- Configuration Guide
- TestFactoryEdgeCases
- Caller Attribution Examples
- Graph Report - Arlogi (2026-07-25)
- test_coverage_boost.py
- Arlogi Developer Guide
- TraceLogger
- Arlogi Library Documentation
- Testing
- C4 Code Level: subdir
- Arlogi Core Source Code
- ._compute_period_key
- `arlogi` - Advanced Logging Library
- Code Quality
- Publishing Workflow Design (Commitizen, GitHub Releases, PyPI)
- Arlogi User Guide
- Arlogi Test Suite
- Integration with Other Libraries
- Configuration
- Contributing
- Handler Configuration
- Troubleshooting
- Global Constraints
- Real-World Application Examples
- Code Elements
- Cross-Component Concerns
- Usage
- Quick Reference
- Key Features by Category
- Common Patterns
- Development Setup
- Environment-Specific Configuration
- Installation
- System Components
- Advanced Configuration
- Documentation
- Advanced Usage
- Application Structure Examples
- Basic Caller Attribution
- Basic Usage
- Caller Attribution
- Dynamic Configuration
- Output Handlers
- Performance Guidelines
- Release Process
- cleanup_json_logger
- cleanup_syslog_logger
- 01-architecture-conventions.md
- Quick Configuration
- Best Practices
- Configuration Reference
- Cross-Module Attribution
- Documentation
- RotatingJsonlMetricExporter
- test_core.py
- reset_otel_globals
- Architecture Decisions
- test_file_rotation.py
- ADDED Requirements
- Requirements
- ._parse_level
- Decisions
- test_rotation_config.py
- ADDED Requirements
- otel-file-exporters Specification
- Decisions
- Proposal
- ADDED Requirements
- Proposal
- Proposal
- documentation-sync Specification
- _files.py
- test_features.py
- Tasks
- docs/index.md
- Tasks
- .close
- Tasks
- Technology Stack Summary
- .with_rotation
- bootstrap.md
- decorator.md
- exporters.md
- .with_json_base_dir
- .with_module_levels

## God Nodes (most connected - your core abstractions)
1. `LoggingConfig` - 81 edges
2. `JSONFileHandler` - 81 edges
3. `Communities (70 Total, 12 Thin Omitted)` - 58 edges
4. `LoggerFactory` - 54 edges
5. `ColoredConsoleHandler` - 42 edges
6. `JSONHandler` - 34 edges
7. `ArlogiSyslogHandler` - 34 edges
8. `LoggerProtocol` - 32 edges
9. `HandlerFactory` - 30 edges
10. `LoggingConfigBuilder` - 29 edges

## Surprising Connections (you probably didn't know these)
- `test_setup_logging_preserves_positional_args_and_rejects_base_dir_without_file()` --calls--> `setup_logging()`  [INFERRED]
  tests/test_core.py → src/arlogi/factory.py
- `test_caller_attribution_renders_without_backslash_on_console_and_json()` --calls--> `ColoredConsoleHandler`  [INFERRED]
  tests/test_features.py → src/arlogi/handlers.py
- `test_colored_console_handler_markup_disabled_by_default()` --calls--> `ColoredConsoleHandler`  [INFERRED]
  tests/test_features.py → src/arlogi/handlers.py
- `main()` --calls--> `LoggingConfig`  [INFERRED]
  tests/example/example.py → src/arlogi/config.py
- `TestBranchCoverageExtra` --uses--> `LoggingConfig`  [INFERRED]
  tests/test_coverage_boost.py → src/arlogi/config.py

## Import Cycles
- None detected.

## Communities (158 total, 18 thin omitted)

### Community 0 - "Core Factory & Handler Infrastructure"
Cohesion: 0.10
Nodes (17): RichHandler, ColoredConsoleHandler, JSONFileHandler, A logging handler that uses rich for colored console output.      Features:, A logging handler that outputs log records as JSON to a file.      Automatically, Initialize the colored console handler.          Args:             show_time: Wh, Find the project root by looking for common indicators.          Searches upward, Test ColoredConsoleHandler and JSONFileHandler edge cases. (+9 more)

### Community 1 - "Handler Implementation & Resource Management"
Cohesion: 0.09
Nodes (21): Builder pattern for LoggingConfig construction.  This module provides a fluent b, get_default_level(), is_test_mode(), Logging configuration dataclass for type-safe setup.  This module provides a str, Detect if running under a test runner.      Checks solely whether ``pytest`` or, Get the default log level based on the current environment.      Returns DEBUG i, _apply_configuration(), cleanup_json_logger() (+13 more)

### Community 2 - "Thread Safety Tests"
Cohesion: 0.06
Nodes (22): Thread safety tests for arlogi.  This module tests that the library is thread-sa, Test thread safety of TRACE level registration., Test that concurrent TRACE registration is safe., Test concurrent initialization of the logging system., Test concurrent logging operations., Test concurrent logging to the same logger instance., Test that concurrent setup() calls don't duplicate handlers., Test concurrent logging with extra fields. (+14 more)

### Community 3 - "Configuration Management"
Cohesion: 0.12
Nodes (9): Build target path for a rotated file., Return a unique rotated path by appending numeric suffixes when needed., Prune old rotated files based on retention count., Ensure file stream is available for writing., Best-effort stream reopen that never raises out of rotation recovery., Report an internal rotation error via handleError., Return True when base file has content that can be rotated., Rotate current file under lock. Returns True on successful rotation. (+1 more)

### Community 4 - "Integration Tests"
Cohesion: 0.17
Nodes (12): C4 Code Level: tests/example, Code Elements, Data Flow Diagram, Dependencies, External Dependencies, Functions/Methods, Internal Dependencies, Module Relationship Diagram (+4 more)

### Community 5 - "Builder Pattern Tests"
Cohesion: 0.11
Nodes (10): LoggingConfigBuilder, Configure JSON output to console only (stderr, no file).          Returns:, Enable syslog output.          Args:             address: Syslog server address, Builder for creating LoggingConfig instances with fluent API.      This builder, Configure console output format.          Args:             show_time: Show time, Build the LoggingConfig instance.          Returns:             A validated Logg, Initialize builder with sensible defaults., Set the global log level.          Args:             level: Log level (e.g., "IN (+2 more)

### Community 6 - "Configuration Builder"
Cohesion: 0.13
Nodes (15): C4 Component Level: System Overview, Component Interactions, Component Relationships, Component Summary Table, Core Logging Library Interactions, Cross-Component Concerns, Data Flow, Dependency Graph (+7 more)

### Community 7 - "Logger Naming Consistency Tests"
Cohesion: 0.04
Nodes (49): 1. Python Package Container, 2. Test Suite Container, 3. Documentation Site Container, C4 Container Level: arlogi System Deployment, Command Line Interface, Command Line Interface, Components, Components (+41 more)

### Community 8 - "Deprecation Warning Tests"
Cohesion: 0.04
Nodes (48): API Documentation Generation, Automated Validation, Build Artifacts, C4 Component Level: Documentation System, Code Elements, Command Line Interface (CLI), Component Diagram, Component Interactions (+40 more)

### Community 9 - "Trace Logger Implementation"
Cohesion: 0.05
Nodes (44): BaseException, P, R, Span, _make_tracer_getter(), Any, @traced decorator for sync and async functions., Replace per-module span gating rules.      Keys are dotted module prefixes; valu (+36 more)

### Community 10 - "SRP Compliance Tests"
Cohesion: 0.04
Nodes (45): Advanced API, Advanced Module Configuration, Arlogi API Reference, `ArlogiSyslogHandler`, Caller Attribution, `cleanup_json_logger(name)`, `cleanup_syslog_logger(name)`, `ColoredConsoleHandler` (+37 more)

### Community 11 - "Type Safety Tests"
Cohesion: 0.05
Nodes (44): 1. Factory Pattern, 2. Builder Pattern, 3. Strategy Pattern, 4. Protocol Pattern, 5. Singleton Pattern, 6. Template Method Pattern, Advanced Features, Architecture Notes (+36 more)

### Community 12 - "TRACE Level Validation Tests"
Cohesion: 0.18
Nodes (6): ArlogiSyslogHandler, Initialize the JSON stream handler.          Args:             stream: The strea, A robust syslog handler with standard formatting and automatic fallback.      Fe, Initialize the syslog handler.          Args:             address: Syslog server, Test get_syslog_logger and cleanup_syslog_logger., TestSyslogLoggerAndCleanupCoverage

### Community 13 - "Backward Compatibility Tests"
Cohesion: 0.05
Nodes (42): Application Developer, Application Developer: Advanced Configuration Journey, Application Developer: Basic Logging Journey, Application Developer: Dedicated Logger Journey, Application Developer: JSON Logging Journey, Application Developer: Module Configuration Journey, Application Developer: TRACE Logging Journey, C4 Context Level: System Context (+34 more)

### Community 14 - "Documentation Generation"
Cohesion: 0.05
Nodes (39): Advanced Handler Configuration, Application Structure Examples, Basic Setup, CLI Application Configuration, Complete Production Setup, Conditional Logging, Configuration File Support, Configuration from Environment Variables (+31 more)

### Community 15 - "Parameter Validation Tests"
Cohesion: 0.05
Nodes (38): Adding Custom Handlers, Adding Custom Log Levels, Architecture Diagrams, Arlogi Architecture Documentation, Builder Pattern, C4 Container Diagram, C4 Context Diagram, Caller Attribution Overhead (+30 more)

### Community 16 - "Critical Bug Fix Tests"
Cohesion: 0.06
Nodes (48): MeterProvider, Resource, _build_resource(), _child_factories(), _clear_global_meter_provider(), _clear_global_tracer_provider(), _has_arlogi_correlation(), install_log_correlation() (+40 more)

### Community 17 - "Feature Tests"
Cohesion: 0.07
Nodes (29): C4 Component Level: Test Suite, `caplog` Fixture, `capsys` Fixture, Code Elements, Component Diagram, Components Tested, Core Functionality Testing, Core Test Functions (+21 more)

### Community 18 - "Core Logging Tests"
Cohesion: 0.08
Nodes (25): C4 Code Level: tests, Code Elements, Dependencies, `do_work()` function in tests/example/worker.py, External Dependencies, Integration Examples, Internal Dependencies, Key Test Categories (+17 more)

### Community 19 - "Example Applications"
Cohesion: 0.22
Nodes (7): Set up arlogi logging with the specified configuration.      This is a convenien, setup_logging(), test_module_specific_levels(), Test to verify relative path functionality in logger output., test_relative_path_logging(), Test that multiple setup() calls don't leak handlers., test_setup_logging_accepts_rotation_options()

### Community 20 - "Path Handling Tests"
Cohesion: 0.11
Nodes (13): Logger, get_json_logger(), Handler, Path, Register the custom TRACE level with Python's logging module., Return an already-created logger without instantiating a placeholder., Detach old handlers, attach replacement, then close old handlers., Detach all handlers from a logger before closing them. (+5 more)

### Community 21 - "Level Validation Helper"
Cohesion: 0.03
Nodes (58): Communities (70 Total, 12 Thin Omitted), Community 0 - "Core Factory & Handler Infrastructure", Community 10 - "SRP Compliance Tests", Community 11 - "Type Safety Tests", Community 12 - "TRACE Level Validation Tests", Community 13 - "Backward Compatibility Tests", Community 14 - "Documentation Generation", Community 15 - "Parameter Validation Tests" (+50 more)

### Community 22 - "Global Level Helper"
Cohesion: 0.19
Nodes (14): SpanExporter, Writes each export batch as one OTLP/JSON ResourceSpans object per line., RotatingJsonlSpanExporter, _provider_with(), A real OSError raised during write() must permanently degrade the writer to a no, SpanExporter logs warning with exc_info when span encoding fails., If something else closes the stream, write_line reopens a fresh file rather than, test_export_writes_valid_otlp_json_line() (+6 more)

### Community 23 - "Console Output Helper"
Cohesion: 0.08
Nodes (24): C4 Code Level: src/arlogi, Class Hierarchy Diagram, Classes/Modules, Code Elements, config.py, config.py, Dependencies, External Dependencies (+16 more)

### Community 24 - "JSON Output Helper"
Cohesion: 0.08
Nodes (24): Additional Resources, 📚 API Reference, Arlogi Library Documentation, Basic Setup, 🎯 Caller Attribution, 🔧 Configuration, Dedicated JSON Logger, 🔧 Developer Documentation (+16 more)

### Community 25 - "Config Factory Helper"
Cohesion: 0.09
Nodes (22): Background Job Processing, Basic Caller Attribution, Best Practices, Caller Attribution Examples, Class Method Attribution, Cross-Module Attribution, Cross-Module Attribution, Database Operations (+14 more)

### Community 26 - "LoggingConfig"
Cohesion: 0.08
Nodes (19): JSONFormatter, JSON formatter for structured log output.      Outputs log records as JSON with, Resource management tests for arlogi.  This module tests that handlers properly, Test ColoredConsoleHandler's project root caching., Test that project root detection is cached., Test that cache persists across multiple handler creations., Test JSONFormatter's error handling., Test that JSONFormatter handles objects that can't be serialized. (+11 more)

### Community 27 - "C4 Architecture Documentation"
Cohesion: 0.09
Nodes (22): About the C4 Model, Additional Resources, API Specifications, Architecture Levels, C4 Architecture Documentation, Code-Level Documents, Component Documentation, Contributing (+14 more)

### Community 28 - ".__post_init__"
Cohesion: 0.12
Nodes (20): LoggerFactory, Factory for creating logger instances with caller attribution support.  This mod, Log a critical message., Log a fatal (critical) message., Factory for creating and configuring logger instances.      This factory manages, Configure the root logger level.          Args:             config: The logging, Clear existing handlers and add configured ones atomically.          Constructs, HandlerFactory (+12 more)

### Community 29 - "Integration with Other Libraries"
Cohesion: 0.09
Nodes (22): Advanced Configuration, `arlogi` - Advanced Logging Library, Basic Setup, Centralized Logging Setup, Color Schemes, Dedicated Loggers, Default INFO when `arlogi` is not imported, Development (+14 more)

### Community 30 - "File Logging Rotation Design"
Cohesion: 0.10
Nodes (20): ADDED Requirements, Purpose, Requirement: Elapsed-period archive naming on schedule rotation, Requirement: Exact-pattern retention pruning and non-fatal rotation error recovery, Requirement: Idempotent and synchronized JSON stream closure, Requirement: Literal console message rendering by default, Requirement: Protected JSON envelope with nested extra collision handling, Requirement: Resilient JSON fallback serialization (+12 more)

### Community 31 - "C4 Code Level: docs/scripts"
Cohesion: 0.11
Nodes (19): `build_pub.sh`, C4 Code Level: docs/scripts, Code Elements, `create_markdown(md_filepath: Path, module_path: str, classes: list, functions: list)`, `create_nav_menu_yaml(nav_items: list[Path])`, Dependencies, External Dependencies, `extract_classes_and_functions(filepath: Path) -> tuple[list[str], list[str]]` (+11 more)

### Community 32 - "C4 Code Level: API Reference Documentation"
Cohesion: 0.12
Nodes (16): C4 Code Level: API Reference Documentation, Code Elements, Configuration Dependencies, Cross-Reference Relationships, Dependencies, Documentation Structure Relationship, Generated Documentation Files, Integration Points (+8 more)

### Community 33 - "2. Work Breakdown Structure"
Cohesion: 0.10
Nodes (20): json-handlers-and-rotation Specification, Purpose, Requirement: Elapsed-period archive naming on schedule rotation, Requirement: Exact-pattern retention pruning and non-fatal rotation error recovery, Requirement: Idempotent and synchronized JSON stream closure, Requirement: Literal console message rendering by default, Requirement: Protected JSON envelope with nested extra collision handling, Requirement: Resilient JSON fallback serialization (+12 more)

### Community 34 - "C4 Code Level: subdir"
Cohesion: 0.22
Nodes (5): Test concurrent logger creation., Test creating many loggers concurrently with different names., Test concurrent JSON logger creation., Test concurrent logger creation with different levels., TestConcurrentLoggerCreation

### Community 35 - "Testing"
Cohesion: 0.18
Nodes (11): Coverage Requirements, Feature Tests, Integration Tests, Running Tests, Test Categories, Test Fixtures, Test Mode Detection, Test Structure (+3 more)

### Community 36 - "factory.py"
Cohesion: 0.10
Nodes (19): ADDED Requirements, Purpose, Requirement: Accurate call-site stacklevel and caller attribution, Requirement: Atomic create-before-detach handler reconfiguration, Requirement: Dedicated loggers conform to LoggerProtocol in fresh processes, Requirement: Disabled-level fast path without side effects, Requirement: Non-mutating structured keyword and Mapping extra handling, Requirement: Thread-safe dedicated logger replacement, cleanup, and rotation (+11 more)

### Community 37 - "._compute_period_key"
Cohesion: 0.05
Nodes (44): Advanced API, Advanced Module Configuration, Arlogi API Reference, `ArlogiSyslogHandler`, Caller Attribution, `cleanup_json_logger(name)`, `cleanup_syslog_logger(name)`, `ColoredConsoleHandler` (+36 more)

### Community 38 - "test_thread_safety.py"
Cohesion: 0.18
Nodes (10): Appends lines to `<directory>/<prefix>-YYYYMMDD-HHMMSS.jsonl`.      A new file i, Test seam, mirroring JSONFileHandler._now_local., _RotatingJsonlWriter, Multiple threads concurrently writing to the writer must produce clean, non-corr, If _stream is None after opening attempt, writer safely marks broken without ass, test_concurrent_writes_thread_safe(), test_writer_prune_skips_dangling_symlink_and_preserves_sibling_files(), test_writer_rejects_invalid_rotate_hours() (+2 more)

### Community 39 - "Code Quality"
Cohesion: 0.22
Nodes (9): Code Quality, Code Style Guidelines, Complexity Limits, Docstring Format, Linting with Ruff, Naming Conventions, Pre-commit Hooks, Ruff Configuration (+1 more)

### Community 40 - "Arlogi Developer Guide"
Cohesion: 0.25
Nodes (8): Arlogi Developer Guide, Continuous Integration, Getting Help, GitHub Actions Workflow, License, Module Responsibilities, Project Structure, Table of Contents

### Community 41 - "Arlogi User Guide"
Cohesion: 0.29
Nodes (7): Arlogi User Guide, Getting Help, License, Minimal Setup, Performance Tips, Quick Start, Table of Contents

### Community 42 - ".__init__"
Cohesion: 0.22
Nodes (6): Path, Initialize the JSON file handler.          Args:             filename: Path to t, Resolve ``filename`` against ``base_dir``, rejecting escapes.          Args:, Get current local datetime.          This indirection keeps schedule checks test, Compute the period key for the configured schedule., Return (archive_period_key, next_active_period_key) when emit should rotate.

### Community 43 - "Contributing"
Cohesion: 0.29
Nodes (7): Code Review Criteria, Commit Message Format, Contributing, Contribution Workflow, PR Description Template, PR Title, Pull Request Guidelines

### Community 44 - "Configuration"
Cohesion: 0.29
Nodes (7): Basic Configuration, Complete Configuration, Configuration, JSON File Logging, JSON-Only Output, Per-Module Levels, Syslog Integration

### Community 45 - "Troubleshooting"
Cohesion: 0.29
Nodes (7): Issue: Caller Attribution Shows Wrong Function, Issue: Duplicate Logs, Issue: JSON File Not Created, Issue: Logs Not Appearing, Issue: Rich Colors Not Working, Issue: Syslog Not Working, Troubleshooting

### Community 46 - "handler_factory.py"
Cohesion: 0.46
Nodes (7): create_console(), create_handlers(), create_json_file(), create_json_handler(), create_json_stream(), create_syslog(), Handler factory for creating logging handlers.  This module provides a centraliz

### Community 47 - "TestMultipleConfigurationChanges"
Cohesion: 0.05
Nodes (38): Adding Custom Handlers, Adding Custom Log Levels, Architecture Diagrams, Arlogi Architecture Documentation, Builder Pattern, C4 Container Diagram, C4 Context Diagram, Caller Attribution Overhead (+30 more)

### Community 48 - "Development Setup"
Cohesion: 0.40
Nodes (5): Clone Repository, Development Commands, Development Setup, Install Dependencies, Prerequisites

### Community 49 - "Common Patterns"
Cohesion: 0.40
Nodes (5): Application Startup, Background Task Logging, Common Patterns, Database Operation Logging, Request/Response Logging

### Community 50 - "Installation"
Cohesion: 0.40
Nodes (5): From Source, Installation, Requirements, Using pip, Using uv

### Community 51 - "Performance Guidelines"
Cohesion: 0.50
Nodes (4): Optimization Checklist, Performance Guidelines, Performance Targets, Profiling

### Community 52 - "Release Process"
Cohesion: 0.50
Nodes (4): Release Checklist, Release Notes Template, Release Process, Version Management

### Community 53 - "Advanced Usage"
Cohesion: 0.50
Nodes (4): Advanced Usage, Conditional Logging, Context Managers, Lazy Log Evaluation

### Community 54 - "Basic Usage"
Cohesion: 0.50
Nodes (4): Basic Usage, Log Levels, Logging Exceptions, Structured Logging

### Community 55 - "Caller Attribution"
Cohesion: 0.50
Nodes (4): Best Practices, Caller Attribution, Cross-Module Attribution, Understanding Depth Values

### Community 56 - "Output Handlers"
Cohesion: 0.50
Nodes (4): Console Handler, JSON Logger, Output Handlers, Syslog Logger

### Community 57 - "Architecture Decisions"
Cohesion: 0.67
Nodes (3): Architecture Decisions, Current Architecture, Decision Records

### Community 58 - "Documentation"
Cohesion: 0.67
Nodes (3): Docstring Standards, Documentation, Updating Documentation

### Community 59 - "Best Practices"
Cohesion: 0.67
Nodes (3): Best Practices, DO, DON'T

### Community 70 - "LoggingConfig"
Cohesion: 0.10
Nodes (15): LoggingConfig, Determine if console output should be shown.          Returns:             True, Determine if JSON output is configured.          Returns:             True if JS, Immutable configuration for arlogi logging setup.      Attributes:         level, Handler, Create a syslog handler.          Args:             config: Logging configuratio, Create all handlers based on configuration.          This is the main factory me, Create a colored console handler.          Args:             config: Logging con (+7 more)

### Community 71 - "LoggerProtocol"
Cohesion: 0.09
Nodes (12): Protocol, get_global_logger(), get_logger(), Get a logger instance conforming to LoggerProtocol.          Auto-initializes wi, Get or initialize the global logger instance.          Returns:             The, Get a logger instance with caller attribution support.      Args:         name:, setup(), LoggerProtocol (+4 more)

### Community 73 - "Configuration Guide"
Cohesion: 0.14
Nodes (14): Advanced Handler Configuration, Conditional Logging, Configuration Guide, Configuration Validation, Custom Formatters, FILE: docs/CALLER_ATTRIBUTION_EXAMPLES.md, Filtering Logs, High-Performance Configuration (+6 more)

### Community 74 - "TestFactoryEdgeCases"
Cohesion: 0.50
Nodes (3): Rotate JSON file handlers attached to the named JSON logger.      Args:, rotate_json_logger(), test_rotate_json_logger_helper()

### Community 75 - "Caller Attribution Examples"
Cohesion: 0.15
Nodes (12): Arlogi User Guides and API Reference, Best Practices, Caller Attribution Examples, Efficient Caller Attribution, FILE: docs/DEVELOPER_GUIDE.md, FILE: docs/USER_GUIDE.md, Modern Setup, Performance Considerations (+4 more)

### Community 76 - "Graph Report - Arlogi (2026-07-25)"
Cohesion: 0.15
Nodes (12): Arlogi Codebase Knowledge Graph (Graphify), Community Hubs (Navigation), Corpus Check, FILE: graphify-out/GRAPH_REPORT.md, God Nodes (Most cOnnected - yOur cOre aBstractions), Graph Freshness, Graph Report - Arlogi (2026-07-25), Import Cycles (+4 more)

### Community 77 - "test_coverage_boost.py"
Cohesion: 0.10
Nodes (19): logger-lifecycle Specification, Purpose, Requirement: Accurate call-site stacklevel and caller attribution, Requirement: Atomic create-before-detach handler reconfiguration, Requirement: Dedicated loggers conform to LoggerProtocol in fresh processes, Requirement: Disabled-level fast path without side effects, Requirement: Non-mutating structured keyword and Mapping extra handling, Requirement: Thread-safe dedicated logger replacement, cleanup, and rotation (+11 more)

### Community 78 - "Arlogi Developer Guide"
Cohesion: 0.17
Nodes (12): Arlogi Developer Guide, Continuous Integration, Docstring Standards, Documentation, FILE: docs/API_REFERENCE.md, Getting Help, GitHub Actions Workflow, License (+4 more)

### Community 79 - "TraceLogger"
Cohesion: 0.10
Nodes (16): Any, Log a message with TRACE level (below DEBUG).          Args:             msg: Th, Log a warning message., Log an error message., Log an exception with traceback., Log a message at the specified level., Custom logger class with trace() and caller attribution support.      This logge, Find the name of the module and function at the specified depth.          Args: (+8 more)

### Community 80 - "Arlogi Library Documentation"
Cohesion: 0.18
Nodes (11): Additional Resources, Arlogi Library Documentation, Documentation Guide, FILE: docs/ARCHITECTURE.md, Getting Started, Key Features, License, Performance Notes (+3 more)

### Community 81 - "Testing"
Cohesion: 0.18
Nodes (11): Coverage Requirements, Feature Tests, Integration Tests, Running Tests, Test Categories, Test Fixtures, Test Mode Detection, Test Structure (+3 more)

### Community 82 - "C4 Code Level: subdir"
Cohesion: 0.17
Nodes (12): C4 Code Level: subdir, Classes/Modules, Code Elements, Dependencies, External Dependencies, Functions/Methods, Internal Dependencies, `main()` (implicit main execution) (+4 more)

### Community 83 - "Arlogi Core Source Code"
Cohesion: 0.20
Nodes (9): Arlogi Core Source Code, FILE: src/arlogi/config_builder.py, FILE: src/arlogi/config.py, FILE: src/arlogi/factory.py, FILE: src/arlogi/handler_factory.py, FILE: src/arlogi/handlers.py, FILE: src/arlogi/__init__.py, FILE: src/arlogi/levels.py (+1 more)

### Community 84 - "._compute_period_key"
Cohesion: 0.17
Nodes (9): MetricExportResult, MetricsData, ReadableSpan, SpanExportResult, b64_ids_to_hex(), Any, OTLP/JSON encoding helpers.  Protobuf's JSON mapping emits bytes fields (trace/s, Recursively convert base64-encoded id fields to lowercase hex, in place. (+1 more)

### Community 85 - "`arlogi` - Advanced Logging Library"
Cohesion: 0.22
Nodes (9): `arlogi` - Advanced Logging Library, Development, Features, FILE: CLAUDE.md, FILE: docs/index.md, FILE: pyproject.toml, Graphify, Installation (+1 more)

### Community 86 - "Code Quality"
Cohesion: 0.22
Nodes (9): Code Quality, Code Style Guidelines, Complexity Limits, Docstring Format, Linting with Ruff, Naming Conventions, Pre-commit Hooks, Ruff Configuration (+1 more)

### Community 87 - "Publishing Workflow Design (Commitizen, GitHub Releases, PyPI)"
Cohesion: 0.16
Nodes (10): LogRecord, Any, Override render method to show relative paths from project root.          Args:, Get level text as a single character with styling.          Args:             re, Render message text with level-specific styling.          Args:             reco, Convert value to string without raising., Merge non-standard record attributes into log_data without clobbering envelope k, Format log record as JSON.          Args:             record: The log record to (+2 more)

### Community 88 - "Arlogi User Guide"
Cohesion: 0.25
Nodes (8): Arlogi User Guide, FILE: docs/CONFIGURATION_GUIDE.md, Getting Help, License, Minimal Setup, Performance Tips, Quick Start, Table of Contents

### Community 89 - "Arlogi Test Suite"
Cohesion: 0.25
Nodes (7): Arlogi Test Suite, FILE: tests/test_core.py, FILE: tests/test_features.py, FILE: tests/test_file_rotation.py, FILE: tests/test_resource_management.py, FILE: tests/test_rotation_config.py, FILE: tests/test_thread_safety.py

### Community 90 - "Integration with Other Libraries"
Cohesion: 0.29
Nodes (7): Default INFO when `arlogi` is Not Imported, Integration with Other Libraries, Lazy Initialization (Safe Use of .trace), Making third‑party Libraries Respect the Chosen Level, Overriding the Level when You _do_ Use `arlogi`, Quick Bootstrap Example, Using TRACE in Your Library

### Community 91 - "Configuration"
Cohesion: 0.29
Nodes (7): Basic Configuration, Complete Configuration, Configuration, JSON File Logging, JSON-Only Output, Per-Module Levels, Syslog Integration

### Community 92 - "Contributing"
Cohesion: 0.29
Nodes (7): Code Review Criteria, Commit Message Format, Contributing, Contribution Workflow, PR Description Template, PR Title, Pull Request Guidelines

### Community 93 - "Handler Configuration"
Cohesion: 0.29
Nodes (7): Console Handler Configuration, Custom JSON Handlers, Handler Configuration, JSON File Configuration, JSON File Structure, Syslog Configuration (Modern), Syslog Handler Details

### Community 94 - "Troubleshooting"
Cohesion: 0.29
Nodes (7): Issue: Caller Attribution Shows Wrong Function, Issue: Duplicate Logs, Issue: JSON File Not Created, Issue: Logs Not Appearing, Issue: Rich Colors Not Working, Issue: Syslog Not Working, Troubleshooting

### Community 95 - "Global Constraints"
Cohesion: 0.11
Nodes (17): ADDED Requirements, Purpose, Requirement: Fluent configuration builder parity and console-only override, Requirement: Public configuration application and root package exports, Requirement: Rotation parameter validation, Requirement: Spoof-resistant test-mode detection, Requirement: Strict log level validation and resolution, Scenario: Applying a pre-built configuration via setup_logging (+9 more)

### Community 96 - "Real-World Application Examples"
Cohesion: 0.33
Nodes (6): Background Job Processing, Class Method Attribution, Database Operations, Error Handling and Exception Tracking, Real-World Application Examples, Web API Handler

### Community 97 - "Code Elements"
Cohesion: 0.11
Nodes (17): Feat, Feat, Feat, Feat, Fix, Fix, Fix, Fix (+9 more)

### Community 98 - "Cross-Component Concerns"
Cohesion: 0.11
Nodes (17): logging-configuration Specification, Purpose, Requirement: Fluent configuration builder parity and console-only override, Requirement: Public configuration application and root package exports, Requirement: Rotation parameter validation, Requirement: Spoof-resistant test-mode detection, Requirement: Strict log level validation and resolution, Requirements (+9 more)

### Community 99 - "Usage"
Cohesion: 0.40
Nodes (5): Basic Setup, Dedicated Loggers, JSON File Rotation and Syslog, Module-Specific Levels, Usage

### Community 100 - "Quick Reference"
Cohesion: 0.40
Nodes (5): Basic Setup, Dedicated JSON Logger, Per-Module Levels, Quick Reference, With JSON Logging

### Community 101 - "Key Features by Category"
Cohesion: 0.40
Nodes (5): 🎯 Caller Attribution, 🔧 Configuration, 🎨 Handlers, Key Features by Category, 📊 Log Levels

### Community 102 - "Common Patterns"
Cohesion: 0.40
Nodes (5): Application Startup, Background Task Logging, Common Patterns, Database Operation Logging, Request/Response Logging

### Community 103 - "Development Setup"
Cohesion: 0.40
Nodes (5): Clone Repository, Development Commands, Development Setup, Install Dependencies, Prerequisites

### Community 104 - "Environment-Specific Configuration"
Cohesion: 0.40
Nodes (5): Development Environment, Environment-Specific Configuration, Production Environment, Staging Environment, Testing Environment

### Community 105 - "Installation"
Cohesion: 0.40
Nodes (5): From Source, Installation, Requirements, Using Pip, Using Uv

### Community 106 - "System Components"
Cohesion: 0.50
Nodes (4): Core Logging Library, Documentation System, Test Suite, System Components

### Community 107 - "Advanced Configuration"
Cohesion: 0.50
Nodes (4): Advanced Configuration, Centralized Logging Setup, Color Schemes, Direct Factory API

### Community 108 - "Documentation"
Cohesion: 0.50
Nodes (4): 📚 API Reference, 🔧 Developer Documentation, Documentation, 📖 User Documentation

### Community 109 - "Advanced Usage"
Cohesion: 0.50
Nodes (4): Advanced Usage, Conditional Logging, Context Managers, Lazy Log Evaluation

### Community 110 - "Application Structure Examples"
Cohesion: 0.50
Nodes (4): Application Structure Examples, CLI Application Configuration, Microservice Configuration, Web Application Configuration

### Community 111 - "Basic Caller Attribution"
Cohesion: 0.50
Nodes (4): Basic Caller Attribution, Using `caller_depth=0` (Current Function), Using `caller_depth=1` (Immediate Caller), Using `caller_depth=2` (Caller's Caller)

### Community 112 - "Basic Usage"
Cohesion: 0.50
Nodes (4): Basic Usage, Log Levels, Logging Exceptions, Structured Logging

### Community 113 - "Caller Attribution"
Cohesion: 0.50
Nodes (4): Best Practices, Caller Attribution, Cross-Module Attribution, Understanding Depth Values

### Community 114 - "Dynamic Configuration"
Cohesion: 0.50
Nodes (4): Configuration File Support, Configuration from Environment Variables, Dynamic Configuration, Runtime Level Adjustment

### Community 115 - "Output Handlers"
Cohesion: 0.50
Nodes (4): Console Handler, JSON Logger, Output Handlers, Syslog Logger

### Community 116 - "Performance Guidelines"
Cohesion: 0.50
Nodes (4): Optimization Checklist, Performance Guidelines, Performance Targets, Profiling

### Community 117 - "Release Process"
Cohesion: 0.50
Nodes (4): Release Checklist, Release Notes Template, Release Process, Version Management

### Community 118 - "cleanup_json_logger"
Cohesion: 0.13
Nodes (9): Any, Convert configuration to a dictionary.          Returns:             Dictionary, Create LoggingConfig from keyword arguments.          This factory method provid, Centralized logging setup for arlogi.          This method configures the root l, Apply a pre-built LoggingConfig to the root logger under lock.          Args:, Apply a LoggingConfig to the root logger.          Args:             config: The, Apply module-specific log level overrides.          Args:             config: Th, test_public_exports_and_apply_config() (+1 more)

### Community 119 - "cleanup_syslog_logger"
Cohesion: 0.13
Nodes (14): ADDED Requirements, Purpose, Requirement: Chained LogRecordFactory idempotency for log correlation, Requirement: Complete sync and async generator lifecycle forwarding in @traced, Requirement: External global provider safety and attribute checks on reset, Requirement: Provider-restart-safe tracer resolution in @traced, Requirement: Strict OTLP endpoint validation and thread-leak-free bootstrap rollback, Scenario: Calling install_log_correlation after third-party factory wrapping (+6 more)

### Community 121 - "Quick Configuration"
Cohesion: 0.67
Nodes (3): Basic Setup, Complete Production Setup, Quick Configuration

### Community 122 - "Best Practices"
Cohesion: 0.67
Nodes (3): Best Practices, DO, DON'T

### Community 123 - "Configuration Reference"
Cohesion: 0.67
Nodes (3): Configuration Reference, Log Levels, `LoggingConfig` Attributes

### Community 124 - "Cross-Module Attribution"
Cohesion: 0.67
Nodes (3): Cross-Module Attribution, Cross-Module Attribution, Same Module Attribution

### Community 125 - "Documentation"
Cohesion: 0.13
Nodes (14): otel-lifecycle Specification, Purpose, Requirement: Chained LogRecordFactory idempotency for log correlation, Requirement: Complete sync and async generator lifecycle forwarding in @traced, Requirement: External global provider safety and attribute checks on reset, Requirement: Provider-restart-safe tracer resolution in @traced, Requirement: Strict OTLP endpoint validation and thread-leak-free bootstrap rollback, Requirements (+6 more)

### Community 126 - "RotatingJsonlMetricExporter"
Cohesion: 0.20
Nodes (6): MetricExporter, Path, Writes each export as one OTLP/JSON ResourceMetrics object per line., RotatingJsonlMetricExporter, MetricExporter logs warning with exc_info when metric encoding fails., test_metric_exporter_logs_warning_on_encode_failure()

### Community 127 - "test_core.py"
Cohesion: 0.22
Nodes (3): Detect if running under a test runner.          Checks solely whether ``pytest``, test_setup_logging_preserves_positional_args_and_rejects_base_dir_without_file(), test_test_mode_detection()

### Community 128 - "reset_otel_globals"
Cohesion: 0.14
Nodes (13): 1. Unified Level Parsing & Dataclass Introspection in `LoggingConfig`, 2. Sentinel-Guarded `setup_logging(config=...)` and `LoggerFactory.apply_config()`, 3. Concurrency, Lock Ordering & Create-Before-Detach Handler Replacement, 4. `TraceLogger` Fast Path, Non-Mutating `extra`, and Frame-Depth Math, 5. `JSONFormatter` Envelope Protection & Resilient Fallback, 6. Synchronized, Idempotent `JSONHandler.close()`, 7. `JSONFileHandler` Containment, Elapsed-Period Naming, Regex Pruning & Non-Fatal Recovery, Context (+5 more)

### Community 129 - "Architecture Decisions"
Cohesion: 0.67
Nodes (3): Architecture Decisions, Current Architecture, Decision Records

### Community 130 - "test_file_rotation.py"
Cohesion: 0.33
Nodes (11): datetime, _emit(), test_base_dir_containment_rejects_traversal_and_directory_equal(), test_emit_boundary_rotation_uses_elapsed_period_key(), test_emit_rotates_on_period_boundary(), test_period_key_generation(), test_pruning_preserves_sibling_files_and_works_in_bracketed_dirs(), test_retention_prunes_old_rotated_files() (+3 more)

### Community 131 - "ADDED Requirements"
Cohesion: 0.17
Nodes (11): ADDED Requirements, Purpose, Requirement: Automated pull-request and branch CI quality gates, Requirement: Documentation deployment on master, release tags, and manual dispatch, Requirement: Lean source distribution and split dependency groups, Requirement: Tag-guarded release publication and least-privilege permissions, Scenario: Building a minimal sdist without graphify-out dumps, Scenario: Deploying documentation via workflow_dispatch or release tag (+3 more)

### Community 132 - "Requirements"
Cohesion: 0.17
Nodes (11): ci-and-packaging Specification, Purpose, Requirement: Automated pull-request and branch CI quality gates, Requirement: Documentation deployment on master, release tags, and manual dispatch, Requirement: Lean source distribution and split dependency groups, Requirement: Tag-guarded release publication and least-privilege permissions, Requirements, Scenario: Building a minimal sdist without graphify-out dumps (+3 more)

### Community 133 - "._parse_level"
Cohesion: 0.18
Nodes (6): Validate a log level value.          Args:             level: Log level as int o, Get the global level as an integer.          Returns:             The resolved l, Resolve a module level to an integer.          Args:             name: Module na, Validate configuration after initialization., Parse and validate a log level value into an integer.          Args:, _validate_level()

### Community 134 - "Decisions"
Cohesion: 0.20
Nodes (9): 1. Provider-Keyed Tracer Cache in `decorator.py` (`DA-003`, `DA-031`), 2. Endpoint Validation, Rollback & External Provider Safety in `bootstrap.py` (`DA-009`, `DA-010`, `DA-024`), 3. `_RotatingJsonlWriter` Prefix/Bounds Validation & Safe Pruning (`DA-002`, `DA-006`), 4. `tests/conftest.py` Teardown Hygiene (`DA-022`), Context, Decisions, Design, Goals / Non-Goals (+1 more)

### Community 135 - "test_rotation_config.py"
Cohesion: 0.20
Nodes (8): test_builder_with_json_console_only_clears_json_file_name(), test_builder_with_rotation_defaults_retention_to_none(), test_builder_with_rotation_options(), test_logging_config_accepts_rotation_options(), test_logging_config_rejects_invalid_and_boolean_levels(), test_logging_config_rejects_invalid_retention_count(), test_logging_config_rejects_invalid_retention_types_and_bounds(), test_logging_config_rejects_invalid_rotate_schedule()

### Community 136 - "ADDED Requirements"
Cohesion: 0.22
Nodes (8): ADDED Requirements, Purpose, Requirement: Non-fatal, exact-pattern retention pruning in rotating JSONL writers, Requirement: Safe prefix and positive integer bounds validation in rotating JSONL writers, Scenario: Continuing telemetry writes when a matched file vanishes or a dangling symlink exists, Scenario: Rejecting non-positive or boolean rotate_hours and retention_count, Scenario: Rejecting path traversal, absolute paths, and glob metacharacters in prefix, Spec Delta

### Community 137 - "otel-file-exporters Specification"
Cohesion: 0.22
Nodes (8): otel-file-exporters Specification, Purpose, Requirement: Non-fatal, exact-pattern retention pruning in rotating JSONL writers, Requirement: Safe prefix and positive integer bounds validation in rotating JSONL writers, Requirements, Scenario: Continuing telemetry writes when a matched file vanishes or a dangling symlink exists, Scenario: Rejecting non-positive or boolean rotate_hours and retention_count, Scenario: Rejecting path traversal, absolute paths, and glob metacharacters in prefix

### Community 138 - "Decisions"
Cohesion: 0.25
Nodes (7): 1. CI Workflows & Release Guards, 2. Packaging & Dependency Groups, 3. Documentation & MkDocs Sync, Context, Decisions, Design, Goals / Non-Goals

### Community 139 - "Proposal"
Cohesion: 0.25
Nodes (7): Capabilities, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 140 - "ADDED Requirements"
Cohesion: 0.25
Nodes (7): ADDED Requirements, Purpose, Requirement: Accurate security and configuration documentation, Requirement: Complete arlogi.otel documentation and MkDocs reference coverage, Scenario: Building MkDocs site with complete arlogi.otel reference, Scenario: Following documented configuration and security guides without errors, Spec Delta

### Community 141 - "Proposal"
Cohesion: 0.25
Nodes (7): Capabilities, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 142 - "Proposal"
Cohesion: 0.25
Nodes (7): Capabilities, Impact, Modified Capabilities, New Capabilities, Proposal, What Changes, Why

### Community 143 - "documentation-sync Specification"
Cohesion: 0.25
Nodes (7): documentation-sync Specification, Purpose, Requirement: Accurate security and configuration documentation, Requirement: Complete arlogi.otel documentation and MkDocs reference coverage, Requirements, Scenario: Building MkDocs site with complete arlogi.otel reference, Scenario: Following documented configuration and security guides without errors

### Community 144 - "_files.py"
Cohesion: 0.32
Nodes (6): Path, Rotating JSONL file writer shared by the span and metric exporters., Validate that prefix is a safe single filename component., Validate that value is a non-boolean integer >= 1., _validate_positive_int(), _validate_prefix()

### Community 146 - "Tasks"
Cohesion: 0.29
Nodes (6): 1. Configuration, Builder & Test-Mode Hardening (`logging-configuration`), 2. JSON Formatting, Stream Closure & File Rotation (`json-handlers-and-rotation`), 3. Logger Lifecycle, Concurrency & Call-Site Attribution (`logger-lifecycle`), 4. Cross-Module Integration & Quality Verification, Tasks, Workflow follow-up

### Community 148 - "Tasks"
Cohesion: 0.33
Nodes (5): 1. Rotating JSONL Writer & Exporter Hardening (`otel-file-exporters`), 2. `@traced` Lifecycle & Complexity Refactor (`otel-lifecycle`), 3. OTLP Bootstrap, Correlation & Test Teardown (`otel-lifecycle`), 4. Cross-Module Verification, Tasks

### Community 149 - ".close"
Cohesion: 0.33
Nodes (3): Close the handler and the stream if we own it.          Only closes custom strea, Close the handler and mark it closed so it will not reopen., Close the handler safely even if initialization failed.

### Community 150 - "Tasks"
Cohesion: 0.40
Nodes (4): 1. CI/CD Workflows & Packaging (`ci-and-packaging`), 2. Documentation & MkDocs Sync (`documentation-sync`), 3. Final Verification, Tasks

### Community 151 - "Technology Stack Summary"
Cohesion: 0.50
Nodes (4): Core Technologies, Development Tools, Supporting Technologies, Technology Stack Summary

## Knowledge Gaps
- **975 isolated node(s):** `arlogi`, `Fix`, `Fix`, `Fix`, `Feat` (+970 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `JSONFileHandler` connect `Core Factory & Handler Infrastructure` to `Handler Implementation & Resource Management`, `test_file_rotation.py`, `Configuration Management`, `Thread Safety Tests`, `C4 Code Level: subdir`, `LoggingConfig`, `LoggerProtocol`, `.__init__`, `TRACE Level Validation Tests`, `handler_factory.py`, `TraceLogger`, `Path Handling Tests`, `.close`, `Publishing Workflow Design (Commitizen, GitHub Releases, PyPI)`, `LoggingConfig`, `.__post_init__`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `C4 Container Level: arlogi System Deployment` connect `Logger Naming Consistency Tests` to `C4-Documentation/README.md`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Why does `C4 Component Level: Core Logging Library` connect `Type Safety Tests` to `C4-Documentation/README.md`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Are the 34 inferred relationships involving `LoggingConfig` (e.g. with `LoggingConfigBuilder` and `Builder pattern for LoggingConfig construction.  This module provides a fluent b`) actually correct?**
  _`LoggingConfig` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 40 inferred relationships involving `JSONFileHandler` (e.g. with `LoggerFactory` and `TraceLogger`) actually correct?**
  _`JSONFileHandler` has 40 INFERRED edges - model-reasoned connections that need verification._
- **Are the 33 inferred relationships involving `LoggerFactory` (e.g. with `LoggingConfig` and `HandlerFactory`) actually correct?**
  _`LoggerFactory` has 33 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `ColoredConsoleHandler` (e.g. with `HandlerFactory` and `Handler factory for creating logging handlers.  This module provides a centraliz`) actually correct?**
  _`ColoredConsoleHandler` has 28 INFERRED edges - model-reasoned connections that need verification._