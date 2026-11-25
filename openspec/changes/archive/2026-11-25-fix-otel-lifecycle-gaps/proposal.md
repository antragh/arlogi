# Proposal: Fix OpenTelemetry Lifecycle Gaps

## Why

The verified deep audit `docs/_audit_/2611250738-deep-audit.json` confirmed six defects in the optional `arlogi.otel` subpackage where toggling observability configuration, restarting providers in-process, or sharing a telemetry directory silently breaks host-application semantics, drops telemetry permanently, or writes files outside the configured directory. Two of them (DA-010 and DA-006) compound into attack chain CHAIN-03, which can wedge the metrics pipeline or turn every meter acquired during a restart gap into a permanent no-op.

## What Changes

- **DA-002 (high)** — A `@traced` async generator whose module is gated off via `set_trace_modules()` SHALL forward `asend()`, `athrow()`, and `aclose()` to the inner generator exactly as the traced path does (today the `async for` fallback discards sent values, bypasses the inner `except` handlers, and skips the inner `finally` on early close).
- **DA-007 (medium)** — Inner generator cleanup triggered by early `close()` / `aclose()` SHALL run with the generator span active, and exceptions raised by that cleanup SHALL be recorded on the span (exception event + `ERROR` status) before propagating.
- **DA-019 (low)** — The per-decorator tracer cache SHALL publish provider and tracer as a single immutable pair and obtain the tracer from the provider it is keyed on, so concurrent callers can never observe a new provider paired with a stale tracer.
- **DA-006 (medium)** — Releasing the global `MeterProvider` slot during `shutdown_metrics()` SHALL also unbind the OpenTelemetry API's proxy meter provider from the shut-down provider, so `metrics.get_meter()` calls made between shutdown and the next `setup_metrics()` return upgradable proxy meters. The test-suite reset helper (`tests/conftest.py::reset_otel_globals`) is aligned.
- **DA-010 (medium)** — `shutdown_tracing()` and `shutdown_metrics()` SHALL always clear arlogi's cached provider and release the global slot even when the provider's own `shutdown()` raises; the original exception still propagates to the caller after cleanup.
- **DA-011 (medium, CWE-59)** — `_RotatingJsonlWriter` SHALL create each new JSONL file atomically and exclusively without following symlinks, advancing the `.N` collision suffix on any pre-existing entry (regular file, live symlink, dangling symlink, directory). This removes the out-of-directory write, the permanent `_broken` latch caused by a stale dangling symlink, and the cross-process same-second append collision.

No **BREAKING** public API changes. Observable behavior changes are limited to the defect fixes above: gated-off async generators now honor `asend`/`athrow`/`aclose`; generator cleanup errors now mark spans `ERROR`; shutdown functions leave the module restartable after a failing `shutdown()`; telemetry files are never created through symlinks.

## Verification of Findings Against Current Code

All six findings were re-verified against the working tree and the installed `opentelemetry-api` / `opentelemetry-sdk` 1.44.0 in `.venv`; none are already fixed and none are excluded:

- DA-002: `src/arlogi/otel/decorator.py:93-96` still uses `async for item in fn(...): yield item` when gated off.
- DA-007: `decorator.py:119-123` and `161-165` call `await gen.aclose()` / `gen.close()` in the outer `finally` outside `trace.use_span(...)` and outside the `except Exception` recorder.
- DA-019: `decorator.py:40-49` keeps two `nonlocal` variables and calls `trace.get_tracer(module)` (re-reads the global provider) after publishing `cached_provider`.
- DA-006: `src/arlogi/otel/bootstrap.py:77-91` resets only `_METER_PROVIDER_SET_ONCE` and `_METER_PROVIDER`; `opentelemetry.metrics._internal._ProxyMeterProvider` exposes `_lock` and `_real_meter_provider`, the latter set by `_set_meter_provider()` and consulted first by `get_meter()`. `tests/conftest.py:33-36` has the same gap.
- DA-010: `bootstrap.py:163-169` and `305-311` call `provider.shutdown()` before clearing state, with no `try/finally`; SDK `MeterProvider.shutdown()` sets `_shutdown = True` before raising and `SynchronousMultiSpanProcessor.shutdown()` propagates processor exceptions.
- DA-011: `src/arlogi/otel/_files.py:85-90` loops on `Path.exists()` (false for dangling symlinks) and then calls `target.open("a")`.

## Non-Goals

- Archive pruning (`_RotatingJsonlWriter._prune()` in `src/arlogi/otel/_files.py` and pruning in `src/arlogi/handlers.py`): findings DA-009, DA-025, and DA-026 are owned by the sibling change `fix-core-logging-and-rotation-gaps`, which introduces a shared `src/arlogi/_rotation.py` pruning helper. This change MUST NOT modify `_prune()` or the "Non-fatal, exact-pattern retention pruning" requirement.
- All other core logging findings in the audit (owned by `fix-core-logging-and-rotation-gaps`).
- CI, documentation, and graphify cleanup (owned by `remove-graphify-and-sync-ci-docs`).
- Directory ownership/permission checks on `file_dir`, retry/backoff policies for failing exporters, and swallowing shutdown errors (see design.md decision on fail-fast).
- Any new runtime dependency or any change to the `arlogi[otel]` optional-dependency boundary.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `otel-lifecycle`: tightens tracer-cache consistency under concurrent provider swaps; extends generator lifecycle forwarding to the gated-off path; adds span-context and error-recording guarantees for generator cleanup; extends the global-slot release requirement to the proxy meter provider; adds a requirement that shutdown always leaves the module restartable even when provider shutdown fails.
- `otel-file-exporters`: adds a requirement for exclusive, symlink-safe creation of new rotating JSONL files (file-open/creation only; pruning requirements unchanged).

## Impact

- Code: `src/arlogi/otel/decorator.py` (generator wrappers, `_make_tracer_getter`), `src/arlogi/otel/bootstrap.py` (`_clear_global_meter_provider`, `shutdown_tracing`, `shutdown_metrics`), `src/arlogi/otel/_files.py` (`_open_new_file` only).
- Tests: `tests/test_otel_decorator.py`, `tests/test_otel_bootstrap.py`, `tests/test_otel_metrics.py`, `tests/test_otel_exporter.py`, and the `reset_otel_globals` fixture in `tests/conftest.py`.
- Dependencies: none added. `arlogi.otel.decorator` stays dependent on `opentelemetry-api` only; core (`no-otel`) installs are unaffected.
- Public API: unchanged signatures; behavior changes limited to the defect fixes listed above.
