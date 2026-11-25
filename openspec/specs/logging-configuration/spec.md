# logging-configuration Specification

## Purpose
Defines immutable logging configuration validation, fluent builder construction, spoof-resistant test-mode detection, and public configuration application contracts for `arlogi`.

## Requirements

### Requirement: Strict log level validation and resolution

The configuration system SHALL accept global and per-module log levels only as `int` (excluding `bool`) or recognized level-name strings (case-insensitive standard logging level names plus `"TRACE"`), and SHALL resolve `"TRACE"` to numeric level `5` even before global `TRACE` registration occurs.

#### Scenario: Resolving TRACE level before logger initialization

- **WHEN** a configuration instance is constructed with `level="TRACE"` or `module_levels={"app.db": "trace"}` in a fresh process prior to logger setup
- **THEN** validation succeeds and level resolution returns integer `5` without raising `AttributeError`

#### Scenario: Rejecting boolean values as log levels

- **WHEN** a configuration instance is constructed with `level=True`, `level=False`, or `module_levels={"app": True}`
- **THEN** construction MUST raise `ValueError`

#### Scenario: Rejecting non-level stdlib logging attributes

- **WHEN** a configuration instance is constructed with a non-level attribute name from Python's `logging` module (such as `"BASIC_FORMAT"` or `"_STYLES"`) or an unknown string
- **THEN** construction MUST raise `ValueError` listing only valid level names

### Requirement: Rotation parameter validation

The configuration system SHALL validate `rotate_schedule` against `{"hour", "day", "week", "month"}` when set and SHALL require `rotate_retention_count` to be a non-boolean integer greater than or equal to `1` when provided.

#### Scenario: Rejecting invalid retention count types and bounds

- **WHEN** a configuration instance is constructed with `rotate_retention_count=0`, `rotate_retention_count=-1`, `rotate_retention_count=True`, or `rotate_retention_count="7"`
- **THEN** construction MUST raise `ValueError`

### Requirement: Fluent configuration builder parity and console-only override

The fluent configuration builder SHALL produce a default configuration equal to a default configuration object and SHALL clear any previously configured JSON file path when `with_json_console_only()` is called.

#### Scenario: Default builder output matches default configuration

- **WHEN** a caller builds a configuration from a newly instantiated builder without overrides
- **THEN** the resulting configuration equals a default-constructed configuration object (including `level == 20`)

#### Scenario: Overriding JSON file output with console-only JSON

- **WHEN** a caller chains `.with_json_file("logs/app.jsonl").with_json_console_only().build()`
- **THEN** the built configuration has `json_file_name=None`, `json_file_only=True`, and `show_console=False`, routing JSON output to `stderr` rather than a file

### Requirement: Public configuration application and root package exports

The library SHALL export `LoggingConfigBuilder` from the top-level `arlogi` package and SHALL provide thread-safe public entrypoints (`setup_logging(config=...)`, `LoggerFactory.setup(config=...)`, and `LoggerFactory.apply_config(config)`) to apply a pre-built `LoggingConfig` without calling private methods.

#### Scenario: Applying a pre-built configuration via setup_logging

- **WHEN** a caller passes `setup_logging(config=built_config)` with no conflicting keyword overrides
- **THEN** the library applies `built_config` under initialization lock protection

#### Scenario: Rejecting simultaneous config object and keyword overrides

- **WHEN** a caller invokes `setup_logging(config=built_config, level="DEBUG")` or `LoggerFactory.setup(config=built_config, use_syslog=True)` with both `config` and explicit keyword overrides
- **THEN** the call MUST raise `ValueError`

### Requirement: Spoof-resistant test-mode detection

Test-mode detection SHALL return `True` exclusively when `pytest` or `unittest` is loaded in `sys.modules` and MUST ignore `PYTEST_CURRENT_TEST` or other environment variables when no test runner module is loaded.

#### Scenario: Ignoring spoofed PYTEST_CURRENT_TEST in production processes

- **WHEN** `PYTEST_CURRENT_TEST` is set in `os.environ` while neither `"pytest"` nor `"unittest"` is present in `sys.modules`
- **THEN** `is_test_mode()` returns `False` and `setup_logging()` attaches configured handlers normally
