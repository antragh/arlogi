# Proposal

## Why

The verified deep repository audit `docs/_audit_/2611250948-deep-audit.json` (on `master` @ `c6f137b`) confirmed `19` findings (`1` High, `10` Medium, `8` Low) and `2` cross-module failure chains across Python 3.13 syslog error handling, handler/exporter close lifecycle, OpenTelemetry proxy/endpoint/correlation edge cases, configuration validation, and published MkDocs/C4 documentation sync. Addressing all `19` findings together eliminates both compound file-descriptor leak chains and brings code, tests, specs, and published documentation into alignment.

## What Changes

Findings covered (all `19` confirmed findings and both compound failure chains from `docs/_audit_/2611250948-deep-audit.json`):

- **DA-001** (`src/arlogi/handlers.py`): Fix `ArlogiSyslogHandler` on Python 3.13 where stdlib `SysLogHandler.createSocket()` swallows `OSError` on Unix sockets and `SysLogHandler.emit()` catches exceptions via `handleError()` without re-raising. Verify socket liveness after `super().__init__()` so stale/unreadable `"/dev/log"` triggers the `("localhost", 514)` fallback and `_failed = True` degradation while custom non-`"/dev/log"` Unix socket paths fail fast with `OSError`; latch `_failed = True` and close the socket on transport `OSError` in `emit()`/`handleError()`. **BREAKING** for callers passing nonexistent/unreadable custom Unix socket paths (now raises `OSError` instead of silently returning a closed socket).
- **DA-007 & CHAIN-01** (`src/arlogi/handlers.py`, `src/arlogi/factory.py`): Add `_closed` guards to `ArlogiSyslogHandler` (`close()` / `emit()`) and `JSONHandler` (`emit()`) so concurrent emissions already inside `logging.Logger.callHandlers()` during `LoggerFactory._swap_handlers()` never reopen closed sockets or write/raise on closed streams.
- **DA-003** (`src/arlogi/handlers.py`): Map `"TRACE"` to `"debug"` in `ArlogiSyslogHandler.priority_map` so `TRACE` (level `5`) records emit syslog `DEBUG` PRI (`<15>` for `LOG_USER`) rather than defaulting to `WARNING` (`<12>`).
- **DA-004** (`src/arlogi/handlers.py`): In `JSONFileHandler._rotate_now_locked()`, advance `_active_period_key` and invoke `_prune_rotated_files()` immediately after `os.replace()` succeeds and before `_open()`, preventing stale-period `.1` archives from evicting legitimate archives and avoiding duplicate `_report_rotation_error()` calls.
- **DA-002, DA-018, DA-019** (`src/arlogi/config.py`, `src/arlogi/handlers.py`, `src/arlogi/factory.py`, `src/arlogi/handler_factory.py`): Consolidate `json_file_name`, `base_dir` / `json_file_base_dir`, `rotate_schedule`, and `rotate_retention_count` validation into shared helpers in `src/arlogi/config.py`; require `base_dir` (when not `None`) to be a non-empty, non-whitespace `str`/`Path` without NUL bytes; validate `filename` in `JSONFileHandler` even when `base_dir is None`; check `isinstance(..., str)` before `VALID_ROTATE_SCHEDULES` lookup so unhashable inputs raise `ValueError` instead of `TypeError`; and unify `"Invalid rotate_schedule"` wording. **BREAKING** for callers relying on `""`/`"   "`/non-path `base_dir`, invalid `JSONFileHandler` filenames without `base_dir`, or `TypeError` on unhashable `rotate_schedule`.
- **DA-005** (`src/arlogi/otel/bootstrap.py`, `tests/conftest.py`): In `_clear_global_meter_provider()`, iterate `proxy._meters` (under `proxy._lock` -> `meter._lock`) and clear `_real_meter = None` and each instrument's `_real_instrument = None` so instruments created during shutdown-to-restart gaps on pre-existing module-level meters upgrade cleanly when `setup_metrics()` restarts.
- **DA-006, DA-013 & CHAIN-02** (`src/arlogi/otel/_files.py`): Add a `_closed` flag to `_RotatingJsonlWriter` (set under `_lock` in `close()` alongside clearing `_active_path = None`) so post-shutdown `write_line()` calls return `False` (`FAILURE` in span/metric exporters) without reopening files or leaking FDs; and best-effort close/clear `self._stream` on write/flush `OSError` when setting `_broken = True`.
- **DA-008** (`src/arlogi/otel/bootstrap.py`): Update `_child_factories()` to inspect callable values in `node.args` and `node.keywords` for `functools.partial` wrappers so `install_log_correlation()` remains idempotent across partial-wrapped factories.
- **DA-011** (`src/arlogi/otel/bootstrap.py`): Tighten `_validate_otlp_endpoint()` to reject `'?'`, `'#'`, and `';'` anywhere in the endpoint, reject dangling empty port separators (`':'`), and require `1 <= port <= 65535` (rejecting port `0`); invoke validation whenever `otlp_endpoint is not None and otlp_endpoint != ""` (so `None` and `""` disable remote OTLP export for file-only operation while whitespace `" "`, falsy non-strings, and malformed URLs raise `ValueError`). **BREAKING** for callers passing trailing empty `?`/`#`/`;`, dangling `:`, `:0`, or falsy non-strings.
- **DA-014** (`src/arlogi/otel/decorator.py`): Skip caching `(current_provider, tracer)` in `_make_tracer_getter()` when `isinstance(current_provider, trace.ProxyTracerProvider)` so concurrent `setup_tracing()` or `ProxyTracer` latching cannot retain a shut-down SDK tracer under `_PROXY_TRACER_PROVIDER`.
- **DA-009, DA-010, DA-012, DA-015, DA-016, DA-017** (`docs/`, `README.md`, `mkdocs.yml`):
  - Delete `docs/C4-Documentation/c4-code-docs-scripts.md` and `docs/C4-Documentation/c4-code-subdir.md` and remove them from `mkdocs.yml`; scrub internal LAN IP (`192.168.168.5`), internal URL, SSH user/key/docroot (`root`, `$HOME/.ssh/il-ed25519`, `/opt/c/nginx/html/arlogi`), and local workstation paths (`/opt/Code/2026/_Libs/arlogi/...`) from remaining `docs/C4-Documentation/` files and `README.md`.
  - Synchronize `docs/C4-Documentation/`, `docs/C4-Documentation/apis/arlogi-api.yaml`, `docs/ARCHITECTURE.md`, and `docs/API_REFERENCE.md` with runtime JSON envelope keys (including `exception`), `caller_depth`, `sys.modules`-only `is_test_mode()`, `stderr` output for `get_json_logger`, atomic handler rollback/re-raise, and per-address syslog error semantics.
  - Update `docs/DEVELOPER_GUIDE.md` commands, CI YAML snippet, and Release Checklist to match `.github/workflows/ci.yml`, `.github/workflows/publish.yml`, and `CLAUDE.md`.
  - Fix runnable snippets in `docs/CONFIGURATION_GUIDE.md` (`get_logger` import + `logger.addFilter`), `docs/API_REFERENCE.md` (`json_file_name="app.jsonl"`), and `docs/CALLER_ATTRIBUTION_EXAMPLES.md` (`caller_depth=2` comment).
  - Add `SyslogJSONFormatter` to `README.md` and prose syslog JSON/transport guidance to `docs/ARCHITECTURE.md`.
  - Fix broken `#jsonhandler` anchors in `docs/index.md` and `docs/C4-Documentation/c4-container.md`, and set `validation.links.anchors: warn` in `mkdocs.yml` so `mkdocs build --strict` enforces heading anchors.

