# Design

## Context

See `proposal.md` for motivation and scope. Five core files (`src/arlogi/config.py`, `config_builder.py`, `factory.py`, `handler_factory.py`, `handlers.py`) currently contain uncommitted working-tree edits introducing `json_file_base_dir` / `base_dir`, `markup=False` in `ColoredConsoleHandler`, and `sys.modules`-only `is_test_mode()`. Two OpenTelemetry files (`src/arlogi/otel/bootstrap.py`, `src/arlogi/otel/exporters.py`) also have uncommitted working-tree edits that belong to Wave 2 and MUST remain untouched during Wave 1 implementation. Core `arlogi` depends strictly on Python `>=3.13` stdlib plus `rich` (`no-otel` invariant `INV-7`/`INV-9`), and `.ruff.toml` enforces `C901` McCabe complexity `<= 10`.

## Goals / Non-Goals

**Goals:**

- Establish deterministic, race-free locking and resource lifecycle invariants across `LoggerFactory`, `HandlerFactory`, `JSONHandler`, and `JSONFileHandler`.
- Guarantee fail-fast validation at configuration/initialization boundaries (`ValueError`/`TypeError`) while enforcing fail-open, non-crashing degradation at runtime log emission, rotation, and retention pruning boundaries.
- Eliminate shared-dict mutation, call-site misattribution, and JSON envelope spoofing without adding runtime overhead on disabled log levels or introducing new dependencies.

**Non-Goals:**

- Modifying `src/arlogi/otel/*` or OTel test fixtures in `tests/conftest.py` (deferred to Wave 2).
- Modifying `.github/workflows/*`, `pyproject.toml` packaging targets, or Markdown documentation guides under `docs/` and `README.md` (deferred to Wave 3; only Python docstrings in touched core modules are aligned here).

## Decisions

### 1. Unified Level Parsing & Dataclass Introspection in `LoggingConfig`

- **Choice**: Extract a single helper `_parse_level(level: int | str) -> int` used by `_validate_level()`, `resolved_level`, and `resolve_module_level()`. Reject `isinstance(level, bool)` explicitly before checking `isinstance(level, int)`. For strings, map `"TRACE"` directly to `TRACE_LEVEL_NUM` (`5`) without requiring `register_trace_level()` to have run, and validate other uppercase names against an explicit integer level table (`logging.getLevelNamesMapping()` excluding `"NOTSET"`, verifying integer type). Validate `rotate_retention_count` with `isinstance(val, int) and not isinstance(val, bool) and val >= 1` (raising `ValueError` on strings, floats, booleans, or `< 1`). Derive `to_dict()` and `from_kwargs()` valid keys from `dataclasses.fields(cls)`. In `LoggingConfigBuilder`, initialize `self._level: int | str = logging.INFO` (`20`), annotate `self._rotate_schedule: RotateSchedule | None = None`, and set `self._json_file_name = None` inside `with_json_console_only()`.
- **Alternatives considered**: Calling `register_trace_level()` eagerly inside `LoggingConfig.__post_init__()` — rejected because constructing an immutable value object should remain side-effect-free with respect to global `logging` state.

### 2. Sentinel-Guarded `setup_logging(config=...)` and `LoggerFactory.apply_config()`

- **Choice**: Export `LoggingConfigBuilder` in `src/arlogi/__init__.py` (`__all__`). Add `LoggerFactory.apply_config(cls, config: LoggingConfig) -> None` that acquires `cls._init_lock` (`threading.RLock`) around `cls._apply_configuration(config)` (and acquire `cls._init_lock` inside `_apply_configuration` itself so existing internal/test callers are also protected). Extend `LoggerFactory.setup()` and `setup_logging()` with `config: LoggingConfig | None = None` while using an internal `_UNSET` sentinel (or explicit keyword-presence check) so passing both `config=...` and any explicit keyword override raises `ValueError`.
- **Alternatives considered**: Allowing keyword arguments to override fields on a passed `config` via `dataclasses.replace()` — rejected because silent partial overrides mask configuration mistakes and complicate default-value detection; `LoggingConfigBuilder` or `dataclasses.replace()` at the call site is clearer.

