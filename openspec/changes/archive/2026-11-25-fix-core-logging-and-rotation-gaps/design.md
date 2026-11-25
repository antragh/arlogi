# Design

## Context

See proposal.md – Why. All cited findings were re-verified on the current tree (identical to `c6f137b` for the touched files) and reproduced read-only (e.g. three unscheduled rotations producing `audit-2026-06-10-10{,.1,.2}.jsonl`, `JSONHandler.close()` leaving a `BrokenPipeError` stream open, `JSONFileHandler(..., rotate_schedule="invalid")` leaving `sub/` behind, `LoggingConfig(json_file_name="")` yielding only a console handler, `get_logger("x", level="debug")` raising).

Constraints that shape the approach:

- The core package must stay importable without the `otel` extra; CI runs a "Core Only (no-otel)" matrix job (`uv sync --frozen --group test`) and a full job with `--extra otel`.
- `ruff` enforces `max-complexity=10`, so fixes favor small helpers over growing existing methods.
- Locks already in place: `LoggerFactory._init_lock` (root configuration), `LoggerFactory._dedicated_lock` (dedicated loggers), `levels._trace_lock` (TRACE registration), per-handler `Handler.lock` (`acquire()`/`release()`), and `_RotatingJsonlWriter._lock`.
- The sibling change `fix-otel-lifecycle-gaps` edits OTEL lifecycle code concurrently and must not touch pruning; the sibling `remove-graphify-and-sync-ci-docs` refreshes docs afterwards.

## Goals / Non-Goals

**Goals:**

- Fix each covered finding with a regression test encoding its audit reproduction.
- Make archive pruning a single implementation with one set of semantics for both writers.
- Prefer fail-fast at construction/configuration time and fail-open (non-fatal) at runtime I/O.

**Non-Goals:**

- No restructuring of `TraceLogger` attribution beyond the `caller_depth` guard.
- No use of private stdlib internals (`logging._lock`) for handler swapping.
- No change to `_RotatingJsonlWriter` rotation timing, broken-state handling, or close semantics (owned by the sibling OTEL change).

## Decisions

### D1. Manual rotation period keys (DA-001)

In `_rotate_now_locked()` when `period_key is None`:

- Scheduled: `current = _compute_period_key(now)`; `period_key = self._active_period_key or current`; `next_key = current`.
- Unscheduled: `period_key = now.strftime("%Y-%m-%d-%H")` every call; `self._active_period_key` stays `None` (also on the empty-file no-op path).

Emit-driven rotation keeps passing explicit `(archive_key, next_key)`. Alternative considered: exposing `rotate_schedule` on `get_json_logger()` – rejected as new API outside scope. Runs under the existing handler lock (`rotate_now()` acquires it; `emit()` is called by `Handler.handle()` under it), so no new locking.

### D2. JSONHandler stream ownership and close (DA-004)

- `_owns_stream = stream is not None and stream not in (sys.stderr, sys.stdout, sys.__stderr__, sys.__stdout__)` evaluated at construction.
- `close()` mirrors `logging.FileHandler.close()`: under the handler lock, `try: flush() finally: close owned stream (if not a system stream and not closed), set self.stream = None; super().close()`. The flush exception still propagates to the caller after cleanup (matching stdlib), so `_closed = True` is no longer a leak because the stream has been released.
- Alternative: swallow flush errors – rejected; stdlib semantics are less surprising and the factory already wraps `close()` in `try/except` during handler replacement.

### D3. JSONFileHandler constructor validation (DA-008) – fail-fast

A small static validator runs first in `__init__`, before `_resolve_within_base()`, `os.makedirs()`, and `FileHandler.__init__()`:

- `rotate_schedule is not None` → must be in `{"hour", "day", "week", "month"}` (so `""` raises).
- `rotate_retention_count is not None` → `isinstance(int) and not isinstance(bool) and >= 1`.
- Raises `ValueError`. Retention default (`7` when a schedule is set) and the `is not None` check for computing `_active_period_key` stay otherwise unchanged.

