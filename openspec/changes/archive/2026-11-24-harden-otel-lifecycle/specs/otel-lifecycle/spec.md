# Spec Delta

## Purpose

Defines provider-restart-resilient `@traced` span instrumentation across sync, async, and generator functions, strict OTLP endpoint bootstrap with clean rollback, and chained log-correlation idempotency while preserving the `opentelemetry-api`-only lazy import boundary.

## ADDED Requirements

### Requirement: Provider-restart-safe tracer resolution in @traced

Functions decorated with `@traced` SHALL resolve their tracer against the currently active global `TracerProvider` so spans continue recording after an in-process `shutdown_tracing()` followed by `setup_tracing()`, without importing `opentelemetry-sdk`.

#### Scenario: Emitting spans after shutdown_tracing and setup_tracing restart

- **WHEN** a module-level `@traced` function executes under a first `TracerProvider`, `shutdown_tracing()` and `setup_tracing()` are called in-process, and the same `@traced` function executes again
- **THEN** spans from the post-restart invocation are exported by the new `TracerProvider`

### Requirement: Complete sync and async generator lifecycle forwarding in @traced

Sync and async generator functions decorated with `@traced` SHALL not leak open spans when argument binding raises, SHALL close the underlying generator on early consumer abandonment (`close()` / `aclose()`), and SHALL preserve `send()`/`asend()`, `throw()`/`athrow()`, and `StopIteration.value` return values.

#### Scenario: Closing inner generator on early break and argument-binding errors

- **WHEN** a consumer breaks early from a `@traced` sync or async generator (triggering `close()`/`aclose()`) or passes invalid call arguments (`TypeError`)
- **THEN** the inner generator's `finally` block executes and any started span is ended cleanly without leaking active spans

#### Scenario: Forwarding send, throw, and return values through @traced generators

- **WHEN** a caller drives a `@traced` generator with `.send(value)`, `.throw(exc)`, or inspects the `StopIteration.value` returned by `yield from`
- **THEN** sent values, thrown exceptions, and generator return values are forwarded identically to the undecorated generator

### Requirement: Strict OTLP endpoint validation and thread-leak-free bootstrap rollback

`setup_tracing()` and `setup_metrics()` SHALL validate `otlp_endpoint` (requiring `http`/`https`, a non-empty `hostname`, valid `port`, and no whitespace, control characters, query, or fragment components) before constructing any `TracerProvider`, `BatchSpanProcessor`, or `PeriodicExportingMetricReader`, and MUST shut down partially created components if initialization fails.

#### Scenario: Rejecting malformed OTLP endpoints without leaking background threads

- **WHEN** `setup_tracing()` or `setup_metrics()` is called with `"http://:4318"`, `"http://localhost:99999"`, `"http://localhost:4318\r\n"`, or `"http://collector:4318?token=x"`
- **THEN** `ValueError` is raised and zero new OTEL background threads remain alive

### Requirement: External global provider safety and attribute checks on reset

When releasing global provider slots during shutdown, helper functions SHALL verify attribute existence before mutation, and `setup_tracing()` / `setup_metrics()` MUST verify that the newly constructed provider became the active global provider (shutting down and not caching the new provider if an external global provider rejected override).

#### Scenario: Preserving an externally registered global TracerProvider

- **WHEN** an external library registers its own global `TracerProvider` before `setup_tracing()` is called
- **THEN** `setup_tracing()` shuts down its unused provider without caching `_tracer_provider` and a subsequent `shutdown_tracing()` does not clobber the external provider

### Requirement: Chained LogRecordFactory idempotency for log correlation

`install_log_correlation()` SHALL detect prior installation even when third-party wrappers (via `_arlogi_prev_factory`, `__wrapped__`, `functools.partial`, or closure cells) have subsequently wrapped `logging.getLogRecordFactory()`, avoiding duplicate correlation wrapper stacking.

#### Scenario: Calling install_log_correlation after third-party factory wrapping

- **WHEN** `install_log_correlation()` is called, a third-party closure wraps `logging.setLogRecordFactory()`, and `install_log_correlation()` is called again
- **THEN** no second correlation wrapper is installed on top of the third-party factory
