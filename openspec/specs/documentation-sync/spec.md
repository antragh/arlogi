# documentation-sync Specification

## Purpose
Defines alignment between published Markdown documentation, MkDocs navigation, and the hardened runtime behavior of `arlogi` and `arlogi.otel`.

## Requirements

### Requirement: Accurate security and configuration documentation

Published documentation (`README.md` and `docs/`) SHALL accurately document `sys.modules`-only `is_test_mode()`, `json_file_base_dir` containment, `LoggingConfigBuilder`, `setup_logging(config=...)`, `LoggerFactory.apply_config()`, valid configuration parameter types/keys, actual JSON envelope fields, and actual `ColoredConsoleHandler` default colors.

#### Scenario: Following documented configuration and security guides without errors

- **WHEN** a user follows the documented `ArlogiSyslogHandler`, `level_styles`, `module_levels`, `caller_depth`, and `json_file_base_dir` examples
- **THEN** every documented parameter name, type, and JSON output key matches the runtime implementation

### Requirement: Complete arlogi.otel documentation and MkDocs reference coverage

`README.md`, `docs/USER_GUIDE.md`, `docs/API_REFERENCE.md`, `docs/ARCHITECTURE.md`, and `mkdocs.yml` SHALL document all 9 public exports of `arlogi.otel` (`setup_tracing`, `shutdown_tracing`, `setup_metrics`, `shutdown_metrics`, `install_log_correlation`, `set_trace_modules`, `traced`, `RotatingJsonlSpanExporter`, `RotatingJsonlMetricExporter`) and its SDK-free lazy import boundary.

#### Scenario: Building MkDocs site with complete arlogi.otel reference

- **WHEN** `uv run mkdocs build --strict` executes
- **THEN** the documentation site builds cleanly with navigation entries for `arlogi.otel` and zero broken links