The valid-schedule set is shared with `LoggingConfig` via a module-level constant (e.g. `VALID_ROTATE_SCHEDULES` in `config.py`, imported by `handlers.py`; `config.py` does not import `handlers.py`, so no cycle).

### D4. Shared stdlib-only pruning helper (DA-009, DA-025, DA-026)

New internal module `src/arlogi/_rotation.py` (imports only `os`, `re`, `pathlib`/`typing`; never `opentelemetry`) exposing one function, conceptually:

`prune_archives(directory, pattern: re.Pattern[str], keep: int, active_path: str | os.PathLike | None = None) -> None`

- `pattern` carries named groups `stamp` (timestamp/period key) and optional `suffix` (collision number).
- Scan with `os.scandir`; skip non-matches; skip `not entry.is_file(follow_symlinks=False)`; skip entries whose `os.path.realpath()` equals the realpath of `active_path`; collect `(entry.stat(follow_symlinks=False).st_mtime_ns, stamp, int(suffix or 0), path)`.
- Sort descending by the first three fields; unlink everything after `keep`. Per-entry `OSError` on stat/unlink → skip; `OSError` on `scandir` → return. `keep <= 0` is never passed (callers validate).
- `JSONFileHandler` precompiles its pattern once in `__init__` (`^<stem>-(?P<stamp>…)(?:\.(?P<suffix>\d+))?<ext>$`) and calls the helper with `keep=rotate_retention_count`, `active_path=self.baseFilename`.
- `_RotatingJsonlWriter._prune()` becomes a one-line delegation with its existing precompiled pattern (gaining named groups) and `keep = retention_count - 1 if active else retention_count`. This is the only edit to `otel/_files.py`; the import is `from .._rotation import prune_archives` (core → no OTEL dependency direction preserved).

Alternatives: keeping two copies with patched sort keys – rejected (already diverged once); sorting by name only – rejected (mtime remains the primary recency signal per the existing specs).

### D5. Atomic handler swap (DA-012)

A single static helper on `LoggerFactory`, conceptually `_swap_handlers(logger, new_handlers) -> None`:

1. Deduplicate `new_handlers` preserving order.
2. `old = logger.handlers` (reference), then `logger.handlers = deduped` – one attribute rebinding, so concurrent `Logger.callHandlers()` iterates either the full old list or the full new list, never an empty or half-mutated one.
3. Close every handler in `old` that is not in `deduped`, each in `try/except Exception`.

Used by `_clear_and_add_handlers()` (under `_init_lock`), `_replace_logger_handlers()` (under `_dedicated_lock`), and `_detach_and_close_handlers()` (swap to `[]`, under `_dedicated_lock`). Create-before-detach is preserved because handler construction still happens before the swap. Rejected alternative: holding private `logging._lock` – undocumented API; the factory locks already serialize all arlogi mutations. Accepted residual: an emitter that loaded the old list just before the swap may still call an old handler being closed; `JSONFileHandler._closed` already prevents reopen and `JSONHandler` degrades through `handleError()`.

### D6. TRACE registration (DA-005)

Inside `_trace_lock`, each step is independent and conditional: `addLevelName(5, "TRACE")` if `getLevelName(5) != "TRACE"`; `setattr(logging, "TRACE", 5)` only if absent (never overwrite a foreign value); attach `logging.Logger.trace` only if `logging.Logger` lacks `trace` (never clobber a foreign implementation). `_trace_registered = True` is set after all three steps. The patched method signature becomes `trace(self, msg: Any, *args: Any, **kwargs: Any)`. Double-checked locking is retained.

### D7. caller_depth guard (DA-017)

In `_apply_caller_attribution()`: return `(msg, None)` if the value is a `bool`; after `int()` conversion, return `(msg, None)` if `depth < 0`. Numeric strings keep their current coercion (out of scope).

### D8. Sentinel-based override detection (DA-013) – fail-fast

