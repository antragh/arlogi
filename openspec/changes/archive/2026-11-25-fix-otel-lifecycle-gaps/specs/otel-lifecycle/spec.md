# Spec Delta: otel-lifecycle

## MODIFIED Requirements

### Requirement: Provider-restart-safe tracer resolution in @traced

Functions decorated with `@traced` SHALL resolve their tracer against the currently active global `TracerProvider` so spans continue recording after an in-process `shutdown_tracing()` followed by `setup_tracing()`, without importing `opentelemetry-sdk`. A cached tracer MUST always originate from the exact provider it is cached against, so concurrent callers never pair a newer provider with a tracer from an older one.

#### Scenario: Emitting spans after shutdown_tracing and setup_tracing restart

- **WHEN** a module-level `@traced` function executes under a first `TracerProvider`, `shutdown_tracing()` and `setup_tracing()` are called in-process, and the same `@traced` function executes again
- **THEN** spans from the post-restart invocation are exported by the new `TracerProvider`

#### Scenario: Concurrent invocations across a provider swap never return a stale tracer

- **WHEN** a `@traced` function has run under provider P0, provider P1 becomes the global provider, and thread A is paused inside P1's tracer acquisition for that function while thread B invokes the same `@traced` function
- **THEN** thread B's span is recorded by P1 (never by a tracer obtained from P0), and once both threads finish every span from both invocations is exported by P1

#### Scenario: Tracer is acquired from the provider the cache is keyed on

- **WHEN** the global `TracerProvider` changes between reading the current provider and acquiring the tracer inside a `@traced` invocation
- **THEN** the tracer used for that invocation is the one returned by the provider that was read, and the cache entry pairs that provider with that tracer

### Requirement: Complete sync and async generator lifecycle forwarding in @traced

Sync and async generator functions decorated with `@traced` SHALL not leak open spans when argument binding raises, SHALL close the underlying generator on early consumer abandonment (`close()` / `aclose()`), and SHALL preserve `send()`/`asend()`, `throw()`/`athrow()`, and `StopIteration.value` return values. This forwarding MUST be identical whether per-module gating (`set_trace_modules()`) enables or disables the span.

#### Scenario: Closing inner generator on early break and argument-binding errors

- **WHEN** a consumer breaks early from a `@traced` sync or async generator (triggering `close()`/`aclose()`) or passes invalid call arguments (`TypeError`)
- **THEN** the inner generator's `finally` block executes and any started span is ended cleanly without leaking active spans

#### Scenario: Forwarding send, throw, and return values through @traced generators

- **WHEN** a caller drives a `@traced` generator with `.send(value)`, `.throw(exc)`, or inspects the `StopIteration.value` returned by `yield from`
- **THEN** sent values, thrown exceptions, and generator return values are forwarded identically to the undecorated generator

#### Scenario: Gated-off async generator forwards asend, athrow, and aclose

- **WHEN** `set_trace_modules({"<module>": False})` disables spans for the module of a `@traced` async generator that computes `val = yield x`, catches `RuntimeError` to yield `"caught:<msg>"`, and records cleanup in `finally`, and a caller performs `await agen.asend(7)`, `await agen.athrow(RuntimeError("boom"))`, and `await agen.aclose()`
- **THEN** the inner generator receives `7`, yields `"caught:boom"` from its own handler, and its `finally` block runs on `aclose()`, exactly as the undecorated generator would, and no span is started

#### Scenario: Gated-off decorated async generator remains an async generator function

- **WHEN** an async generator function is decorated with `@traced` and its module is gated off
- **THEN** `inspect.isasyncgenfunction()` on the decorated callable returns `True` and plain `async for` iteration yields the same items as the undecorated generator

### Requirement: External global provider safety and attribute checks on reset

When releasing global provider slots during shutdown, helper functions SHALL verify attribute existence before mutation, and `setup_tracing()` / `setup_metrics()` MUST verify that the newly constructed provider became the active global provider (shutting down and not caching the new provider if an external global provider rejected override). Releasing the global `MeterProvider` slot MUST also stop the OpenTelemetry API's proxy meter provider from delegating to the shut-down provider.

