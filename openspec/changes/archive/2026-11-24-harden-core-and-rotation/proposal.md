# Proposal

## Why

The repository deep audit (`docs/_audit_/2611242139-deep-audit.md`) identified critical lifecycle, concurrency, data-integrity, and rotation defects across `arlogi`'s core logging and handler modules — alongside an uncommitted security-hardening diff in `config.py`, `config_builder.py`, `factory.py`, `handler_factory.py`, and `handlers.py` that introduces `INV-2` (`sys.modules`-only `is_test_mode()`), `INV-4` (`markup=False` console default), and `INV-5` (`json_file_base_dir` containment) but still lacks complete validation, atomic handler cleanup, and regression coverage. Remediating Wave 1 as a cohesive spec-driven change stabilizes core logging semantics, thread safety, JSON audit integrity, and file rotation before Wave 2 (`arlogi.otel`) and Wave 3 (CI/CD, packaging, and documentation sync).

## What Changes

- **Harden `LoggingConfig` & `LoggingConfigBuilder` (`DA-012`, `DA-021`, `DA-032`, `INV-1`, `INV-2`)**:
  - Consolidate level validation and resolution so `'TRACE'` resolves cleanly before `register_trace_level()` runs, while rejecting `bool` values and non-level `logging` module attributes (e.g., `'BASIC_FORMAT'`, `'_STYLES'`) and enforcing strict integer validation on `rotate_retention_count`.
  - Fix `LoggingConfigBuilder.with_json_console_only()` to clear `_json_file_name`, align builder default level/types with `LoggingConfig`, and derive `LoggingConfig.to_dict()` / `from_kwargs()` dynamically from `dataclasses.fields()`.
  - Add public, lock-protected `LoggerFactory.apply_config(config: LoggingConfig)` and optional `config: LoggingConfig | None = None` support in `setup_logging()` / `LoggerFactory.setup()` (raising `ValueError` if combined with explicit keyword overrides), and export `LoggingConfigBuilder` in `arlogi.__all__`.
  - Finalize `is_test_mode()` (`sys.modules`-only check, removing unused `import os` and aligning Python docstrings in `config.py` and `factory.py`).
- **Fix `TraceLogger` & `LoggerFactory` lifecycle and concurrency (`DA-001`, `DA-007`, `DA-015`, `DA-016`, `INV-3`, `INV-4`)**:
  - Initialize `TRACE` level and `TraceLogger` class inside `get_json_logger()` and `get_syslog_logger()` (under `_init_lock`), guard `cleanup_json_logger()`, `cleanup_syslog_logger()`, and `rotate_json_logger()` against instantiating uncreated plain loggers, and serialize dedicated-logger handler replacement/cleanup/rotation with detach-before-close ordering.
  - Make root and dedicated handler reconfiguration create-before-detach-and-close (`HandlerFactory.create_handlers()` rolls back already-opened handlers on partial failure; old handlers are detached and closed only after replacements succeed).
  - Fix `TraceLogger._process_params()` to stop mutating caller `extra` dicts in place, preserve non-`dict` `Mapping` keys, skip work on disabled log levels via `isEnabledFor()`, and fix call-site `stacklevel` / `caller_depth` frame offsets across `exception()`, `fatal()`, explicit `stacklevel`, and monkey-patched `logging.Logger.trace()`.
- **Harden JSON formatting, stream closing, and file rotation (`DA-004`, `DA-008`, `DA-013`, `DA-014`, `DA-023`, `INV-4`, `INV-5`)**:
  - Protect canonical envelope keys (`timestamp`, `level`, `logger_name`, `message`, `module`, `function`, `line_number`, `exception`, and active correlation IDs `trace_id`, `span_id`) in `JSONFormatter.format()` by routing colliding `extra`/kwargs fields into a nested `"extra": {...}` object, and harden fallback serialization (`default=str`, canonical `record` source, broad `Exception` guard).
  - Make `JSONHandler.close()` lock-protected and idempotent on owned custom streams.
  - Harden `JSONFileHandler`: reject directory-equal paths in `_resolve_within_base()`, archive schedule-rotated files under the elapsed `_active_period_key` (**behavioral bug fix**), restrict `_prune_rotated_files()` to escaped exact stem + valid period-key/collision regex with safe per-file `stat()`, and guard `_ensure_stream_open()` inside `_rotate_now_locked()` so I/O failures never crash `rotate_now()` or `rotate_json_logger()` callers.
