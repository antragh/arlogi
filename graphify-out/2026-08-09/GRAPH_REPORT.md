# Graph Report - arlogi  (2026-07-25)

## Corpus Check
- 59 files · ~79,293 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1560 nodes · 2229 edges · 126 communities (115 shown, 11 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 419 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `65abaf72`
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

## God Nodes (most connected - your core abstractions)
1. `JSONFileHandler` - 114 edges
2. `LoggingConfig` - 102 edges
3. `LoggerFactory` - 76 edges
4. `JSONHandler` - 61 edges
5. `Communities (70 Total, 12 Thin Omitted)` - 58 edges
6. `ColoredConsoleHandler` - 54 edges
7. `LoggerProtocol` - 46 edges
8. `HandlerFactory` - 44 edges
9. `ArlogiSyslogHandler` - 43 edges
10. `JSONFormatter` - 33 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `LoggingConfig`  [INFERRED]
  tests/example/example.py → src/arlogi/config.py
- `TestBranchCoverageExtra` --uses--> `LoggingConfig`  [INFERRED]
  tests/test_coverage_boost.py → src/arlogi/config.py
- `TestConfigBuilderCoverage` --uses--> `LoggingConfig`  [INFERRED]
  tests/test_coverage_boost.py → src/arlogi/config.py
- `TestFactoryEdgeCases` --uses--> `LoggingConfig`  [INFERRED]
  tests/test_coverage_boost.py → src/arlogi/config.py
- `TestHandlersCoverageEdgeCases` --uses--> `LoggingConfig`  [INFERRED]
  tests/test_coverage_boost.py → src/arlogi/config.py

## Import Cycles
- None detected.

## Communities (126 total, 11 thin omitted)

### Community 0 - "Core Factory & Handler Infrastructure"
Cohesion: 0.08
Nodes (28): RichHandler, ColoredConsoleHandler, JSONFormatter, JSON formatter for structured log output.      Outputs log records as JSON with, A logging handler that uses rich for colored console output.      Features:, Test ColoredConsoleHandler and JSONFileHandler edge cases., TestHandlersCoverageEdgeCases, Resource management tests for arlogi.  This module tests that handlers properly (+20 more)

### Community 1 - "Handler Implementation & Resource Management"
Cohesion: 0.22
Nodes (5): get_default_level(), is_test_mode(), Logging configuration dataclass for type-safe setup.  This module provides a str, Detect if running under a test runner.      Checks for pytest, unittest, or the, Get the default log level based on the current environment.      Returns DEBUG i

### Community 2 - "Thread Safety Tests"
Cohesion: 0.08
Nodes (20): LoggerFactory, main(), Thread safety tests for arlogi.  This module tests that the library is thread-sa, Test concurrent logging operations., Test concurrent logging to the same logger instance., Test concurrent initialization of the logging system., Test concurrent logging with extra fields., Test concurrent logging at different levels. (+12 more)

### Community 3 - "Configuration Management"
Cohesion: 0.12
Nodes (8): Close the handler and the stream if we own it.          Only closes custom strea, Build target path for a rotated file., Return a unique rotated path by appending numeric suffixes when needed., Prune old rotated files based on retention count., Ensure file stream is available for writing., Return True when base file has content that can be rotated., Rotate current file under lock. Returns True on successful rotation., Force immediate file rotation.          Returns:             True if rotation co

### Community 4 - "Integration Tests"
Cohesion: 0.17
Nodes (12): C4 Code Level: tests/example, Code Elements, Data Flow Diagram, Dependencies, External Dependencies, Functions/Methods, Internal Dependencies, Module Relationship Diagram (+4 more)

### Community 5 - "Builder Pattern Tests"
Cohesion: 0.06
Nodes (23): LoggingConfigBuilder, Builder pattern for LoggingConfig construction.  This module provides a fluent b, Enable syslog output.          Args:             address: Syslog server address, Builder for creating LoggingConfig instances with fluent API.      This builder, Configure console output format.          Args:             show_time: Show time, Configure optional time-window file rotation.          Args:             schedul, Build the LoggingConfig instance.          Returns:             A validated Logg, Initialize builder with sensible defaults. (+15 more)

### Community 6 - "Configuration Builder"
Cohesion: 0.14
Nodes (14): C4 Component Level: System Overview, Component Interactions, Component Relationships, Component Summary Table, Core Logging Library Interactions, Core Technologies, Data Flow, Dependency Graph (+6 more)

### Community 7 - "Logger Naming Consistency Tests"
Cohesion: 0.04
Nodes (49): 1. Python Package Container, 2. Test Suite Container, 3. Documentation Site Container, C4 Container Level: arlogi System Deployment, Command Line Interface, Command Line Interface, Components, Components (+41 more)

### Community 8 - "Deprecation Warning Tests"
Cohesion: 0.04
Nodes (48): API Documentation Generation, Automated Validation, Build Artifacts, C4 Component Level: Documentation System, Code Elements, Command Line Interface (CLI), Component Diagram, Component Interactions (+40 more)

### Community 9 - "Trace Logger Implementation"
Cohesion: 0.25
Nodes (5): Test that handlers are properly closed and removed., Test that _clear_and_add_handlers closes existing handlers., Test that get_json_logger closes previous handlers before adding new ones., Test that get_syslog_logger closes previous handlers before adding new ones., TestHandlerCleanup

### Community 10 - "SRP Compliance Tests"
Cohesion: 0.05
Nodes (44): Advanced API, Advanced Module Configuration, Arlogi API Reference, `ArlogiSyslogHandler`, Caller Attribution, `cleanup_json_logger(name)`, `cleanup_syslog_logger(name)`, `ColoredConsoleHandler` (+36 more)

### Community 11 - "Type Safety Tests"
Cohesion: 0.05
Nodes (44): 1. Factory Pattern, 2. Builder Pattern, 3. Strategy Pattern, 4. Protocol Pattern, 5. Singleton Pattern, 6. Template Method Pattern, Advanced Features, Architecture Notes (+36 more)

### Community 12 - "TRACE Level Validation Tests"
Cohesion: 0.13
Nodes (34): Factory for creating logger instances with caller attribution support.  This mod, Log a message with TRACE level (below DEBUG).          Args:             msg: Th, Log a warning message., Log an error message., Log a critical message., Log an exception with traceback., Log a message at the specified level., Factory for creating and configuring logger instances.      This factory manages (+26 more)

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
Cohesion: 0.36
Nodes (8): datetime, Logging handlers for arlogi.  This module provides custom logging handlers inclu, _emit(), test_emit_rotates_on_period_boundary(), test_period_key_generation(), test_retention_prunes_old_rotated_files(), test_rotate_now_is_noop_for_empty_file(), test_rotate_now_moves_to_suffixed_file()

### Community 17 - "Feature Tests"
Cohesion: 0.07
Nodes (29): C4 Component Level: Test Suite, `caplog` Fixture, `capsys` Fixture, Code Elements, Component Diagram, Components Tested, Core Functionality Testing, Core Test Functions (+21 more)

### Community 18 - "Core Logging Tests"
Cohesion: 0.08
Nodes (25): C4 Code Level: tests, Code Elements, Dependencies, `do_work()` function in tests/example/worker.py, External Dependencies, Integration Examples, Internal Dependencies, Key Test Categories (+17 more)

### Community 19 - "Example Applications"
Cohesion: 0.18
Nodes (6): Set up arlogi logging with the specified configuration.      This is a convenien, setup_logging(), test_module_specific_levels(), Test to verify relative path functionality in logger output., test_relative_path_logging(), test_setup_logging_accepts_rotation_options()

### Community 20 - "Path Handling Tests"
Cohesion: 0.17
Nodes (3): get_json_logger(), Get a dedicated JSON-only logger.      Args:         name: Logger name suffix, test_test_mode_detection()

### Community 21 - "Level Validation Helper"
Cohesion: 0.03
Nodes (58): Communities (70 Total, 12 Thin Omitted), Community 0 - "Core Factory & Handler Infrastructure", Community 10 - "SRP Compliance Tests", Community 11 - "Type Safety Tests", Community 12 - "TRACE Level Validation Tests", Community 13 - "Backward Compatibility Tests", Community 14 - "Documentation Generation", Community 15 - "Parameter Validation Tests" (+50 more)

### Community 22 - "Global Level Helper"
Cohesion: 0.27
Nodes (6): LogRecord, Any, Override render method to show relative paths from project root.          Args:, Get level text as a single character with styling.          Args:             re, Render message text with level-specific styling.          Args:             reco, Format log record as JSON.          Args:             record: The log record to

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
Cohesion: 0.25
Nodes (5): Tests that detect actual resource leaks (requires psutil)., Skip all tests in this class if psutil is not available., Test that creating/destroying loggers doesn't leak file descriptors., Test that creating/destroying file loggers doesn't leak file descriptors., TestResourceLeakDetection

### Community 27 - "C4 Architecture Documentation"
Cohesion: 0.09
Nodes (22): About the C4 Model, Additional Resources, API Specifications, Architecture Levels, C4 Architecture Documentation, Code-Level Documents, Component Documentation, Contributing (+14 more)

### Community 28 - ".__post_init__"
Cohesion: 0.40
Nodes (3): Validate configuration after initialization., Validate a log level value.          Args:             level: Log level as int o, _validate_level()

### Community 29 - "Integration with Other Libraries"
Cohesion: 0.09
Nodes (21): Advanced Configuration, `arlogi` - Advanced Logging Library, Basic Setup, Centralized Logging Setup, Color Schemes, Dedicated Loggers, Default INFO when `arlogi` is not imported, Development (+13 more)

### Community 30 - "File Logging Rotation Design"
Cohesion: 0.10
Nodes (19): 10. Test Plan, 11. Rollout Notes, 12. Open Questions, 1. Objective, 2. Requirements (Validated), 3. Non-Goals, 4. High-Level Architecture, 5.1 Configuration Surface (+11 more)

### Community 31 - "C4 Code Level: docs/scripts"
Cohesion: 0.11
Nodes (19): `build_pub.sh`, C4 Code Level: docs/scripts, Code Elements, `create_markdown(md_filepath: Path, module_path: str, classes: list, functions: list)`, `create_nav_menu_yaml(nav_items: list[Path])`, Dependencies, External Dependencies, `extract_classes_and_functions(filepath: Path) -> tuple[list[str], list[str]]` (+11 more)

### Community 32 - "C4 Code Level: API Reference Documentation"
Cohesion: 0.12
Nodes (16): C4 Code Level: API Reference Documentation, Code Elements, Configuration Dependencies, Cross-Reference Relationships, Dependencies, Documentation Structure Relationship, Generated Documentation Files, Integration Points (+8 more)

### Community 33 - "2. Work Breakdown Structure"
Cohesion: 0.15
Nodes (12): 1. Scope and Guardrails, 2. Work Breakdown Structure, 3. Suggested Implementation Order, 4. Risk Register and Mitigations, 5. Definition of Done, Implementation Plan: Optional File Logging Rotation, Phase A - Config and API Contracts, Phase B - Handler Factory Wiring (+4 more)

### Community 34 - "C4 Code Level: subdir"
Cohesion: 0.25
Nodes (5): Test creating many loggers concurrently with different names., Test concurrent JSON logger creation., Test concurrent logger creation with different levels., Test concurrent logger creation., TestConcurrentLoggerCreation

### Community 35 - "Testing"
Cohesion: 0.18
Nodes (11): Coverage Requirements, Feature Tests, Integration Tests, Running Tests, Test Categories, Test Fixtures, Test Mode Detection, Test Structure (+3 more)

### Community 36 - "factory.py"
Cohesion: 0.26
Nodes (11): _apply_configuration(), _clear_and_add_handlers(), _configure_module_levels(), _configure_root_logger(), get_global_logger(), get_logger(), _initialize_trace_level(), is_test_mode() (+3 more)

### Community 37 - "._compute_period_key"
Cohesion: 0.05
Nodes (44): Advanced API, Advanced Module Configuration, Arlogi API Reference, `ArlogiSyslogHandler`, Caller Attribution, `cleanup_json_logger(name)`, `cleanup_syslog_logger(name)`, `ColoredConsoleHandler` (+36 more)

### Community 38 - "test_thread_safety.py"
Cohesion: 0.33
Nodes (4): Test thread safety of TRACE level registration., Test that concurrent TRACE registration is safe., Test that multiple TRACE registrations are safe., TestTraceRegistrationThreadSafety

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
Cohesion: 0.25
Nodes (4): Initialize the JSON stream handler.          Args:             stream: The strea, Initialize the colored console handler.          Args:             show_time: Wh, Initialize the syslog handler.          Args:             address: Syslog server, Find the project root by looking for common indicators.          Searches upward

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
Cohesion: 0.57
Nodes (6): create_console(), create_handlers(), create_json_file(), create_json_handler(), create_json_stream(), create_syslog()

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
Cohesion: 0.09
Nodes (16): Handler, LoggingConfig, Determine if console output should be shown.          Returns:             True, Determine if JSON output is configured.          Returns:             True if JS, Resolve a module level to an integer.          Args:             name: Module na, Immutable configuration for arlogi logging setup.      Attributes:         level, Get the global level as an integer.          Returns:             The resolved l, Create a syslog handler.          Args:             config: Logging configuratio (+8 more)

### Community 71 - "LoggerProtocol"
Cohesion: 0.14
Nodes (7): Protocol, get_syslog_logger(), Get a logger that only outputs to Syslog, bypassing root handlers.          Args, Get a dedicated syslog-only logger.      Args:         name: Logger name suffix, LoggerProtocol, Any, Protocol defining the interface for the arlogi logger.

### Community 73 - "Configuration Guide"
Cohesion: 0.14
Nodes (14): Advanced Handler Configuration, Conditional Logging, Configuration Guide, Configuration Validation, Custom Formatters, FILE: docs/CALLER_ATTRIBUTION_EXAMPLES.md, Filtering Logs, High-Performance Configuration (+6 more)

### Community 74 - "TestFactoryEdgeCases"
Cohesion: 0.21
Nodes (5): Rotate JSON file handlers attached to the named JSON logger.      Args:, rotate_json_logger(), Test LoggerFactory helper methods and edge cases., TestFactoryEdgeCases, test_rotate_json_logger_helper()

### Community 75 - "Caller Attribution Examples"
Cohesion: 0.15
Nodes (12): Arlogi User Guides and API Reference, Best Practices, Caller Attribution Examples, Efficient Caller Attribution, FILE: docs/DEVELOPER_GUIDE.md, FILE: docs/USER_GUIDE.md, Modern Setup, Performance Considerations (+4 more)

### Community 76 - "Graph Report - Arlogi (2026-07-25)"
Cohesion: 0.15
Nodes (12): Arlogi Codebase Knowledge Graph (Graphify), Community Hubs (Navigation), Corpus Check, FILE: graphify-out/GRAPH_REPORT.md, God Nodes (Most cOnnected - yOur cOre aBstractions), Graph Freshness, Graph Report - Arlogi (2026-07-25), Import Cycles (+4 more)

### Community 77 - "test_coverage_boost.py"
Cohesion: 0.21
Nodes (5): Register the TRACE level with the standard logging module.      Thread-safe: Use, register_trace_level(), Additional unit tests to achieve high test coverage across arlogi modules., Test TRACE level registration and execution covering all 8 branches in levels.py, TestLevelsCoverage

### Community 78 - "Arlogi Developer Guide"
Cohesion: 0.17
Nodes (12): Architecture Decisions, Arlogi Developer Guide, Continuous Integration, Current Architecture, Decision Records, FILE: docs/API_REFERENCE.md, Getting Help, GitHub Actions Workflow (+4 more)

### Community 80 - "Arlogi Library Documentation"
Cohesion: 0.18
Nodes (11): Additional Resources, Arlogi Library Documentation, Documentation Guide, FILE: docs/ARCHITECTURE.md, Getting Started, Key Features, License, Performance Notes (+3 more)

### Community 81 - "Testing"
Cohesion: 0.18
Nodes (11): Coverage Requirements, Feature Tests, Integration Tests, Running Tests, Test Categories, Test Fixtures, Test Mode Detection, Test Structure (+3 more)

### Community 82 - "C4 Code Level: subdir"
Cohesion: 0.20
Nodes (7): C4 Code Level: subdir, Dependencies, External Dependencies, Internal Dependencies, Notes, Overview, Relationships

### Community 83 - "Arlogi Core Source Code"
Cohesion: 0.20
Nodes (9): Arlogi Core Source Code, FILE: src/arlogi/config_builder.py, FILE: src/arlogi/config.py, FILE: src/arlogi/factory.py, FILE: src/arlogi/handler_factory.py, FILE: src/arlogi/handlers.py, FILE: src/arlogi/__init__.py, FILE: src/arlogi/levels.py (+1 more)

### Community 84 - "._compute_period_key"
Cohesion: 0.22
Nodes (5): Initialize the JSON file handler.          Args:             filename: Path to t, Get current local datetime.          This indirection keeps schedule checks test, Compute the period key for the configured schedule., Return the new period key when an emit should trigger rotation., Emit a log record, rotating first when schedule boundary changed.

### Community 85 - "`arlogi` - Advanced Logging Library"
Cohesion: 0.22
Nodes (9): `arlogi` - Advanced Logging Library, Development, Features, FILE: CLAUDE.md, FILE: docs/index.md, FILE: pyproject.toml, Graphify, Installation (+1 more)

### Community 86 - "Code Quality"
Cohesion: 0.22
Nodes (9): Code Quality, Code Style Guidelines, Complexity Limits, Docstring Format, Linting with Ruff, Naming Conventions, Pre-commit Hooks, Ruff Configuration (+1 more)

### Community 87 - "Publishing Workflow Design (Commitizen, GitHub Releases, PyPI)"
Cohesion: 0.22
Nodes (8): 1. Local Tooling & Configuration (`pyproject.toml`), 2. GitHub Actions Release Workflow (`.github/workflows/publish.yml`), 3. Developer Workflow, Architecture & Workflows, Goals, Overview, Publishing Workflow Design (Commitizen, GitHub Releases, PyPI), Verification Plan

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
Cohesion: 0.29
Nodes (6): Global Constraints, Publishing Workflow Implementation Plan, Task 1: Configure Commitizen in pyproject.toml, Task 2: Create GitHub Actions Publishing Workflow, Task 3: Update Project Documentation, Task 4: Local Verification of Build and Bump Dry-Run

### Community 96 - "Real-World Application Examples"
Cohesion: 0.33
Nodes (6): Background Job Processing, Class Method Attribution, Database Operations, Error Handling and Exception Tracking, Real-World Application Examples, Web API Handler

### Community 97 - "Code Elements"
Cohesion: 0.40
Nodes (5): Classes/Modules, Code Elements, Functions/Methods, `main()` (implicit main execution), `test_nested.py` Module

### Community 98 - "Cross-Component Concerns"
Cohesion: 0.40
Nodes (5): Cross-Component Concerns, Development Workflow, Documentation Synchronization, Quality Assurance, Release Coordination

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
Cohesion: 0.50
Nodes (3): cleanup_json_logger(), Clean up handlers for a JSON logger to free resources.          This method clos, Clean up handlers for a JSON logger to free resources.      This function closes

### Community 119 - "cleanup_syslog_logger"
Cohesion: 0.50
Nodes (3): cleanup_syslog_logger(), Clean up handlers for a syslog logger to free resources.          Args:, Clean up handlers for a syslog logger to free resources.      Args:         name

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
Cohesion: 0.67
Nodes (3): Docstring Standards, Documentation, Updating Documentation

## Knowledge Gaps
- **844 isolated node(s):** `arlogi`, `graphify`, `Release & Publishing`, `Features`, `Installation` (+839 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Arlogi API Reference` connect `SRP Compliance Tests` to `C4-Documentation/README.md`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `Arlogi User Guide` connect `Arlogi User Guide` to `C4-Documentation/README.md`, `Configuration`, `Troubleshooting`, `Common Patterns`, `Installation`, `Advanced Usage`, `Basic Usage`, `Caller Attribution`, `Output Handlers`, `Best Practices`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `C4 Component Level: Documentation System` connect `Deprecation Warning Tests` to `C4-Documentation/README.md`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 81 inferred relationships involving `JSONFileHandler` (e.g. with `LoggerFactory` and `TraceLogger`) actually correct?**
  _`JSONFileHandler` has 81 INFERRED edges - model-reasoned connections that need verification._
- **Are the 63 inferred relationships involving `LoggingConfig` (e.g. with `LoggingConfigBuilder` and `Builder pattern for LoggingConfig construction.  This module provides a fluent b`) actually correct?**
  _`LoggingConfig` has 63 INFERRED edges - model-reasoned connections that need verification._
- **Are the 60 inferred relationships involving `LoggerFactory` (e.g. with `LoggingConfig` and `HandlerFactory`) actually correct?**
  _`LoggerFactory` has 60 INFERRED edges - model-reasoned connections that need verification._
- **Are the 53 inferred relationships involving `JSONHandler` (e.g. with `LoggerFactory` and `TraceLogger`) actually correct?**
  _`JSONHandler` has 53 INFERRED edges - model-reasoned connections that need verification._