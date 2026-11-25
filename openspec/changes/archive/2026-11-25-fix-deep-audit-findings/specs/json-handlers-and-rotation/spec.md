# Spec Delta: json-handlers-and-rotation

## MODIFIED Requirements

### Requirement: Idempotent and synchronized JSON stream closure

Closing a JSON stream handler that owns a custom non-system stream SHALL acquire the handler lock across flush and stream closure, SHALL close and release the owned stream even when flushing raises, and SHALL safely allow repeated `close()` calls without raising `ValueError`. System streams (`sys.stdout`, `sys.stderr`, `sys.__stdout__`, `sys.__stderr__`) MUST never be treated as owned or closed, even when passed explicitly or when standard streams are redirected. Once closed, `JSONHandler.emit()` SHALL return immediately without writing to any stream or invoking `handleError()`.

#### Scenario: Calling close twice on an owned file or BytesIO stream

- **WHEN** `handler.close()` is invoked multiple times on a `JSONHandler` wrapping an open file or `io.BytesIO` stream
- **THEN** the first call flushes and closes the stream under lock and subsequent calls complete without raising `ValueError: I/O operation on closed file`

#### Scenario: Releasing an owned stream when flush fails during close

- **WHEN** a `JSONHandler` wraps an owned stream whose `flush()` raises `BrokenPipeError` (or `OSError` with `ENOSPC`) and `handler.close()` is called
- **THEN** the owned stream is closed (`stream.closed` is `True`), the handler's stream reference is cleared, and a second `handler.close()` call completes without raising

#### Scenario: Never closing an explicitly passed system stream under redirection

- **WHEN** a handler is constructed with `JSONHandler(stream=sys.stderr)` and later closed inside `contextlib.redirect_stderr(io.StringIO())`
- **THEN** the original stderr stream remains open (`closed` is `False`) after `handler.close()` returns

#### Scenario: Post-close emit on JSONHandler is a silent no-op

- **WHEN** `handler.close()` has completed on a `JSONHandler` wrapping either a custom stream or `sys.stderr` and `handler.handle(record)` is subsequently called
- **THEN** `emit()` returns without writing to the stream and without calling `handleError()` or writing `--- Logging error ---` to `sys.stderr`

### Requirement: Strict base-directory containment for JSON file logs

When `base_dir` (or `json_file_base_dir`) is configured (not `None`), JSON file handler initialization SHALL validate that `base_dir` is a non-empty, non-whitespace `str` or `Path` without NUL bytes, SHALL resolve symlinks and relative segments, and MUST reject any target path that escapes `base_dir` or resolves to the `base_dir` directory itself with `ValueError` before creating directories or opening files.

#### Scenario: Rejecting traversal and symlink escapes outside base_dir

- **WHEN** a JSON file handler is constructed with `base_dir="/var/log/app"` and `filename="../outside.jsonl"` or a symlink pointing outside `base_dir`
- **THEN** initialization MUST raise `ValueError` before creating directories or opening files outside `base_dir`

#### Scenario: Rejecting path equal to base_dir directory

- **WHEN** a JSON file handler is constructed with `base_dir="/var/log/app"` and `filename="."` or `filename="/var/log/app"`
- **THEN** initialization MUST raise `ValueError`

#### Scenario: Rejecting empty, whitespace, or non-path base_dir

- **WHEN** `JSONFileHandler("app.jsonl", base_dir=v)` is called with `v` in `("", "   ", 123, True, "\x00")`
- **THEN** initialization MUST raise `ValueError` before resolving `os.getcwd()` or creating any directory or file

### Requirement: Exact-pattern retention pruning and non-fatal rotation error recovery

Retention pruning SHALL match only archive files belonging to the handler's exact stem, valid period-key format, and optional numeric collision suffix (even when directory or file names contain glob metacharacters), and any filesystem error during rotation, stream reopening, or `stat()`/unlink pruning MUST degrade non-fatally without raising out of `emit()`, `rotate_now()`, or `rotate_json_logger()`. When `os.replace()` archives the current file during rotation, `_active_period_key` SHALL advance and `_prune_rotated_files()` SHALL execute before attempting to reopen the active stream, and persistent reopen failures MUST NOT invoke `_report_rotation_error()` more than once per rotation attempt.

#### Scenario: Preserving sibling hyphenated log files and pruning inside bracketed directories

- **WHEN** `app.jsonl` rotates in a directory that also contains `app-audit.jsonl` (or inside a directory named `svc[v2]/`) with `rotate_retention_count=1`
- **THEN** `app-audit.jsonl` is never deleted and excess `app-<period>.jsonl` archives inside `svc[v2]/` are pruned to the retention limit

#### Scenario: Non-fatal recovery when stream reopen or file stat fails during rotation

- **WHEN** `rotate_now()` or `rotate_json_logger()` encounters `PermissionError` or `OSError` during `os.replace()`, `_open()`, or concurrent archive deletion during pruning
- **THEN** no exception escapes to the caller and `rotate_now()` returns `False` when rotation did not complete

#### Scenario: Period key advances and retention prunes even when _open() fails after os.replace()

