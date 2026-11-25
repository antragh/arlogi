# Spec Delta

## Purpose

Defines thread-safe logger initialization, `TRACE` level support, structured keyword/context handling, call-site attribution, and atomic handler replacement across root and dedicated loggers.

## ADDED Requirements

### Requirement: Dedicated loggers conform to LoggerProtocol in fresh processes

Calling `get_json_logger()` or `get_syslog_logger()` in a fresh process prior to `setup_logging()` or `get_logger()` SHALL register the `TRACE` level and instantiate a `LoggerProtocol`-compliant logger supporting `.trace()`, `caller_depth`, and structured keyword arguments; calling cleanup or rotation helpers for an uncreated logger MUST NOT prematurely cache a plain `logging.Logger`.

#### Scenario: Using get_json_logger first in a fresh process

- **WHEN** `get_json_logger("audit", "logs/audit.jsonl")` is called in a fresh Python process before `setup_logging()` and invoked with `logger.info("login", user_id=123, caller_depth=0)` and `logger.trace("detail")`
- **THEN** the returned logger satisfies `isinstance(logger, LoggerProtocol)` and emits structured records without raising `TypeError` or `AttributeError`

#### Scenario: Cleaning up or rotating a non-existent dedicated logger

- **WHEN** `cleanup_json_logger("unused")`, `cleanup_syslog_logger("unused")`, or `rotate_json_logger("unused")` is called before `get_json_logger("unused")` or `get_syslog_logger("unused")`
- **THEN** the helper completes as a no-op without registering a plain `logging.Logger` in Python's logger manager

### Requirement: Thread-safe dedicated logger replacement, cleanup, and rotation

Dedicated JSON and Syslog logger creation, cleanup, and rotation SHALL serialize mutations to `logger.handlers` under lock protection and MUST detach existing handlers from the logger before closing them so concurrent log emissions never reopen closed file streams or accumulate duplicate handlers.

#### Scenario: Concurrent same-name dedicated logger reconfiguration and emission

- **WHEN** multiple threads concurrently emit records, reconfigure `get_json_logger("audit", path)`, and call `rotate_json_logger("audit")` or `cleanup_json_logger("audit")`
- **THEN** at most one handler remains attached after reconfiguration and detached handlers do not reopen closed streams or emit `ResourceWarning`

### Requirement: Atomic create-before-detach handler reconfiguration

When reconfiguring root or dedicated loggers, the factory SHALL construct all replacement handlers before detaching and closing existing handlers, and SHALL close any partially created handlers if a subsequent handler constructor fails.

#### Scenario: Preserving active handlers when reconfiguration fails

- **WHEN** logging is already active and a subsequent `setup_logging()`, `get_json_logger()`, or `get_syslog_logger()` call fails during new handler creation (for example due to base-directory containment rejection or an unreachable explicit syslog address)
- **THEN** the call raises the error while closing any partially opened new handlers and leaving previously attached handlers intact and open

#### Scenario: Closing replaced handlers cleanly on successful reconfiguration

- **WHEN** `setup_logging()` is called again in production mode with valid handler settings
- **THEN** replaced root handlers are detached and explicitly closed without emitting `ResourceWarning`

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

Logger methods (`trace`, `debug`, `info`, `warning`, `error`, `critical`, `fatal`, `exception`, `log`, and monkey-patched `logging.Logger.trace`) SHALL report the caller's module, function, and line number accurately, increment caller-provided `stacklevel` offsets by `1`, and escape caller attribution suffixes against Rich markup interpretation.

#### Scenario: Accurate call site on exception and fatal methods

- **WHEN** user code invokes `logger.exception("boom", caller_depth=0)` or `logger.fatal("halt", caller_depth=0)`
- **THEN** the resulting log record's `funcName`, `filename`, `lineno`, and `[<func>()]` attribution suffix all reference the user's function rather than `arlogi` wrapper frames

#### Scenario: Respecting explicit stacklevel from user helper wrappers

- **WHEN** a helper function calls `logger.info("wrapped", stacklevel=2)` (or invokes `.trace()` on a pre-existing `logging.Logger`)
- **THEN** the log record attributes the call to the caller of the helper function (or direct `.trace()` caller) rather than the `arlogi` wrapper
