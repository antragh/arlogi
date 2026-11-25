# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Complete TRACE registration when logging.TRACE pre-exists

`TRACE` registration SHALL independently ensure, under a lock and idempotently, that level `5` is named `"TRACE"`, that `logging.TRACE` exists (without overwriting an existing value), and that `logging.Logger` provides a `trace()` method (without replacing an existing one), even when another library already defined `logging.TRACE`.

#### Scenario: Third-party library pre-defines logging.TRACE

- **WHEN** a fresh process sets `logging.TRACE = 5` and creates `logging.getLogger("app.worker")` before calling `arlogi.get_logger("app.worker")`
- **THEN** `logging.getLevelName(5)` returns `"TRACE"`, the pre-existing logger has a callable `.trace()`, `isinstance(logger, LoggerProtocol)` is `True`, and JSON output for a level-5 record reports `"level": "TRACE"`

#### Scenario: Concurrent registration remains idempotent

- **WHEN** multiple threads call `get_logger()` concurrently in a fresh process where `logging.TRACE` was pre-defined
- **THEN** level-name registration and `Logger.trace` attachment each happen at most once and no thread raises