- **WHEN** a daily-rotating `JSONFileHandler` (`rotate_retention_count=1`) rotates across a day boundary (`2026-06-10` -> `2026-06-11`), `os.replace("app.jsonl", "app-2026-06-10.jsonl")` succeeds, and the subsequent `self._open()` raises `OSError`
- **THEN** `_active_period_key` is already updated to `"2026-06-11"`, older expired archives are pruned, subsequent `2026-06-11` emissions do not create a misdated `app-2026-06-10.1.jsonl` that evicts `app-2026-06-10.jsonl`, and persistent `_open()` failure reports at most once

### Requirement: JSON file handler parameter validation before filesystem side effects

The JSON file handler SHALL validate `filename` (non-empty, non-whitespace `str` without NUL bytes, regardless of whether `base_dir` is set), `base_dir` (when not `None`, `str` or `Path` with non-empty stripped string and no NUL bytes), `rotate_schedule` (when not `None`, a `str` in `{"hour", "day", "week", "month"}` raising `ValueError` with `"Invalid rotate_schedule"` otherwise), and `rotate_retention_count` (when not `None`, a non-boolean integer `>= 1`) and MUST raise `ValueError` before creating any directory, creating any file, or opening any stream.

#### Scenario: Rejecting an invalid schedule without leaving files or descriptors

- **WHEN** `JSONFileHandler("sub/app.jsonl", rotate_schedule="invalid")`, `rotate_schedule=""`, or `rotate_schedule=["day"]` is constructed in an empty directory
- **THEN** construction raises `ValueError` matching `"Invalid rotate_schedule"`, neither `sub/` nor `sub/app.jsonl` is created, and no `ResourceWarning: unclosed file` is emitted

#### Scenario: Rejecting invalid retention counts

- **WHEN** `JSONFileHandler("app.jsonl", rotate_retention_count=...)` is constructed with `0`, `-1`, `True`, `False`, or `"7"`
- **THEN** construction raises `ValueError` and no archive can be deleted by a later rotation

#### Scenario: Rejecting empty or non-string filename without base_dir

- **WHEN** `JSONFileHandler(bad_name)` is constructed with `bad_name` in `("", "   ", 123, "\x00")` and `base_dir=None`
- **THEN** construction raises `ValueError` before creating any file or raising `IsADirectoryError` / `AttributeError`

### Requirement: Syslog handler socket release on close

`ArlogiSyslogHandler` SHALL verify Unix socket liveness (`self.socket is not None and self.socket.fileno() != -1`) after initialization so stale or permission-denied `"/dev/log"` sockets fall back to `("localhost", 514)` (or degrade to `_failed = True`) while custom non-`"/dev/log"` Unix socket failures raise `OSError` immediately. On transport `OSError` during `emit()` or `handleError()`, `ArlogiSyslogHandler` SHALL set `_failed = True` and close/clear the socket under lock without flooding `sys.stderr`. Closing the syslog handler SHALL acquire the handler lock, set `_closed = True` so subsequent `emit()` calls return early without reopening a socket, release any open socket even when `_failed` is `True`, and complete without raising even if initialization failed. `ArlogiSyslogHandler` SHALL map `"TRACE"` to `"debug"` in `priority_map`.

#### Scenario: Closing after a post-initialization emit failure

- **WHEN** an `ArlogiSyslogHandler(address=("localhost", 514))` opens a socket, a transport `OSError` or exception occurs inside `emit()` marking `_failed = True`, and `cleanup_syslog_logger()` or `handler.close()` runs
- **THEN** the socket is closed (`fileno() == -1`), subsequent `emit()` calls are silent no-ops without `stderr` tracebacks, and `close()` completes without raising

#### Scenario: Closing a handler whose initialization failed

- **WHEN** both the `/dev/log` and `("localhost", 514)` fallbacks fail during construction and `handler.close()` is called twice
- **THEN** both calls complete without raising

#### Scenario: Stale or permission-denied /dev/log triggers UDP fallback on Python 3.13

- **WHEN** `/dev/log` exists on disk as a stale or refused Unix socket and `ArlogiSyslogHandler(address="/dev/log")` is constructed on Python 3.13
- **THEN** the handler detects the dead Unix socket (`fileno() == -1`), falls back to UDP `("localhost", 514)` (or marks `_failed = True` if UDP also fails), and does not flood `stderr` on subsequent `emit()` calls

#### Scenario: Custom non-/dev/log Unix socket fails fast with OSError

- **WHEN** `ArlogiSyslogHandler(address="/nonexistent_socket_path")` is constructed with an unreachable custom Unix socket path
- **THEN** initialization raises `OSError` immediately instead of silently leaving a closed socket

#### Scenario: Post-close emit never reopens a closed syslog socket

- **WHEN** `handler.close()` completes on an `ArlogiSyslogHandler` and a subsequent `handler.handle(record)` runs
- **THEN** `emit()` sees `_closed == True` and returns immediately without calling `createSocket()` or emitting `ResourceWarning`

#### Scenario: Mapping TRACE level records to syslog DEBUG priority

- **WHEN** a `LogRecord` at level `TRACE` (`5`) is emitted via `ArlogiSyslogHandler` in `"text"` or `"json"` mode
- **THEN** `mapPriority("TRACE")` returns `"debug"` and the syslog frame encodes PRI `<15>` (`LOG_USER | LOG_DEBUG`) rather than `<12>` (`WARNING`)
