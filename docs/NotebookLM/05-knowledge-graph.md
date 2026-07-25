# Arlogi Codebase Knowledge Graph (Graphify)

---

## FILE: graphify-out/GRAPH_REPORT.md

# Graph Report - Arlogi (2026-07-25)

## Corpus Check

- 51 files · ~49,262 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary

- 1082 nodes · 1792 edges · 70 communities (58 shown, 12 thin omitted)
- Extraction: 71% EXTRACTED · 29% INFERRED · 0% AMBIGUOUS · INFERRED: 511 edges (avg confidence: 0.51)
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

## God Nodes (Most cOnnected - yOur cOre aBstractions)

1. `JSONFileHandler` - 126 edges
2. `LoggingConfig` - 113 edges
3. `JSONHandler` - 83 edges
4. `LoggerFactory` - 80 edges
5. `LoggerProtocol` - 58 edges
6. `ColoredConsoleHandler` - 52 edges
7. `ArlogiSyslogHandler` - 49 edges
8. `HandlerFactory` - 48 edges
9. `JSONFormatter` - 38 edges
10. `TraceLogger` - 18 edges

## Surprising Connections (You pRobably dIdn't kNow tHese)

- `test_module_specific_levels()` --calls--> `setup_logging()`  [INFERRED]
  tests/test_features.py → src/arlogi/factory.py
- `test_setup_logging_accepts_rotation_options()` --calls--> `setup_logging()`  [INFERRED]
  tests/test_rotation_config.py → src/arlogi/factory.py
- `main()` --calls--> `LoggingConfig`  [INFERRED]
  tests/example/example.py → src/arlogi/config.py
- `Resource management tests for arlogi.  This module tests that handlers properly` --uses--> `LoggingConfig`  [INFERRED]
  tests/test_resource_management.py → src/arlogi/config.py
- `Test that JSONHandler doesn't close system streams.` --uses--> `LoggingConfig`  [INFERRED]
  tests/test_resource_management.py → src/arlogi/config.py

## Import Cycles

- None detected.

## Communities (70 Total, 12 Thin Omitted)

### Community 0 - "Core Factory & Handler Infrastructure"

Cohesion: 0.14

Nodes (15): JSONFormatter, JSON formatter for structured log output.      Outputs log records as JSON with, Resource management tests for arlogi.  This module tests that handlers properly, Test that JSONHandler doesn't close system streams., Test JSONFormatter's error handling., Test that JSONFormatter handles objects that can't be serialized., Test that JSONFormatter works for normal cases., Test that multiple configuration changes don't leak resources. (+7 more)

### Community 1 - "Handler Implementation & Resource Management"

Cohesion: 0.22

Nodes (5): get_default_level(), is_test_mode(), Logging configuration dataclass for type-safe setup.  This module provides a str, Detect if running under a test runner.      Checks for pytest, unittest, or the, Get the default log level based on the current environment.      Returns DEBUG i

### Community 2 - "Thread Safety Tests"

Cohesion: 0.18

Nodes (8): LoggerFactory, Test concurrent directory creation in JSON file handlers., Test concurrent JSON file handlers creating the same directory., Stress tests with high concurrency., Stress test with high concurrency., Test rapid initialization and logging cycles., TestConcurrentDirectoryCreation, TestStressTest

### Community 3 - "Configuration Management"

Cohesion: 0.09

Nodes (13): Close the handler and the stream if we own it.          Only closes custom strea, Initialize the JSON file handler.          Args:             filename: Path to t, Get current local datetime.          This indirection keeps schedule checks test, Compute the period key for the configured schedule., Build target path for a rotated file., Return a unique rotated path by appending numeric suffixes when needed., Prune old rotated files based on retention count., Return the new period key when an emit should trigger rotation. (+5 more)

### Community 4 - "Integration Tests"

Cohesion: 0.17

Nodes (12): C4 Code Level: tests/example, Code Elements, Data Flow Diagram, Dependencies, External Dependencies, Functions/Methods, Internal Dependencies, Module Relationship Diagram (+4 more)

### Community 5 - "Builder Pattern Tests"

Cohesion: 0.06