### 3. Concurrency, Lock Ordering & Create-Before-Detach Handler Replacement

- **Choice**:
  - **Locking**: Use `LoggerFactory._init_lock` (`threading.RLock`) for root initialization/reconfiguration and `TRACE`/`TraceLogger` registration, and a dedicated `_dedicated_lock = threading.RLock()` on `LoggerFactory` to serialize `get_json_logger()`, `get_syslog_logger()`, `cleanup_json_logger()`, `cleanup_syslog_logger()`, and `rotate_json_logger()`. Acquire `_init_lock` before `_dedicated_lock` (or call `_initialize_trace_level()` first) so lock acquisition order is strictly acyclic and never holds `_dedicated_lock` across arbitrary user callbacks.
  - **Lazy dedicated teardown**: In `cleanup_json_logger()`, `cleanup_syslog_logger()`, and `rotate_json_logger()`, check `logger_name in logging.Logger.manager.loggerDict` (and ensure the entry is an actual `logging.Logger`, not a `PlaceHolder`) before calling `logging.getLogger(logger_name)`, returning early if uncreated (`0` for `rotate_json_logger`).
  - **Create-before-detach-and-close**:
    1. In `HandlerFactory.create_handlers(config)`, wrap construction in `try/except`: if creating a subsequent handler raises (e.g., invalid explicit `syslog_address`), close every handler already appended before re-raising.
    2. In `LoggerFactory._clear_and_add_handlers(config)`, call `new_handlers = HandlerFactory.create_handlers(config)` *before* touching `root.handlers`. Once creation succeeds, detach each old handler via `root.removeHandler(old)`, attach `new_handlers`, and then call `old.close()` on each detached old handler.
    3. Apply the exact same create-new -> `removeHandler(old)` -> `addHandler(new)` -> `old.close()` sequence inside `get_json_logger()` (which also accepts optional `base_dir: str | Path | None = None`) and `get_syslog_logger()`, and detach before `close()` in `cleanup_json_logger()` / `cleanup_syslog_logger()`. Snapshot `list(logger.handlers)` under `_dedicated_lock` in `rotate_json_logger()`.
- **Alternatives considered**: Closing handlers before calling `removeHandler()` — rejected because `logging.Logger.callHandlers()` does not hold the factory lock, allowing a concurrent `emit()` on an attached `mode='a'` `JSONFileHandler` to see `self.stream is None` and silently reopen the closed file descriptor.

### 4. `TraceLogger` Fast Path, Non-Mutating `extra`, and Frame-Depth Math

- **Choice**:
  - **Fast path (`isEnabledFor`)**: Check `self.isEnabledFor(level)` at the top of `trace`, `debug`, `info`, `warning`, `error`, `critical`, `fatal`, `exception`, and `log` (validating `isinstance(level, int)` in `log` per stdlib behavior) *before* invoking `_process_params()`.
  - **Non-mutating `extra`**: When `custom_kwargs` is non-empty:
    - If `extra is None` (or omitted): set `kwargs["extra"] = dict(custom_kwargs)` (no `_original_extra`).
    - If `isinstance(extra, collections.abc.Mapping)`: set `kwargs["extra"] = {**extra, **custom_kwargs}` (never mutating `extra` in place; supports `MappingProxyType` and custom mappings).
    - Otherwise (non-mapping scalar/object): preserve `kwargs["extra"] = {"_original_extra": extra, **custom_kwargs}` for backward compatibility with existing edge-case callers/tests.
  - **Call-site `stacklevel` & `caller_depth`**:
    - In `_process_params()`, compute `raw_sl = kwargs.get("stacklevel", 1)` and set `kwargs["stacklevel"] = (raw_sl + 1) if isinstance(raw_sl, int) and not isinstance(raw_sl, bool) else 2`.
    - In `TraceLogger.exception()`, check `self.isEnabledFor(logging.ERROR)`, set `kwargs.setdefault("exc_info", True)`, run `_process_params()`, and delegate directly to `super().error(msg, *args, **kwargs)` (avoiding double entry through `logging.Logger.exception() -> self.error()`).
    - Add `TraceLogger.fatal()` checking `self.isEnabledFor(logging.CRITICAL)`, running `_process_params()`, and delegating directly to `super().critical(msg, *args, **kwargs)` so frame depth matches `critical()`.
    - In `levels.py` monkey-patched `trace()`, increment `kws["stacklevel"] = kws.get("stacklevel", 1) + 1` before `self._log(...)`.