A typed private sentinel (`class _Unset(enum.Enum): UNSET = enum.auto()`, `_UNSET = _Unset.UNSET`) becomes the default of every configuration parameter of `LoggerFactory.setup()` and `setup_logging()` (annotated as `T | _Unset`). With `config` set, any non-sentinel parameter → `ValueError` listing parameter names. Without `config`, sentinel entries are dropped and the remainder goes to `LoggingConfig.from_kwargs()`, making `LoggingConfig` field defaults the single source of truth; `_SETUP_DEFAULTS` is deleted. `setup_logging()` forwards arguments unchanged so sentinels propagate. Enum sentinel chosen over `object()` for precise typing under `ty`.

### D9. get_logger level resolution (DA-018)

`LoggerFactory.get_logger()` resolves a non-`None` level before `setLevel()`: case-insensitive `"NOTSET"` → `0`, otherwise `LoggingConfig._parse_level()` (exposed via a small public-in-module helper if needed to avoid calling a private static from another class). Invalid values raise `ValueError` before mutating the logger.

### D10. JSON file name handling (DA-020, DA-021) – fail-fast

- `LoggingConfig.__post_init__`: if `json_file_name is not None` and it is not a `str` or `not json_file_name.strip()` → `ValueError`.
- `LoggerFactory.get_json_logger()`: same check (it bypasses `LoggingConfig`); `base_dir` guard uses `json_file_name is None`; handler selection uses `is not None`.
- `HandlerFactory.create_handlers()`, `create_json_handler()`, `create_json_file()`: `is not None` checks (`create_json_file()` raises when `None`).
- `LoggingConfigBuilder.with_json_console_only()` also sets `_json_file_base_dir = None`.

### D11. Syslog socket release (DA-022) – fail-open

- Failed-init branch sets `self.socket = None` before `_failed = True`.
- `emit()`: when an exception escapes and `_failed` flips, close the socket under the handler lock (suppress `OSError`) and set it to `None`.
- `close()`: always delegate to `SysLogHandler.close()` (which closes a non-`None` socket under lock and calls `Handler.close()`), guarded with `getattr(self, "socket", None)` semantics; never raises.

### Error-recovery summary

| Area | Policy |
| --- | --- |
| Constructor/config validation (D3, D8, D9, D10) | Fail-fast `ValueError`, before any side effect |
| Rotation, pruning, stream reopen (D1, D4) | Fail-open: non-fatal, `rotate_now()` returns `False` on failure |
| Handler close (D2, D5, D11) | Always release resources; D2 re-raises flush errors after cleanup (stdlib parity); factory swallows close errors of replaced handlers |

### no-otel boundary

`_rotation.py` is core and stdlib-only; `otel/_files.py` depends on it, never the reverse. A no-otel regression test asserts `import arlogi; import arlogi._rotation` does not load any `opentelemetry` module, and the CI "Core Only (no-otel)" job runs the full core suite.

## Risks / Trade-offs

- [Callers relying on lenient `JSONFileHandler` arguments now get `ValueError`] → Only invalid values that previously caused data loss or descriptor leaks are rejected; documented in proposal Impact.
- [`setup_logging(config=cfg, level=logging.INFO)` now raises] → Matches the existing spec contract; error message names the offending parameters.
- [`help(setup_logging)` shows a sentinel default] → Docstrings state effective defaults; sibling docs change refreshes the API reference.
- [Patched `Logger.trace(message=...)` keyword callers break] → Rare; positional usage unaffected; aligns with `LoggerProtocol`.
- [Atomic swap could drop a handler added concurrently by third-party code via `addHandler()` between snapshot and swap] → arlogi owns root handler configuration during `setup()`; window is a single attribute read/write; documented.
- [Archive ordering for mixed-schedule archives in one directory compares period keys lexicographically] → mtime remains primary; key is only a tie-breaker.
- [Concurrent edits with `fix-otel-lifecycle-gaps` in `otel/_files.py`] → This change edits only `_prune()` and the pattern definition; merge conflicts are limited to those lines.

## Migration Plan

Single release; no data migration. Rollback is a revert of the change. Existing archives remain valid because archive naming formats and regexes are unchanged (only named groups are added).
