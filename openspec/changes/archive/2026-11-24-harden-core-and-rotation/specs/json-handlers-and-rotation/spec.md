# Spec Delta

## Purpose

Defines safe console rendering, tamper-resistant JSON record formatting, idempotent stream cleanup, base-directory path containment, and non-fatal scheduled JSON file rotation and retention pruning.

## ADDED Requirements

### Requirement: Literal console message rendering by default

The colored console handler SHALL render log message text literally (`markup=False`) by default so untrusted message content cannot inject Rich console markup unless the caller explicitly enables `markup=True`.

#### Scenario: Rendering bracketed untrusted text without Rich markup parsing

- **WHEN** a message containing Rich markup syntax such as `"[bold red]injected[/bold red]"` is emitted to a default-configured console handler
- **THEN** the literal bracketed characters are written without applying Rich markup tags or raising markup parse errors

### Requirement: Protected JSON envelope with nested extra collision handling

The JSON formatter SHALL preserve canonical top-level envelope fields (`timestamp`, `level`, `logger_name`, `message`, `module`, `function`, `line_number`, `exception`, and correlation fields `trace_id`/`span_id` when present on the record) and SHALL place any colliding user-supplied `extra` or keyword fields inside a nested `"extra"` JSON object while keeping non-colliding custom fields at the top level.

#### Scenario: Routing colliding custom keys under nested extra object

- **WHEN** a record is logged with custom fields `timestamp="custom-ts"`, `level="FAKE"`, and `user_id=42`
- **THEN** top-level `timestamp` and `level` retain the canonical `LogRecord` values, top-level `user_id` equals `42`, and `"extra"` contains `{"timestamp": "custom-ts", "level": "FAKE"}`

#### Scenario: Preserving user-supplied extra key alongside other collisions

- **WHEN** a record is logged with both a custom `extra={"k": 1}` attribute and a colliding `logger_name="spoof"` attribute
- **THEN** top-level `logger_name` retains `record.name` and the nested `"extra"` object preserves both the user's `"extra"` value and `"logger_name": "spoof"` without data loss

### Requirement: Resilient JSON fallback serialization

When primary JSON serialization fails for any exception (including `TypeError`, `ValueError`, or custom `__str__` errors), the JSON formatter SHALL emit a valid fallback JSON line constructed directly from canonical `LogRecord` fields using safe string conversion rather than re-reading mutated dictionaries.

#### Scenario: Fallback serialization when custom **str** raises an exception

- **WHEN** a custom structured field raises `TypeError`, `ValueError`, or `RuntimeError` during `json.dumps(..., default=str)`
- **THEN** formatting returns a valid JSON string containing canonical record metadata and an `"error"` diagnostic field without raising out of `format()`

### Requirement: Idempotent and synchronized JSON stream closure

Closing a JSON stream handler that owns a custom non-system stream SHALL acquire the handler lock across flush and stream closure, skip system streams (`sys.stdout`, `sys.stderr`), and safely allow repeated `close()` calls without raising `ValueError`.

#### Scenario: Calling close twice on an owned file or BytesIO stream

- **WHEN** `handler.close()` is invoked multiple times on a `JSONHandler` wrapping an open file or `io.BytesIO` stream
- **THEN** the first call flushes and closes the stream under lock and subsequent calls complete without raising `ValueError: I/O operation on closed file`

### Requirement: Strict base-directory containment for JSON file logs

When `base_dir` (or `json_file_base_dir`) is configured, JSON file handler initialization SHALL resolve symlinks and relative segments and MUST reject any target path that escapes `base_dir` or resolves to the `base_dir` directory itself with `ValueError`.

#### Scenario: Rejecting traversal and symlink escapes outside base_dir

- **WHEN** a JSON file handler is constructed with `base_dir="/var/log/app"` and `filename="../outside.jsonl"` or a symlink pointing outside `base_dir`
- **THEN** initialization MUST raise `ValueError` before creating directories or opening files outside `base_dir`

#### Scenario: Rejecting path equal to base_dir directory

- **WHEN** a JSON file handler is constructed with `base_dir="/var/log/app"` and `filename="."` or `filename="/var/log/app"`
- **THEN** initialization MUST raise `ValueError`

### Requirement: Elapsed-period archive naming on schedule rotation

When an incoming log record crosses a configured schedule boundary (`hour`, `day`, `week`, or `month`), the JSON file handler SHALL name the rotated archive file using the elapsed active period key before advancing the active period key to the newly entered period.

#### Scenario: Daily boundary rotation names archive after the completed day

- **WHEN** a daily-rotating `app.jsonl` writes events on `2026-06-10` and then emits its first event on `2026-06-11`
- **THEN** the `2026-06-10` events are archived to `app-2026-06-10.jsonl` and subsequent manual rotation on `2026-06-11` writes to `app-2026-06-11.jsonl` without spurious `.1` collision suffixes

### Requirement: Exact-pattern retention pruning and non-fatal rotation error recovery

Retention pruning SHALL match only archive files belonging to the handler's exact stem, valid period-key format, and optional numeric collision suffix (even when directory or file names contain glob metacharacters), and any filesystem error during rotation, stream reopening, or `stat()`/unlink pruning MUST degrade non-fatally without raising out of `emit()`, `rotate_now()`, or `rotate_json_logger()`.

#### Scenario: Preserving sibling hyphenated log files and pruning inside bracketed directories

- **WHEN** `app.jsonl` rotates in a directory that also contains `app-audit.jsonl` (or inside a directory named `svc[v2]/`) with `rotate_retention_count=1`
- **THEN** `app-audit.jsonl` is never deleted and excess `app-<period>.jsonl` archives inside `svc[v2]/` are pruned to the retention limit

#### Scenario: Non-fatal recovery when stream reopen or file stat fails during rotation

- **WHEN** `rotate_now()` or `rotate_json_logger()` encounters `PermissionError` or `OSError` during `os.replace()`, `_open()`, or concurrent archive deletion during pruning
- **THEN** no exception escapes to the caller and `rotate_now()` returns `False` when rotation did not complete