Nodes (22): LoggingConfigBuilder, Builder pattern for LoggingConfig construction.  This module provides a fluent b, Enable syslog output.          Args:             address: Syslog server address, Builder for creating LoggingConfig instances with fluent API.      This builder, Configure console output format.          Args:             show_time: Show time, Configure optional time-window file rotation.          Args:             schedul, Build the LoggingConfig instance.          Returns:             A validated Logg, Initialize builder with sensible defaults. (+14 more)

### Community 6 - "Configuration Builder"

Cohesion: 0.06

Nodes (35): C4 Code Level: subdir, Classes/Modules, Code Elements, Dependencies, External Dependencies, Functions/Methods, Internal Dependencies, `main()` (implicit main execution) (+27 more)

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

Cohesion: 0.07

Nodes (59): Handler, Protocol, LoggingConfig, Get the global level as an integer.          Returns:             The resolved l, Determine if console output should be shown.          Returns:             True, Determine if JSON output is configured.          Returns:             True if JS, Resolve a module level to an integer.          Args:             name: Module na, Immutable configuration for arlogi logging setup.      Attributes:         level (+51 more)

### Community 13 - "Backward Compatibility Tests"

Cohesion: 0.05

Nodes (42): Application Developer, Application Developer: Advanced Configuration Journey, Application Developer: Basic Logging Journey, Application Developer: Dedicated Logger Journey, Application Developer: JSON Logging Journey, Application Developer: Module Configuration Journey, Application Developer: TRACE Logging Journey, C4 Context Level: System Context (+34 more)

### Community 14 - "Documentation Generation"

Cohesion: 0.05

Nodes (41): Advanced Handler Configuration, Application Structure Examples, Basic Setup, CLI Application Configuration, Complete Production Setup, Conditional Logging, Configuration File Support, Configuration from Environment Variables (+33 more)

### Community 15 - "Parameter Validation Tests"

Cohesion: 0.05

Nodes (38): Adding Custom Handlers, Adding Custom Log Levels, Architecture Diagrams, Arlogi Architecture Documentation, Builder Pattern, C4 Container Diagram, C4 Context Diagram, Caller Attribution Overhead (+30 more)

### Community 16 - "Critical Bug Fix Tests"

Cohesion: 0.23

Nodes (14): datetime, JSONFileHandler, Logging handlers for arlogi.  This module provides custom logging handlers inclu, A logging handler that outputs log records as JSON to a file.      Automatically, _emit(), test_emit_rotates_on_period_boundary(), test_period_key_generation(), test_retention_prunes_old_rotated_files() (+6 more)

### Community 17 - "Feature Tests"

Cohesion: 0.07

Nodes (29): C4 Component Level: Test Suite, `caplog` Fixture, `capsys` Fixture, Code Elements, Component Diagram, Components Tested, Core Functionality Testing, Core Test Functions (+21 more)

### Community 18 - "Core Logging Tests"

Cohesion: 0.08

Nodes (25): C4 Code Level: tests, Code Elements, Dependencies, `do_work()` function in tests/example/worker.py, External Dependencies, Integration Examples, Internal Dependencies, Key Test Categories (+17 more)

### Community 22 - "Global Level Helper"

Cohesion: 0.18

Nodes (8): LogRecord, Any, Override render method to show relative paths from project root.          Args:, Get level text as a single character with styling.          Args:             re, Render message text with level-specific styling.          Args:             reco, Format log record as JSON.          Args:             record: The log record to, Initialize the JSON stream handler.          Args:             stream: The strea, Initialize the syslog handler.          Args:             address: Syslog server

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

Cohesion: 0.10

Nodes (20): Advanced Configuration, `arlogi` - Advanced Logging Library, Basic Setup, Color Schemes, Console Styling, Dedicated Loggers, Default INFO when `arlogi` is not imported, Development (+12 more)

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

### Community 34 - "C4 Code Level: sUbdir"

Cohesion: 0.25

Nodes (5): Test creating many loggers concurrently with different names., Test concurrent JSON logger creation., Test concurrent logger creation with different levels., Test concurrent logger creation., TestConcurrentLoggerCreation

### Community 35 - "Testing"

Cohesion: 0.18

Nodes (11): Coverage Requirements, Feature Tests, Integration Tests, Running Tests, Test Categories, Test Fixtures, Test Mode Detection, Test Structure (+3 more)