#### Scenario: Preserving an externally registered global TracerProvider

- **WHEN** an external library registers its own global `TracerProvider` before `setup_tracing()` is called
- **THEN** `setup_tracing()` shuts down its unused provider without caching `_tracer_provider` and a subsequent `shutdown_tracing()` does not clobber the external provider

#### Scenario: Meter acquired between shutdown_metrics and setup_metrics records to the new provider

- **WHEN** `setup_metrics()` installs provider P1, `shutdown_metrics()` is called, `metrics.get_meter("app.between")` creates a counter that is incremented after a subsequent `setup_metrics()` installs provider P2, and P2 is flushed
- **THEN** no "shut down MeterProvider" warning is logged, the meter is not a permanent no-op, and P2 exports the counter measurement

#### Scenario: Tolerating missing proxy meter provider internals

- **WHEN** `shutdown_metrics()` runs against an `opentelemetry-api` build whose proxy meter provider lacks the expected lock or delegate attribute
- **THEN** no exception is raised, the arlogi-owned global slot is still released, and a single warning is logged that re-initialisation may be ignored

## ADDED Requirements

### Requirement: Generator cleanup runs inside the generator span

When early `close()` / `aclose()` on a traced `@traced` generator runs the inner generator's cleanup, that cleanup MUST execute with the generator's span as the current span, and an exception raised by the cleanup MUST be recorded on the span as an exception event with `ERROR` status before it propagates. Normal close and `asyncio.CancelledError` MUST NOT set `ERROR` status.

#### Scenario: Cleanup observes the generator span as current

- **WHEN** a consumer breaks early from a traced sync or async `@traced` generator whose `finally` block captures `trace.get_current_span()` and starts a child span, with no other span active
- **THEN** the captured current span is the generator's span and the child span's parent is the generator's span

#### Scenario: Cleanup exception marks the span as failed

- **WHEN** the `finally` block of a traced `@traced` sync or async generator raises `RuntimeError("cleanup boom")` during early `close()` / `aclose()`
- **THEN** `RuntimeError("cleanup boom")` propagates to the caller and the ended span has `StatusCode.ERROR` and exactly one exception event for it

#### Scenario: Clean early close keeps non-error status

- **WHEN** a consumer breaks early from a traced `@traced` generator whose cleanup does not raise, or the consuming task is cancelled
- **THEN** the span is ended exactly once with a status other than `ERROR` and no exception event

### Requirement: Shutdown always leaves providers restartable

`shutdown_tracing()` and `shutdown_metrics()` SHALL clear arlogi's cached provider and release the corresponding global provider slot even when the provider's own `shutdown()` raises, and SHALL then re-raise the original exception to the caller.

#### Scenario: Metrics restart after a failing reader shutdown

- **WHEN** `setup_metrics()` installs provider P1 whose metric reader raises during shutdown, `shutdown_metrics()` is called, and `setup_metrics()` is called again
- **THEN** `shutdown_metrics()` raises the provider's shutdown exception, the second `setup_metrics()` returns a new provider that is not P1, logs no "called more than once" warning, and exports subsequently recorded metrics

#### Scenario: Tracing restart after a failing span processor shutdown

- **WHEN** `setup_tracing()` installs provider P1 with a span processor that raises during shutdown, `shutdown_tracing()` is called, and `setup_tracing()` is called again
- **THEN** `shutdown_tracing()` raises the processor's exception, the second `setup_tracing()` returns a new provider that is not P1 and is the active global provider, and spans from `@traced` functions are exported by it

#### Scenario: Repeated shutdown after a failure is a no-op

- **WHEN** `shutdown_metrics()` or `shutdown_tracing()` has raised because provider shutdown failed and is then called again before any new setup
- **THEN** the second call returns without raising and without calling the failed provider's `shutdown()` again