- **Alternatives considered**: Keeping `super().exception()` and adjusting `stacklevel` with a private flag — rejected because it still shifts `_get_caller_info(depth)` by an extra stack frame (`sys._getframe(depth + 3)`), whereas direct `super().error(..., exc_info=True)` keeps frame depth uniform across all methods.

### 5. `JSONFormatter` Envelope Protection & Resilient Fallback

- **Choice**:
  - Build `log_data` with the canonical envelope keys (`timestamp`, `level`, `logger_name`, `message`, `module`, `function`, `line_number`, plus `"exception"` when `record.exc_info` is set).
  - Define `_PROTECTED_ENVELOPE_KEYS = frozenset({"timestamp", "level", "logger_name", "message", "module", "function", "line_number", "exception"})` (plus `"trace_id"` and `"span_id"` only when stamped by correlation; when present on `record` without collision they remain top-level fields).
  - Scan `record.__dict__` (excluding `standard_attrs` and `"_"`-prefixed keys): non-colliding keys are placed at top level on `log_data`, while any key in `_PROTECTED_ENVELOPE_KEYS` is collected into `collisions: dict[str, Any]`. If `collisions` is non-empty and the caller also supplied a custom `"extra"` attribute on `record`, preserve that `"extra"` value under `collisions["extra"]` before setting `log_data["extra"] = collisions` so no field is silently overwritten.
  - Wrap `json.dumps(log_data, default=str)` in `except Exception as e:` (catching `TypeError`, `ValueError`, and custom `__str__` exceptions such as `RuntimeError`), and build the fallback JSON payload directly from `record` attributes (`datetime.fromtimestamp(record.created).isoformat()`, `record.levelname`, `record.name`, safe `_safe_str(record)` message, `record.module`, `record.funcName`, `record.lineno`, and `_safe_str(e)` error) with `default=str`.
- **Alternatives considered**: Dropping colliding keys silently — rejected per user design decision because preserving colliding values under `"extra": {...}` protects SIEM/audit fields without losing diagnostic data.

### 6. Synchronized, Idempotent `JSONHandler.close()`

- **Choice**: Acquire `self.acquire()` / `self.release()` across `JSONHandler.close()`. Check `stream = self.stream`: only call `self.flush()` when `stream is not None and not getattr(stream, "closed", False)`. When `self._owns_stream and stream is not None and stream not in (sys.stderr, sys.stdout)`, close `stream` (if `hasattr(stream, "close") and not getattr(stream, "closed", False)`) and set `self.stream = None` before calling `super().close()` in `finally`. Maintain a `self._closed = True` guard so subsequent `close()` calls are strict no-ops.
- **Alternatives considered**: Catching `ValueError` around `self.flush()` without locking — rejected because unlocked `stream.close()` still races with concurrent `StreamHandler.emit()` between `flush()` lock release and `stream.close()`.

### 7. `JSONFileHandler` Containment, Elapsed-Period Naming, Regex Pruning & Non-Fatal Recovery