### Community 36 - "factory.py"

Cohesion: 0.16

Nodes (14): _apply_configuration(), cleanup_json_logger(), cleanup_syslog_logger(), _clear_and_add_handlers(), _configure_module_levels(), _configure_root_logger(), get_global_logger(), get_logger() (+6 more)

### Community 37 - "._compute_period_key"

Cohesion: 0.25

Nodes (5): Test concurrent logging operations., Test concurrent logging to the same logger instance., Test concurrent logging with extra fields., Test concurrent logging at different levels., TestConcurrentLogging

### Community 38 - "test_thread_safety.py"

Cohesion: 0.18

Nodes (7): Register the TRACE level with the standard logging module.      Thread-safe: Use, register_trace_level(), Thread safety tests for arlogi.  This module tests that the library is thread-sa, Test thread safety of TRACE level registration., Test that concurrent TRACE registration is safe., Test that multiple TRACE registrations are safe., TestTraceRegistrationThreadSafety

### Community 39 - "Code Quality"

Cohesion: 0.22

Nodes (9): Code Quality, Code Style Guidelines, Complexity Limits, Docstring Format, Linting with Ruff, Naming Conventions, Pre-commit Hooks, Ruff Configuration (+1 more)

### Community 40 - "Arlogi Developer Guide"

Cohesion: 0.25

Nodes (8): Arlogi Developer Guide, Continuous Integration, Getting Help, GitHub Actions Workflow, License, Module Responsibilities, Project Structure, Table of Contents

### Community 41 - "Arlogi User Guide"

Cohesion: 0.25

Nodes (7): Arlogi User Guide, Getting Help, License, Minimal Setup, Performance Tips, Quick Start, Table of Contents

### Community 42 - ".__init__"

Cohesion: 0.23

Nodes (9): RichHandler, ColoredConsoleHandler, A logging handler that uses rich for colored console output.      Features:, Initialize the colored console handler.          Args:             show_time: Wh, Find the project root by looking for common indicators.          Searches upward, Test ColoredConsoleHandler's project root caching., Test that project root detection is cached., Test that cache persists across multiple handler creations. (+1 more)

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

Cohesion: 0.25

Nodes (5): Test concurrent initialization of the logging system., Test that concurrent setup() calls don't duplicate handlers., Test that concurrent get_logger() calls initialize successfully., Test that concurrent get_global_logger() calls are thread-safe., TestConcurrentInitialization

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

## Knowledge Gaps

- **528 isolated node(s):** `arlogi`, `graphify`, `Features`, `Basic Setup`, `Module-Specific Levels` (+523 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** – run `graphify query` to explore isolated nodes.

## Suggested Questions

_Questions this graph is uniquely positioned to answer:_

- **Why does `C4 Container Level: arlogi System Deployment` connect `Logger Naming Consistency Tests` to `Configuration Builder`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Why does `C4 Context Level: System Context` connect `Backward Compatibility Tests` to `Configuration Builder`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `Arlogi Developer Guide` connect `Arlogi Developer Guide` to `Testing`, `Configuration Builder`, `Code Quality`, `Contributing`, `Development Setup`, `Performance Guidelines`, `Release Process`, `Architecture Decisions`, `Documentation`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 102 inferred relationships involving `JSONFileHandler` (e.g. with `LoggerFactory` and `TraceLogger`) actually correct?**
  _`JSONFileHandler` has 102 INFERRED edges - model-reasoned connections that need verification._
- **Are the 86 inferred relationships involving `LoggingConfig` (e.g. with `LoggingConfigBuilder` and `Builder pattern for LoggingConfig construction.  This module provides a fluent b`) actually correct?**
  _`LoggingConfig` has 86 INFERRED edges - model-reasoned connections that need verification._
- **Are the 75 inferred relationships involving `JSONHandler` (e.g. with `LoggerFactory` and `TraceLogger`) actually correct?**
  _`JSONHandler` has 75 INFERRED edges - model-reasoned connections that need verification._
- **Are the 64 inferred relationships involving `LoggerFactory` (e.g. with `LoggingConfig` and `HandlerFactory`) actually correct?**
  _`LoggerFactory` has 64 INFERRED edges - model-reasoned connections that need verification._
