# Proposal

## Why

The repository deep audit (`docs/_audit_/2611242139-deep-audit.md`) uncovered high-severity reliability and security defects in `arlogi.otel`: `@traced` permanently caches decoration-time tracers (silently dropping 100% of spans after `shutdown_tracing()` / `setup_tracing()` restarts), generator wrappers leak inner generators and spans, `_RotatingJsonlWriter` accepts unvalidated `prefix` values (enabling path traversal and glob injection) and latches `_broken = True` on transient `stat()` `OSError`s, and `bootstrap.py` leaks background threads on invalid OTLP endpoints while silently caching orphaned providers. Wave 2 resolves these defects while preserving the `INV-7` SDK-free lazy import boundary.

## What Changes

- **Harden `@traced` lifecycle & reduce complexity (`DA-003`, `DA-031`, `INV-7`)**:
  - Replace decoration-time `tracer` capture with a provider-aware lookup (`(cached_provider, cached_tracer)` refreshed when `trace.get_tracer_provider()` changes) so `@traced` functions continue emitting spans across `shutdown_tracing()` / `setup_tracing()` restarts without breaking the `opentelemetry-api`-only import boundary.
  - Extract module-private wrapper builders (`_wrap_async_gen`, `_wrap_sync_gen`, `_wrap_async`, `_wrap_sync`) and `_record_span_error` in `src/arlogi/otel/decorator.py` so `traced` and `decorate` satisfy Ruff `C901 <= 10`.
  - Fix sync and async generator wrappers: construct `gen = fn(*args, **kwargs)` inside `try` (or before starting the span) so argument-binding errors do not leak open spans, close inner generators (`await gen.aclose()` / `gen.close()`) on consumer abandonment, and preserve `send()`/`asend()`, `throw()`/`athrow()`, and `StopIteration.value` return values.
- **Harden OTLP bootstrap, correlation & teardown (`DA-009`, `DA-010`, `DA-022`, `DA-024`, `INV-8`)**:
  - Strengthen `_validate_otlp_endpoint()` to reject whitespace/control characters, host-less netlocs (`parsed.hostname` required), invalid/out-of-range ports (`parsed.port`), and non-empty `params`/`query`/`fragment`.
  - Validate parameters at the top of `setup_tracing()` and `setup_metrics()` before creating providers/processors/readers, and shut down partially created components on failure so background OTEL threads never leak.
  - Check `hasattr()` in `_clear_global_tracer_provider()` / `_clear_global_meter_provider()` before mutating private OTel attributes, and verify `trace.get_tracer_provider() is provider` / `metrics.get_meter_provider() is provider` after registration (shutting down and not caching orphaned providers if an external global provider is already installed).
  - Enhance `install_log_correlation()` idempotency detection to traverse chained `LogRecord` factories (`_arlogi_prev_factory`, `__wrapped__`, `functools.partial`, `__closure__`).
  - Harden `tests/conftest.py` (`reset_otel_globals`) to restore `logging.getLogRecordFactory()`, reset `_trace_modules`, and shut down directly registered providers before clearing `_SET_ONCE` slots.
- **Harden `_RotatingJsonlWriter` & exporters (`DA-002`, `DA-006`, `INV-8`)**:
  - Validate `prefix` (must be a non-empty single filename component with no `/`, `\`, `..`, NUL bytes, or glob metacharacters) and validate `rotate_hours >= 1` and `retention_count >= 1` (rejecting `bool`/non-int).
  - Replace `Path.glob(f"{prefix}-*.jsonl")` in `_prune()` with `os.scandir()` + anchored timestamp regex (`^<escaped_prefix>-\d{8}-\d{6}(?:\.\d+)?\.jsonl$`), per-entry `try/except OSError` `stat()`, and an outer `try/except OSError` so pruning never latches `self._broken = True`.
- **Non-Goals / Out of Scope**:
  - GitHub Actions workflows, Hatchling `sdist` / dependency-group splitting, and Markdown documentation guides (`DA-005`, `DA-011`, `DA-017`..`DA-020`, `DA-025`..`DA-030`) — deferred to Wave 3.

## Capabilities

### New Capabilities

- `otel-lifecycle`: Provider-restart-safe `@traced` decorator with full sync/async generator lifecycle forwarding, validated OTLP bootstrap with rollback and external-provider safety, chained log-correlation idempotency, and `INV-7` SDK-free lazy import guarantees.
- `otel-file-exporters`: Safe-prefix-validated, bounded, and non-fatal rotating JSONL span/metric file writers with exact-pattern retention pruning.

### Modified Capabilities

<!-- None: Wave 2 introduces the OpenSpec baseline capabilities for arlogi.otel. -->

## Impact

- **Affected Code**: `src/arlogi/otel/bootstrap.py`, `src/arlogi/otel/decorator.py`, `src/arlogi/otel/_files.py`, `src/arlogi/otel/exporters.py`, `tests/conftest.py`, `tests/test_otel_bootstrap.py`, `tests/test_otel_decorator.py`, `tests/test_otel_exporter.py`, `tests/test_otel_metrics.py`.
- **Public API & Behavioral Compatibility**:
  - **Strict Validation**: Passing path-traversal/glob-metacharacter `file_prefix`/`prefix` values, `rotate_hours < 1`, `retention_count < 1`, or malformed `otlp_endpoint` URLs (such as `http://:4318`, control characters, or query/fragment URLs) now raises `ValueError` eagerly at construction/setup time.
  - **Dependencies**: Zero new dependencies; `arlogi.otel` and `arlogi.otel.decorator` remain strictly `opentelemetry-api`-only.