- **Choice**:
  - **Containment (`_resolve_within_base`)**: Reject empty filenames and require `resolved != base and resolved.startswith(base_prefix)` (handling `base == os.sep` cleanly via `os.path.commonpath([base, resolved]) == base and resolved != base`) so passing `filename="."` or `filename=base_dir` raises `ValueError` before `os.makedirs` / `open`. Also mark `self._closed = False` in `__init__` and `self._closed = True` in `close()`, skipping reopen in `emit()` / `rotate_now()` once explicitly closed.
  - **Elapsed-period archive naming**: Split archive naming from state advancement in `_rotate_now_locked(self, period_key: str | None = None, *, next_active_period_key: str | None = None) -> bool`. During `emit()`, when `current_key != self._active_period_key`, pass `period_key=self._active_period_key` (the elapsed period whose events live in the file) and `next_active_period_key=current_key`. On successful `os.replace()` (or empty-file boundary advance), set `self._active_period_key = next_active_period_key or period_key`; on `PermissionError`, leave `self._active_period_key` unchanged so the boundary rotation retries on the next `emit()`. Direct callers of `_rotate_now_locked()` or `_rotate_now_locked("2026-01-01-00")` retain backward-compatible behavior.
  - **Exact retention pruning (`_prune_rotated_files`)**: Replace `glob(f"{root}-*{ext}")` with `os.scandir(parent_dir)` and an anchored compiled regex `rf"^{re.escape(stem)}-(?:\d{{4}}-\d{{2}}(?:-\d{{2}}(?:-\d{{2}})?)?|\d{{4}}-W\d{{2}})(?:\.\d+)?{re.escape(ext)}$"`. Collect `(entry.stat().st_mtime, entry.path)` inside a per-entry `try/except OSError` loop (ignoring vanished files or dangling symlinks without aborting) and wrap the entire `_prune_rotated_files()` method in `try/except OSError` so pruning never alters `_rotate_now_locked()`'s `True` return status after `os.replace()` has already succeeded.
  - **Guarded stream recovery**: Make `_ensure_stream_open()` (or a `_try_ensure_stream_open()` helper used in `_rotate_now_locked()`'s empty-file branch and `except PermissionError` / `except Exception` blocks) catch `OSError` and report via `self.handleError(...)` instead of letting `_open()` failures escape `rotate_now()` and `rotate_json_logger()`. Keep each helper small so all methods stay well within Ruff's `C901 <= 10` limit.
- **Alternatives considered**: Using `glob.escape(root) + "-*" + glob.escape(ext)` alone — rejected because a wildcard `*-*` still matches sibling hyphenated loggers (e.g., `app-audit.jsonl` alongside `app.jsonl`).

## Risks / Trade-offs

- **[Archive filename shift on schedule boundary]** -> Existing operational scripts expecting the buggy new-period archive name (e.g., `app-2026-06-11.jsonl` for June 10 logs) will now see `app-2026-06-10.jsonl`. Mitigation: Existing unit tests only assert archive count, and elapsed-period naming matches standard log-rotation conventions and eliminates `.1` collisions with manual `rotate_now()`.
- **[`ColoredConsoleHandler` defaults `markup=False`]** -> Callers embedding Rich tags directly in log strings without passing `markup=True` will see literal brackets. Mitigation: Preserves explicit `ColoredConsoleHandler(markup=True)` opt-in while enforcing `INV-4` injection safety by default.
- **[Existing unit tests coupled to internal mocks]** -> `tests/test_coverage_boost.py:156` asserts exact `_log` kwargs without `stacklevel=2`, and `tests/test_coverage_boost.py:273` patches `glob.glob` for `_prune_rotated_files()`. Mitigation: Update those unit tests alongside the implementation to assert the hardened contracts directly against real temp directories and `stacklevel=2`.
- **[Uncommitted Wave 2 OTel changes in working tree]** -> `src/arlogi/otel/bootstrap.py` and `src/arlogi/otel/exporters.py` currently have uncommitted edits. Mitigation: Wave 1 tasks explicitly restrict file edits to core `src/arlogi/*.py` and core `tests/test_*.py`, leaving `src/arlogi/otel/*` untouched.

## Migration Plan

1. Consolidate and complete the Wave 1 implementation across the core modules (`__init__.py`, `config.py`, `config_builder.py`, `levels.py`, `types.py`, `handler_factory.py`, `handlers.py`, `factory.py`) without touching `src/arlogi/otel/*`.
2. Add comprehensive unit, subprocess-isolation (fresh-process `get_json_logger`/`get_syslog_logger` and `PYTEST_CURRENT_TEST` spoofing), and multi-threaded stress tests covering all 12 Wave 1 audit findings.
3. Verify zero regressions across `uv run pytest`, `uv run ruff check` (on Wave 1 files), and `uv run ruff format --check` (on Wave 1 files).