## Non-goals

- No new public functions, classes, or optional extras in `arlogi` or `arlogi.otel`.
- No changes to the minimal `rich`-only core dependency invariant or lazy `arlogi.otel` import boundary.
- No changes to `.github/workflows/*.yml` or `pyproject.toml` packaging rules (audited compliant with `ci-and-packaging`).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `logging-configuration`: Shared validation for `json_file_base_dir` / `base_dir`, `json_file_name`, `rotate_schedule` (including unhashable inputs), and `rotate_retention_count`.
- `json-handlers-and-rotation`: Python 3.13 `ArlogiSyslogHandler` `/dev/log` fallback, custom Unix socket fail-fast `OSError`, transport `OSError` degradation, `_closed` guards on `ArlogiSyslogHandler` and `JSONHandler`, `TRACE` syslog priority mapping, post-`os.replace()` state/pruning ordering in `JSONFileHandler`, and pre-side-effect `filename`/`base_dir`/rotation validation.
- `logger-lifecycle`: Concurrent `get_syslog_logger()` handler swap safety against reopened sockets and `get_json_logger()` `base_dir` validation.
- `otel-lifecycle`: Proxy-provider cache exclusion in `@traced`, strict OTLP endpoint validation (`""`/`None` disabled; `" "`/falsy non-strings/`?`/`#`/`;`/empty `:`/port `0` rejected), pre-existing `_ProxyMeter` / `_ProxyInstrument` reset across shutdown gaps, and `functools.partial` argument traversal in `install_log_correlation()`.
- `otel-file-exporters`: `_closed` post-shutdown rejection in `_RotatingJsonlWriter` and immediate stream closure on write/flush `OSError`.
- `documentation-sync`: Scrubbing internal host/workstation metadata and removing stale C4 pages for ignored folders, syncing C4/architecture/API/developer docs and runnable examples, adding `SyslogJSONFormatter` prose, fixing broken `#jsonhandler` anchors, and enforcing `validation.links.anchors: warn` in `mkdocs.yml`.

