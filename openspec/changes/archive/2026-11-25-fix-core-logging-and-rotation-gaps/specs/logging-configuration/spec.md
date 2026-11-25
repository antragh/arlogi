# Spec Delta

## MODIFIED Requirements

### Requirement: Strict log level validation and resolution

The configuration system and `get_logger(name, level=...)` SHALL accept global, per-module, and per-logger log levels only as `int` (excluding `bool`) or recognized level-name strings (case-insensitive standard logging level names plus `"TRACE"`), and SHALL resolve `"TRACE"` to numeric level `5` even before global `TRACE` registration occurs. `get_logger()` SHALL additionally accept a case-insensitive `"NOTSET"` string, resolving it to `0`.

#### Scenario: Resolving TRACE level before logger initialization

- **WHEN** a configuration instance is constructed with `level="TRACE"` or `module_levels={"app.db": "trace"}` in a fresh process prior to logger setup
- **THEN** validation succeeds and level resolution returns integer `5` without raising `AttributeError`

#### Scenario: Rejecting boolean values as log levels

- **WHEN** a configuration instance is constructed with `level=True`, `level=False`, or `module_levels={"app": True}`
- **THEN** construction MUST raise `ValueError`

#### Scenario: Rejecting non-level stdlib logging attributes

- **WHEN** a configuration instance is constructed with a non-level attribute name from Python's `logging` module (such as `"BASIC_FORMAT"` or `"_STYLES"`) or an unknown string
- **THEN** construction MUST raise `ValueError` listing only valid level names

#### Scenario: Case-insensitive level names in get_logger

- **WHEN** a caller invokes `get_logger("app.worker", level="trace")` or `get_logger("app.worker", level="debug")`
- **THEN** the call succeeds and the logger's level is `5` or `10` respectively

#### Scenario: Rejecting boolean levels in get_logger

- **WHEN** a caller invokes `get_logger("app.worker", level=True)` or `get_logger("app.worker", level=False)`
- **THEN** the call MUST raise `ValueError` and the logger's existing level is unchanged

#### Scenario: Resetting a logger level to NOTSET via get_logger

- **WHEN** a caller invokes `get_logger("app.worker", level="NOTSET")` or `get_logger("app.worker", level=logging.NOTSET)`
- **THEN** the logger's level is `0`

### Requirement: Fluent configuration builder parity and console-only override

The fluent configuration builder SHALL produce a default configuration equal to a default configuration object and SHALL clear any previously configured JSON file path and JSON file base directory when `with_json_console_only()` is called.

#### Scenario: Default builder output matches default configuration

- **WHEN** a caller builds a configuration from a newly instantiated builder without overrides
- **THEN** the resulting configuration equals a default-constructed configuration object (including `level == 20`)

#### Scenario: Overriding JSON file output with console-only JSON

- **WHEN** a caller chains `.with_json_file("logs/app.jsonl").with_json_console_only().build()`
- **THEN** the built configuration has `json_file_name=None`, `json_file_only=True`, and `show_console=False`, routing JSON output to `stderr` rather than a file

#### Scenario: Console-only override clears the JSON base directory

- **WHEN** a caller chains `.with_json_file("a.jsonl").with_json_base_dir("/tmp").with_json_console_only().build()`
- **THEN** the built configuration has `json_file_base_dir=None`

### Requirement: Public configuration application and root package exports

The library SHALL export `LoggingConfigBuilder` from the top-level `arlogi` package and SHALL provide thread-safe public entrypoints (`setup_logging(config=...)`, `LoggerFactory.setup(config=...)`, and `LoggerFactory.apply_config(config)`) to apply a pre-built `LoggingConfig` without calling private methods. Any explicitly passed configuration keyword combined with `config` MUST be rejected regardless of whether its value equals the parameter default.

#### Scenario: Applying a pre-built configuration via setup_logging

- **WHEN** a caller passes `setup_logging(config=built_config)` with no conflicting keyword overrides
- **THEN** the library applies `built_config` under initialization lock protection

#### Scenario: Rejecting simultaneous config object and keyword overrides

- **WHEN** a caller invokes `setup_logging(config=built_config, level="DEBUG")` or `LoggerFactory.setup(config=built_config, use_syslog=True)` with both `config` and explicit keyword overrides
- **THEN** the call MUST raise `ValueError`

#### Scenario: Rejecting default-equal explicit overrides combined with config

- **WHEN** `cfg = LoggingConfigBuilder().with_level("DEBUG").with_syslog().with_json_file("app.jsonl", console_also=False).build()` and a caller invokes `setup_logging(config=cfg, level=logging.INFO)`, `setup_logging(config=cfg, use_syslog=False)`, `setup_logging(config=cfg, json_file_name=None)`, or `LoggerFactory.setup(config=cfg, json_file_base_dir=None)`
- **THEN** each call MUST raise `ValueError` naming the overridden parameter, and the previously applied configuration remains in effect

#### Scenario: Keyword-only setup without config keeps existing defaults

- **WHEN** a caller invokes `setup_logging()` or `setup_logging(level="DEBUG")` without `config`
- **THEN** omitted parameters take the `LoggingConfig` defaults and the resulting configuration matches the previous behavior

## ADDED Requirements

### Requirement: Non-empty JSON file name validation

Wherever a JSON file name is accepted (`LoggingConfig`, the fluent builder, `setup_logging()`, and `get_json_logger()`), a value that is not `None` MUST be a non-empty, non-whitespace `str`, otherwise `ValueError` SHALL be raised. JSON file handler selection SHALL depend only on whether the name is `None`, never on its truthiness, so an invalid name never silently falls back to console or `stderr` output.

#### Scenario: Rejecting an empty file name in configuration

- **WHEN** a caller constructs `LoggingConfig(json_file_name="")`, `LoggingConfig(json_file_name="   ", json_file_base_dir="/tmp")`, `LoggingConfigBuilder().with_json_file("").build()`, or calls `setup_logging(json_file_name="", json_file_base_dir="/var/log/app")`
- **THEN** each call MUST raise `ValueError` before any handler is created

#### Scenario: Rejecting a non-string file name in configuration

- **WHEN** a caller constructs `LoggingConfig(json_file_name=123)`
- **THEN** construction MUST raise `ValueError`

#### Scenario: Rejecting an empty file name for a dedicated JSON logger

- **WHEN** a caller invokes `get_json_logger("audit", "")` or `get_json_logger("audit", "", base_dir="/tmp")`
- **THEN** the call MUST raise `ValueError` stating the file name must be non-empty, and no `stderr` JSON handler is attached

#### Scenario: Omitted file name still selects stderr JSON output

- **WHEN** a caller invokes `get_json_logger("audit")` or applies `LoggingConfig(json_file_only=True)`
- **THEN** a stream JSON handler writing to `stderr` is attached as before
