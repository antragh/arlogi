# logger-lifecycle Specification

## Purpose
Defines thread-safe logger initialization, `TRACE` level support, structured keyword/context handling, call-site attribution, and atomic handler replacement across root and dedicated loggers.

## Requirements

### Requirement: Dedicated loggers conform to LoggerProtocol in fresh processes

Calling `get_json_logger()` or `get_syslog_logger()` in a fresh process prior to `setup_logging()` or `get_logger()` SHALL register the `TRACE` level and instantiate a `LoggerProtocol`-compliant logger supporting `.trace()`, `caller_depth`, and structured keyword arguments; calling cleanup or rotation helpers for an uncreated logger MUST NOT prematurely cache a plain `logging.Logger`.

#### Scenario: Using get_json_logger first in a fresh process

- **WHEN** `get_json_logger("audit", "logs/audit.jsonl")` is called in a fresh Python process before `setup_logging()` and invoked with `logger.info("login", user_id=123, caller_depth=0)` and `logger.trace("detail")`
- **THEN** the returned logger satisfies `isinstance(logger, LoggerProtocol)` and emits structured records without raising `TypeError` or `AttributeError`

#### Scenario: Cleaning up or rotating a non-existent dedicated logger

- **WHEN** `cleanup_json_logger("unused")`, `cleanup_syslog_logger("unused")`, or `rotate_json_logger("unused")` is called before `get_json_logger("unused")` or `get_syslog_logger("unused")`
- **THEN** the helper completes as a no-op without registering a plain `logging.Logger` in Python's logger manager

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

### Requirement: Atomic create-before-detach handler reconfiguration

When reconfiguring root or dedicated loggers, the factory SHALL construct all replacement handlers before replacing the existing handler set in a single atomic swap of the logger's handler list, SHALL close replaced handlers only after the swap, and SHALL close any partially created handlers if a subsequent handler constructor fails. Concurrent emitters MUST never observe an empty or partially mutated handler list during reconfiguration.

#### Scenario: Preserving active handlers when reconfiguration fails

- **WHEN** logging is already active and a subsequent `setup_logging()`, `get_json_logger()`, or `get_syslog_logger()` call fails during new handler creation (for example due to base-directory containment rejection or an unreachable explicit syslog address)
- **THEN** the call raises the error while closing any partially opened new handlers and leaving previously attached handlers intact and open

#### Scenario: Closing replaced handlers cleanly on successful reconfiguration

- **WHEN** `setup_logging()` is called again in production mode with valid handler settings
- **THEN** replaced root handlers are detached and explicitly closed without emitting `ResourceWarning`

#### Scenario: No zero-handler window during concurrent dedicated reconfiguration

- **WHEN** worker threads continuously emit `WARNING` records to `arlogi.json.audit` while another thread repeatedly calls `get_json_logger("audit", path)`
- **THEN** no record is delivered to `logging.lastResort` (nothing raw is written to `sys.stderr` by the last-resort handler) and every observed handler list contains exactly one handler

#### Scenario: Multi-handler root reconfiguration delivers to all handlers

- **WHEN** worker threads emit records to a root logger configured with three handlers while another thread repeatedly reapplies an equivalent three-handler configuration
- **THEN** every emitted record reaches exactly three handlers and no record reaches `logging.lastResort`

### Requirement: Non-mutating structured keyword and Mapping extra handling

Structured keyword arguments passed to logger methods SHALL be merged into a new `extra` dictionary without mutating any caller-supplied `extra` mapping in place, SHALL treat `extra=None` as empty without attaching `_original_extra`, and SHALL preserve keys from non-`dict` `collections.abc.Mapping` instances.

#### Scenario: Preserving shared caller context dictionary across log calls

- **WHEN** a caller passes a shared `ctx = {"request_id": "r1"}` via `logger.info("auth", extra=ctx, user_id=42)`
- **THEN** the emitted record includes both `request_id` and `user_id` while `ctx` remains `{"request_id": "r1"}`

#### Scenario: Merging read-only Mapping extra with structured kwargs

- **WHEN** a caller passes `extra=MappingProxyType({"tenant": "acme"})` together with `action="sync"`
- **THEN** both `tenant` and `action` are attached to the log record without silent key loss

### Requirement: Disabled-level fast path without side effects

Logger methods SHALL check whether the target level is enabled on the logger before performing caller-frame inspection or `extra` parameter processing.

#### Scenario: Skipping parameter processing on disabled TRACE or DEBUG calls