## Impact

- **Code**: `src/arlogi/config.py`, `src/arlogi/handlers.py`, `src/arlogi/factory.py`, `src/arlogi/handler_factory.py`, `src/arlogi/otel/bootstrap.py`, `src/arlogi/otel/decorator.py`, `src/arlogi/otel/_files.py`.
- **Docs & Config**: `README.md`, `mkdocs.yml`, `docs/index.md`, `docs/API_REFERENCE.md`, `docs/ARCHITECTURE.md`, `docs/CONFIGURATION_GUIDE.md`, `docs/CALLER_ATTRIBUTION_EXAMPLES.md`, `docs/DEVELOPER_GUIDE.md`, `docs/C4-Documentation/` (including deleting `c4-code-docs-scripts.md` and `c4-code-subdir.md`).
- **Tests**: `tests/conftest.py`, `tests/test_coverage_boost.py`, `tests/test_rotation_config.py`, `tests/test_syslog_json_format.py`, `tests/test_file_rotation.py`, `tests/test_resource_management.py`, `tests/test_thread_safety.py`, `tests/test_otel_bootstrap.py`, `tests/test_otel_decorator.py`, `tests/test_otel_exporter.py`, `tests/test_otel_metrics.py`, `tests/test_docs_examples.py`.
- **Behavioral compatibility**:
  - `ArlogiSyslogHandler` with an invalid/nonexistent non-`/dev/log` Unix socket path now raises `OSError` instead of silently succeeding on Python 3.13.
  - `LoggingConfig`, `get_json_logger()`, and `JSONFileHandler` reject `""`, whitespace, NUL bytes, and non-`str`/`Path` values in `base_dir`/`json_file_base_dir` (and `JSONFileHandler` validates `filename` even when `base_dir is None`) with `ValueError`.
  - Unhashable `rotate_schedule` raises `ValueError` instead of `TypeError`, and `JSONFileHandler` aligns its error text on `"Invalid rotate_schedule"`.
  - `ArlogiSyslogHandler` emits `TRACE` records at syslog `DEBUG` priority (`<15>`) instead of `WARNING` (`<12>`).
  - `setup_tracing()` / `setup_metrics()` treat `otlp_endpoint=""` identically to `None` (file-only export) while rejecting `" "`/whitespace, falsy non-strings (`0`, `False`), `?`/`#`/`;`, empty `:`, and `:0` with `ValueError`.
  - `RotatingJsonlSpanExporter` / `RotatingJsonlMetricExporter` return `FAILURE` on `export()` calls after `shutdown()` instead of reopening files.
