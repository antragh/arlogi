# Spec Delta

## MODIFIED Requirements

### Requirement: Idempotent and synchronized JSON stream closure

Closing a JSON stream handler that owns a custom non-system stream SHALL acquire the handler lock across flush and stream closure, SHALL close and release the owned stream even when flushing raises, and SHALL safely allow repeated `close()` calls without raising `ValueError`. System streams (`sys.stdout`, `sys.stderr`, `sys.__stdout__`, `sys.__stderr__`) MUST never be treated as owned or closed, even when passed explicitly or when standard streams are redirected.

#### Scenario: Calling close twice on an owned file or BytesIO stream

- **WHEN** `handler.close()` is invoked multiple times on a `JSONHandler` wrapping an open file or `io.BytesIO` stream
- **THEN** the first call flushes and closes the stream under lock and subsequent calls complete without raising `ValueError: I/O operation on closed file`

#### Scenario: Releasing an owned stream when flush fails during close

- **WHEN** a `JSONHandler` wraps an owned stream whose `flush()` raises `BrokenPipeError` (or `OSError` with `ENOSPC`) and `handler.close()` is called
- **THEN** the owned stream is closed (`stream.closed` is `True`), the handler's stream reference is cleared, and a second `handler.close()` call completes without raising

#### Scenario: Never closing an explicitly passed system stream under redirection

- **WHEN** a handler is constructed with `JSONHandler(stream=sys.stderr)` and later closed inside `contextlib.redirect_stderr(io.StringIO())`
- **THEN** the original stderr stream remains open (`closed` is `False`) after `handler.close()` returns

### Requirement: Elapsed-period archive naming on schedule rotation

When an incoming log record crosses a configured schedule boundary (`hour`, `day`, `week`, or `month`), or when a manual rotation (`rotate_now()` or `rotate_json_logger()`) runs after such a boundary has elapsed without an intervening record, the JSON file handler SHALL name the rotated archive file using the elapsed active period key before advancing the active period key to the newly entered period.

#### Scenario: Daily boundary rotation names archive after the completed day

- **WHEN** a daily-rotating `app.jsonl` writes events on `2026-06-10` and then emits its first event on `2026-06-11`
- **THEN** the `2026-06-10` events are archived to `app-2026-06-10.jsonl` and subsequent manual rotation on `2026-06-11` writes to `app-2026-06-11.jsonl` without spurious `.1` collision suffixes

#### Scenario: Manual rotation after an elapsed boundary names archive after the completed day

- **WHEN** a daily-rotating `app.jsonl` writes events on `2026-06-10` and `rotate_now()` is called at `2026-06-11 00:05` before any `2026-06-11` record is emitted
- **THEN** the `2026-06-10` events are archived to `app-2026-06-10.jsonl` (not `app-2026-06-11.jsonl`) and the active period key advances to `2026-06-11`

## ADDED Requirements

### Requirement: Current-hour archive naming for unscheduled manual rotation

A JSON file handler without a rotation schedule SHALL name each manually rotated archive after the local hour (`YYYY-MM-DD-HH`) in which that rotation runs and MUST NOT retain a period key across rotations, including after a no-op rotation of an empty file.

#### Scenario: Repeated manual rotations across days on an unscheduled handler

- **WHEN** a logger from `get_json_logger("audit", "audit.jsonl")` writes events and `rotate_json_logger("audit")` is called at `2026-06-10 10:00`, `2026-06-13 15:00`, and `2026-07-01 09:00`
- **THEN** the archives are `audit-2026-06-10-10.jsonl`, `audit-2026-06-13-15.jsonl`, and `audit-2026-07-01-09.jsonl` with no `.1`/`.2` collision suffixes

#### Scenario: Empty-file no-op does not freeze the archive name

- **WHEN** `rotate_now()` is called on an unscheduled handler with an empty file at `2026-06-10 10:00` and again after writing events at `2026-07-01 09:00`
- **THEN** the first call returns `False` and the second call archives to `audit-2026-07-01-09.jsonl`

### Requirement: JSON file handler parameter validation before filesystem side effects

The JSON file handler SHALL validate `rotate_schedule` (when not `None`, it MUST be one of `hour`, `day`, `week`, `month`; the empty string is invalid) and `rotate_retention_count` (when not `None`, it MUST be a non-boolean integer `>= 1`) and MUST raise `ValueError` before creating any directory, creating any file, or opening any stream.

#### Scenario: Rejecting an invalid schedule without leaving files or descriptors

- **WHEN** `JSONFileHandler("sub/app.jsonl", rotate_schedule="invalid")` or `rotate_schedule=""` is constructed in an empty directory
- **THEN** construction raises `ValueError`, neither `sub/` nor `sub/app.jsonl` is created, and no `ResourceWarning: unclosed file` is emitted

#### Scenario: Rejecting invalid retention counts

- **WHEN** `JSONFileHandler("app.jsonl", rotate_retention_count=...)` is constructed with `0`, `-1`, `True`, `False`, or `"7"`
- **THEN** construction raises `ValueError` and no archive can be deleted by a later rotation

### Requirement: Deterministic regular-file-only archive retention

Retention pruning SHALL count and delete only regular files (never directories or symlinks, evaluated without following symlinks), SHALL exclude the active log file by resolved path, and SHALL order archives newest-first by nanosecond modification time, then by archive timestamp key, then by numeric collision suffix (unsuffixed counts as `0`, so `.10` is newer than `.2`), deleting only entries beyond the retention count.

#### Scenario: Matching directory or symlink does not consume a retention slot

- **WHEN** a directory contains a real archive `app-2026-06-10.jsonl`, a newer directory named `app-2026-06-15.jsonl/`, and a newer symlink `app-2026-06-16.jsonl`, and `app.jsonl` rotates with `rotate_retention_count=2`
- **THEN** the real archives `app-2026-06-10.jsonl` and the newly rotated archive are both retained and the directory and symlink are left untouched

#### Scenario: Equal modification times prune the older archive

- **WHEN** rotated archives `app-2026-06-10.jsonl`, `app-2026-06-10.1.jsonl`, and `app-2026-06-10.2.jsonl` share an identical `st_mtime_ns` and pruning runs with `rotate_retention_count=2`
- **THEN** `app-2026-06-10.jsonl` is deleted and `app-2026-06-10.1.jsonl` and `app-2026-06-10.2.jsonl` are retained regardless of directory enumeration order

### Requirement: Syslog handler socket release on close

Closing the syslog handler SHALL release any open socket under the handler lock even when the handler was marked failed after successful initialization, and closing a handler whose initialization failed MUST complete without raising.

#### Scenario: Closing after a post-initialization emit failure

- **WHEN** an `ArlogiSyslogHandler(address=("localhost", 514))` opens a socket, an exception escapes `emit()` (for example a closed `sys.stderr` raising `ValueError` inside error handling) marking the handler failed, and `cleanup_syslog_logger()` or `handler.close()` runs
- **THEN** the socket is closed (`fileno() == -1`) and no exception escapes `close()`

#### Scenario: Closing a handler whose initialization failed

- **WHEN** both the `/dev/log` and `("localhost", 514)` fallbacks fail during construction and `handler.close()` is called twice
- **THEN** both calls complete without raising