- **WHEN** a logger configured at `INFO` level is called with `logger.trace("skip", extra=ctx, caller_depth=1, secret="x")`
- **THEN** no frame inspection or dictionary allocation occurs and `ctx` is untouched

### Requirement: Accurate call-site stacklevel and caller attribution

Logger methods (`trace`, `debug`, `info`, `warning`, `error`, `critical`, `fatal`, `exception`, `log`, and monkey-patched `logging.Logger.trace`) SHALL report the caller's module, function, and line number accurately, increment caller-provided `stacklevel` offsets by `1`, and escape caller attribution suffixes against Rich markup interpretation. A `caller_depth` that is a boolean or a negative integer MUST disable attribution instead of exposing internal frames.

#### Scenario: Accurate call site on exception and fatal methods

- **WHEN** user code invokes `logger.exception("boom", caller_depth=0)` or `logger.fatal("halt", caller_depth=0)`
- **THEN** the resulting log record's `funcName`, `filename`, `lineno`, and `[<func>()]` attribution suffix all reference the user's function rather than `arlogi` wrapper frames

#### Scenario: Respecting explicit stacklevel from user helper wrappers

- **WHEN** a helper function calls `logger.info("wrapped", stacklevel=2)` (or invokes `.trace()` on a pre-existing `logging.Logger`)
- **THEN** the log record attributes the call to the caller of the helper function (or direct `.trace()` caller) rather than the `arlogi` wrapper

#### Scenario: Negative caller_depth does not leak internal frames

- **WHEN** user code invokes `logger.info("test", caller_depth=d)` for each `d` in `-1`, `-2`, `-3`, `-4`, `-5`
- **THEN** the emitted message is exactly `"test"` with no `[info()]`, `[_process_params()]`, `[_apply_caller_attribution()]`, or `[_get_caller_info()]` suffix and no attribution field is attached

#### Scenario: Boolean caller_depth disables attribution

- **WHEN** user code invokes `logger.info("test", caller_depth=False)` or `logger.info("test", caller_depth=True)`
- **THEN** the emitted message is exactly `"test"` with no attribution suffix

#### Scenario: Keyword msg on the patched Logger.trace

- **WHEN** a pre-existing plain `logging.Logger` (created before arlogi initialization) calls `logger.trace(msg="kwarg")` with `TRACE` enabled
- **THEN** a level-5 record with message `"kwarg"` is emitted without raising `TypeError`

### Requirement: Complete TRACE registration when logging.TRACE pre-exists

`TRACE` registration SHALL independently ensure, under a lock and idempotently, that level `5` is named `"TRACE"`, that `logging.TRACE` exists (without overwriting an existing value), and that `logging.Logger` provides a `trace()` method (without replacing an existing one), even when another library already defined `logging.TRACE`.

#### Scenario: Third-party library pre-defines logging.TRACE

- **WHEN** a fresh process sets `logging.TRACE = 5` and creates `logging.getLogger("app.worker")` before calling `arlogi.get_logger("app.worker")`
- **THEN** `logging.getLevelName(5)` returns `"TRACE"`, the pre-existing logger has a callable `.trace()`, `isinstance(logger, LoggerProtocol)` is `True`, and JSON output for a level-5 record reports `"level": "TRACE"`

#### Scenario: Concurrent registration remains idempotent

- **WHEN** multiple threads call `get_logger()` concurrently in a fresh process where `logging.TRACE` was pre-defined
- **THEN** level-name registration and `Logger.trace` attachment each happen at most once and no thread raises

### Requirement: Dedicated syslog logger format selection

`get_syslog_logger()` and `LoggerFactory.get_syslog_logger()` SHALL accept `syslog_format: Literal["text", "json"] = "text"`, forward it to `ArlogiSyslogHandler`, and preserve atomic create-before-detach handler replacement so an invalid `syslog_format` fails without disturbing previously attached handlers.

#### Scenario: Dedicated JSON-formatted syslog logger emission

- **WHEN** a caller obtains `get_syslog_logger("security", syslog_format="json")` and logs a structured event with custom kwargs and `caller_depth`
- **THEN** the attached `ArlogiSyslogHandler` formats the emitted syslog payload via `SyslogJSONFormatter` as `arlogi.syslog.security[<pid>]: <json_payload>` containing the structured kwargs

#### Scenario: Preserving active dedicated syslog handler on invalid syslog_format

- **WHEN** `get_syslog_logger("security", syslog_format="text")` is active and a subsequent call `get_syslog_logger("security", syslog_format="invalid")` raises `ValueError`
- **THEN** the previously attached `ArlogiSyslogHandler` remains attached and open on `arlogi.syslog.security`
