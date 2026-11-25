# Spec Delta: logger-lifecycle

## MODIFIED Requirements

### Requirement: Thread-safe dedicated logger replacement, cleanup, and rotation

Dedicated JSON and Syslog logger creation, cleanup, and rotation SHALL serialize mutations to `logger.handlers` under lock protection and MUST detach existing handlers from the logger before closing them so concurrent log emissions never reopen closed file streams or sockets or accumulate duplicate handlers. `get_json_logger()` SHALL validate both `json_file_name` and `base_dir` via shared configuration validators before creating any handler.

#### Scenario: Concurrent same-name dedicated logger reconfiguration and emission

- **WHEN** multiple threads concurrently emit records, reconfigure `get_json_logger("audit", path)`, and call `rotate_json_logger("audit")` or `cleanup_json_logger("audit")`
- **THEN** at most one handler remains attached after reconfiguration and detached handlers do not reopen closed streams or emit `ResourceWarning`

#### Scenario: Concurrent dedicated syslog logger reconfiguration and emission

- **WHEN** worker threads continuously emit records to `get_syslog_logger("sec", address=...)` while another thread concurrently calls `get_syslog_logger("sec", address=...)` or `cleanup_syslog_logger("sec")`
- **THEN** detached `ArlogiSyslogHandler` instances never reopen sockets via `createSocket()` inside `emit()` and emit zero `ResourceWarning`s

#### Scenario: Invalid base_dir rejected before handler replacement in get_json_logger

- **WHEN** `get_json_logger("audit", "app.jsonl", base_dir="")` or `base_dir="   "` or `base_dir=True` is called while an existing handler is active on `arlogi.json.audit`
- **THEN** `ValueError` is raised before creating any directory or detaching the active handler
