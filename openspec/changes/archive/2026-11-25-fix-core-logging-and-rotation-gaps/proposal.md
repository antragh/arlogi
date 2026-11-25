# Proposal

## Why

The verified deep audit `docs/_audit_/2611250738-deep-audit.json` (against commit `c6f137b`) confirmed a set of defects in the zero-OTEL core: archive misnaming on manual JSON rotation, file-descriptor and socket leaks on handler close and construction, silent configuration drops (default-equal overrides, empty `json_file_name`), a zero-handler window during reconfiguration that leaks raw records to `logging.lastResort`, incomplete `TRACE` registration, and two duplicated, diverged archive-pruning loops that evict real archives when directories, symlinks, or equal mtimes are present. Each finding was re-verified against the current code on disk (unchanged since `c6f137b`) and reproduced read-only before drafting this change.

## What Changes

Findings covered (all confirmed still present; none excluded):

- **DA-001** – `JSONFileHandler` manual rotation (`rotate_now()` / `rotate_json_logger()`): unscheduled handlers always name archives after the current hour and never persist a period key; scheduled handlers archive post-boundary content under the elapsed active period key.
- **DA-004** – `JSONHandler.close()` always closes an owned stream and clears it even when `flush()` raises; explicitly passed `sys.stderr`/`sys.stdout`/`sys.__stderr__`/`sys.__stdout__` are never treated as owned or closed, including under stream redirection.
- **DA-005** – `TRACE` registration repairs each missing piece independently (level name, `logging.TRACE`, `logging.Logger.trace`) instead of returning early when `logging.TRACE` already exists; the patched `Logger.trace` accepts `msg` as its first parameter name.
- **DA-008** – `JSONFileHandler` validates `rotate_schedule` (including rejecting `""`) and `rotate_retention_count` before creating directories or opening files.
- **DA-009 / DA-025 / DA-026** – both pruning loops (`JSONFileHandler._prune_rotated_files()` and `_RotatingJsonlWriter._prune()`) delegate to one stdlib-only core helper that counts only regular files (no directories or symlinks), orders deterministically by `(st_mtime_ns, timestamp key, numeric collision suffix)`, excludes the active file by resolved path, and remains non-fatal on `OSError`.
- **DA-012** – root and dedicated logger handler replacement and cleanup swap `logger.handlers` atomically under the factory lock, eliminating the zero-handler window and in-place list mutation during concurrent emission.
- **DA-013** – `setup_logging()` / `LoggerFactory.setup()` detect explicit overrides combined with `config=` via a typed private sentinel, so default-equal explicit overrides also raise `ValueError`.
- **DA-017** – `caller_depth` values that are booleans or negative integers disable attribution instead of exposing internal frames.
- **DA-018** – `get_logger(name, level=...)` resolves levels through the same validation as `LoggingConfig` (case-insensitive names, `TRACE`, booleans rejected).
- **DA-020 / DA-021** – empty, whitespace-only, or non-`str` `json_file_name` is rejected wherever a JSON file name is accepted (`LoggingConfig`, `get_json_logger()`), downstream checks use `is not None` instead of truthiness, and `LoggingConfigBuilder.with_json_console_only()` also clears the JSON base directory.
- **DA-022** – `ArlogiSyslogHandler.close()` releases the socket even after `emit()` marked the handler failed post-initialization.

## Non-goals

- Findings **DA-002, DA-006, DA-007, DA-010, DA-011, DA-019** are owned by sibling change `fix-otel-lifecycle-gaps`. That change MUST NOT touch archive pruning; this change only replaces the body of `_RotatingJsonlWriter._prune()` and does not alter OTEL bootstrap, exporter, or decorator lifecycle.
- Findings **DA-003, DA-014, DA-015, DA-016, DA-023, DA-024** and graphify removal are owned by sibling change `remove-graphify-and-sync-ci-docs`, which will also refresh user-facing docs (`docs/API_REFERENCE.md`, `docs/CONFIGURATION_GUIDE.md`) for the behavior changed here. This change does not edit `docs/`, CI workflows, or packaging.
- Rejecting `json_file_base_dir` when `json_file_name` is `None` in `LoggingConfig` (optional audit suggestion) is out of scope.
- No new public API, no new runtime dependencies, no changes to coerced numeric-string `caller_depth` handling.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `json-handlers-and-rotation`: manual-rotation archive naming (DA-001), JSON stream closure on flush failure and system-stream ownership (DA-004), constructor validation before I/O (DA-008), deterministic regular-file-only pruning (DA-009/025), syslog socket release (DA-022).
- `logger-lifecycle`: atomic handler-list swap (DA-012), self-healing `TRACE` registration and `msg` keyword (DA-005), boolean/negative `caller_depth` rejection (DA-017).
- `logging-configuration`: sentinel-based override detection (DA-013), `get_logger()` level resolution (DA-018), non-empty JSON file name validation and console-only base-dir reset (DA-020/021).
- `otel-file-exporters`: shared pruning semantics for `_RotatingJsonlWriter` (DA-009/026) only.

## Impact

- **Code**: `src/arlogi/handlers.py`, `src/arlogi/factory.py`, `src/arlogi/levels.py`, `src/arlogi/config.py`, `src/arlogi/config_builder.py`, `src/arlogi/handler_factory.py`, `src/arlogi/otel/_files.py` (prune delegation only), new internal module `src/arlogi/_rotation.py` (stdlib-only, no `opentelemetry` imports).
- **Tests**: regression tests in `tests/test_file_rotation.py`, `tests/test_resource_management.py`, `tests/test_thread_safety.py`, `tests/test_core.py`, `tests/test_features.py`, `tests/test_rotation_config.py`, `tests/test_otel_exporter.py` (OTEL-guarded).
- **Behavioral compatibility impact** (intentional, fail-fast at construction/configuration time):
  - `JSONFileHandler(...)` now raises `ValueError` for `rotate_schedule=""` or any unsupported value and for `rotate_retention_count` that is `0`, negative, boolean, or non-integer (previously accepted, leading to data loss or a leaked descriptor).
  - `setup_logging(config=cfg, level=logging.INFO)` (or any explicit default-equal keyword alongside `config`) now raises `ValueError` instead of silently ignoring the override. Signature defaults of `setup_logging()` / `LoggerFactory.setup()` become a private sentinel (introspection shows the sentinel; calling behavior without `config` is unchanged).
  - `get_logger(name, level="debug")` / `"trace"` now succeed; `level=True`/`False` now raise `ValueError`. The string `"NOTSET"` stays accepted for `get_logger()` to preserve the stdlib reset idiom.
  - `LoggingConfig(json_file_name="")` and `get_json_logger(name, "")` now raise `ValueError` instead of silently dropping file output or falling back to stderr.
  - `LoggingConfigBuilder.with_json_console_only()` now also resets `json_file_base_dir` to `None`.
  - The monkey-patched `logging.Logger.trace` first parameter is renamed `message` → `msg`; callers using `trace(message=...)` keyword must switch to `msg=` (positional calls are unaffected).
  - Unscheduled `JSONFileHandler` archives are now named after the hour in which each manual rotation happens (no more frozen `.1`, `.2` suffix chains).