- **Non-Goals / Out of Scope**:
  - OpenTelemetry (`src/arlogi/otel/*` and `tests/conftest.py` OTel fixtures: `DA-002`, `DA-003`, `DA-006`, `DA-009`, `DA-010`, `DA-022`, `DA-024`, `DA-031`) — deferred to Wave 2 (`otel` change); uncommitted edits in `src/arlogi/otel/` will not be modified in Wave 1.
  - GitHub Actions workflows, Hatchling `sdist` / dependency-group splitting, and Markdown documentation guides (`DA-005`, `DA-011`, `DA-017`..`DA-020`, `DA-025`..`DA-030`) — deferred to Wave 3.

## Capabilities

### New Capabilities

- `logging-configuration`: Validated immutable `LoggingConfig`, fluent `LoggingConfigBuilder`, `sys.modules`-only `is_test_mode()`, and public configuration application APIs (`setup_logging(config=...)`, `LoggerFactory.apply_config`, `arlogi.__all__` exports).
- `logger-lifecycle`: Idempotent `TRACE` level registration, `TraceLogger` structured kwargs / non-mutating `extra` / `caller_depth` / `stacklevel` semantics, atomic root handler replacement, and synchronized dedicated JSON/Syslog logger lifecycle.
- `json-handlers-and-rotation`: Literal-by-default `ColoredConsoleHandler`, collision-safe `JSONFormatter` with resilient fallback serialization, idempotent `JSONHandler` stream cleanup, and containment-enforced, exact-pruning, non-fatal `JSONFileHandler` rotation.

### Modified Capabilities

<!-- None: this change establishes the initial OpenSpec baseline capabilities for arlogi's core package. -->

## Impact

- **Affected Code**: `src/arlogi/__init__.py`, `src/arlogi/config.py`, `src/arlogi/config_builder.py`, `src/arlogi/levels.py`, `src/arlogi/types.py`, `src/arlogi/factory.py`, `src/arlogi/handler_factory.py`, `src/arlogi/handlers.py`, and core test suites under `tests/` (plus `tests/example/example.py` if updated from `_apply_configuration` to public API).
- **Public API & Behavioral Compatibility**:
  - **Additive API**: `LoggingConfigBuilder` exported in `arlogi`, `LoggingConfig.json_file_base_dir` / `LoggingConfigBuilder.with_json_base_dir()`, `JSONFileHandler(..., base_dir=...)`, `get_json_logger(..., base_dir=...)`, `LoggerFactory.apply_config(config)`, and `setup_logging(config=...)` / `LoggerFactory.setup(config=...)`.
  - **Behavioral Tightening / Bug Fixes**:
    - `ColoredConsoleHandler` defaults `markup=False` instead of `markup=True` (callers requiring Rich markup must opt in explicitly via `markup=True`).
    - `is_test_mode()` ignores `PYTEST_CURRENT_TEST` when neither `pytest` nor `unittest` is loaded in `sys.modules`.
    - `JSONFormatter` moves custom `extra`/kwargs keys that collide with reserved envelope keys into `"extra": {...}` rather than overwriting top-level audit fields.
    - Schedule-triggered rotation in `JSONFileHandler` names rotated archives after the elapsed period key rather than the newly entered period key.
    - Invalid `LoggingConfig` levels such as `bool` (`True`/`False`) or non-level `logging` attributes (`"BASIC_FORMAT"`) now raise `ValueError`.
- **Dependencies**: Zero new runtime or development dependencies (`rich` remains the sole core runtime dependency).
