# Spec Delta: logging-configuration

## MODIFIED Requirements

### Requirement: Rotation parameter validation

The configuration system SHALL validate `rotate_schedule` as a `str` matching `{"hour", "day", "week", "month"}` when set (raising `ValueError` with `"Invalid rotate_schedule"` for non-string, unhashable, or unsupported values) and SHALL require `rotate_retention_count` to be a non-boolean integer greater than or equal to `1` when provided.

#### Scenario: Rejecting invalid retention count types and bounds

- **WHEN** a configuration instance is constructed with `rotate_retention_count=0`, `rotate_retention_count=-1`, `rotate_retention_count=True`, or `rotate_retention_count="7"`
- **THEN** construction MUST raise `ValueError`

#### Scenario: Rejecting unhashable or non-string rotate_schedule

- **WHEN** a configuration instance is constructed with `rotate_schedule=["day"]`, `rotate_schedule={"schedule": "day"}`, or `rotate_schedule=123`
- **THEN** construction MUST raise `ValueError` (never `TypeError`)

### Requirement: Non-empty JSON file name validation

Wherever a JSON file name or base directory is accepted (`LoggingConfig`, the fluent builder, `setup_logging()`, `get_json_logger()`, and `JSONFileHandler`), a `json_file_name` that is not `None` MUST be a non-empty, non-whitespace `str` free of NUL bytes, and a `json_file_base_dir` / `base_dir` that is not `None` MUST be a `str` or `Path` (excluding `bool` and other non-path types) whose string form is non-empty after stripping whitespace and free of NUL bytes; otherwise `ValueError` SHALL be raised before any handler or filesystem side effect occurs. JSON file handler selection SHALL depend only on whether the name is `None`, never on its truthiness, so an invalid name never silently falls back to console or `stderr` output.

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

#### Scenario: Rejecting invalid json_file_base_dir values

- **WHEN** a caller constructs `LoggingConfig(json_file_name="app.jsonl", json_file_base_dir=v)`, `LoggingConfigBuilder().with_json_file("app.jsonl").with_json_base_dir(v).build()`, or calls `get_json_logger("audit", "app.jsonl", base_dir=v)` with `v` in `("", "   ", 123, True, "\x00")`
- **THEN** each call MUST raise `ValueError` before creating any directory or file, and containment MUST NOT silently anchor to `os.getcwd()`
