# Spec Delta: otel-lifecycle

## MODIFIED Requirements

### Requirement: Provider-restart-safe tracer resolution in @traced

Functions decorated with `@traced` SHALL resolve their tracer against the currently active global `TracerProvider` so spans continue recording after an in-process `shutdown_tracing()` followed by `setup_tracing()`, without importing `opentelemetry-sdk`. A cached tracer MUST always originate from the exact provider it is cached against, and `@traced` MUST NOT cache tracers keyed against `opentelemetry.trace.ProxyTracerProvider`, so concurrent callers never pair `_PROXY_TRACER_PROVIDER` with a real SDK tracer or latched `ProxyTracer` across a shutdown-and-restart gap.

#### Scenario: Emitting spans after shutdown_tracing and setup_tracing restart

- **WHEN** a module-level `@traced` function executes under a first `TracerProvider`, `shutdown_tracing()` and `setup_tracing()` are called in-process, and the same `@traced` function executes again
- **THEN** spans from the post-restart invocation are exported by the new `TracerProvider`

#### Scenario: Concurrent invocations across a provider swap never return a stale tracer

- **WHEN** a `@traced` function has run under provider P0, provider P1 becomes the global provider, and thread A is paused inside P1's tracer acquisition for that function while thread B invokes the same `@traced` function
- **THEN** thread B's span is recorded by P1 (never by a tracer obtained from P0), and once both threads finish every span from both invocations is exported by P1

#### Scenario: Tracer is acquired from the provider the cache is keyed on

- **WHEN** the global `TracerProvider` changes between reading the current provider and acquiring the tracer inside a `@traced` invocation
- **THEN** the tracer used for that invocation is the one returned by the provider that was read, and the cache entry pairs that provider with that tracer

#### Scenario: ProxyTracerProvider is never cached across setup_tracing and shutdown_tracing

- **WHEN** a `@traced` invocation runs concurrently with `setup_tracing()` (or caches a `ProxyTracer` that latches onto P1) and `shutdown_tracing()` subsequently clears the global `TracerProvider`
- **THEN** post-shutdown `@traced` invocations during the gap obtain a fresh no-op `NonRecordingSpan` rather than recording spans against shut-down P1

### Requirement: Strict OTLP endpoint validation and thread-leak-free bootstrap rollback

`setup_tracing()` and `setup_metrics()` SHALL treat `otlp_endpoint=None` or `otlp_endpoint=""` as remote OTLP export disabled (file-only export) and SHALL validate any other `otlp_endpoint` value (requiring a non-empty `str` with `http`/`https`, a non-empty `hostname`, `1 <= port <= 65535` when a port is specified with no dangling empty `:` separator, and no whitespace, control characters, `?`, `#`, or `;` delimiters anywhere in the URL) before constructing any `TracerProvider`, `BatchSpanProcessor`, or `PeriodicExportingMetricReader`, and MUST shut down partially created components if initialization fails.

#### Scenario: Rejecting malformed OTLP endpoints without leaking background threads

- **WHEN** `setup_tracing()` or `setup_metrics()` is called with `" "`, `"   "`, `0`, `False`, `"http://:4318"`, `"http://localhost:99999"`, `"http://localhost:0"`, `"http://localhost:"`, `"http://[::1]:"`, `"http://localhost:4318\r\n"`, `"http://collector:4318?"`, `"http://collector:4318#"`, `"http://collector:4318/otlp;"`, or `"http://collector:4318?token=x"`
- **THEN** `ValueError` is raised and zero new OTEL background threads remain alive

#### Scenario: Empty string OTLP endpoint disables remote export for file-only mode

- **WHEN** `setup_tracing(..., otlp_endpoint="")` or `setup_metrics(..., otlp_endpoint="")` is called
- **THEN** initialization succeeds with only the rotating file exporter configured and no remote OTLP exporter attached

### Requirement: External global provider safety and attribute checks on reset

When releasing global provider slots during shutdown, helper functions SHALL verify attribute existence before mutation, and `setup_tracing()` / `setup_metrics()` MUST verify that the newly constructed provider became the active global provider (shutting down and not caching the new provider if an external global provider rejected override). Releasing the global `MeterProvider` slot MUST also stop the OpenTelemetry API's proxy meter provider and any pre-existing `_ProxyMeter` / `_ProxyInstrument` instances registered in `proxy._meters` from delegating to the shut-down provider (acquiring locks in `proxy._lock` -> `meter._lock` order).

#### Scenario: Preserving an externally registered global TracerProvider

- **WHEN** an external library registers its own global `TracerProvider` before `setup_tracing()` is called
- **THEN** `setup_tracing()` shuts down its unused provider without caching `_tracer_provider` and a subsequent `shutdown_tracing()` does not clobber the external provider

#### Scenario: Meter acquired between shutdown_metrics and setup_metrics records to the new provider

- **WHEN** `setup_metrics()` installs provider P1, `shutdown_metrics()` is called, `metrics.get_meter("app.between")` creates a counter that is incremented after a subsequent `setup_metrics()` installs provider P2, and P2 is flushed
- **THEN** no "shut down MeterProvider" warning is logged, the meter is not a permanent no-op, and P2 exports the counter measurement

#### Scenario: Pre-existing module-level meter creates an instrument in the shutdown gap and upgrades on restart

- **WHEN** `meter = metrics.get_meter("app.pre")` is acquired before the first `setup_metrics()` (P1), `shutdown_metrics()` runs, `c_gap = meter.create_counter("c_gap")` is created during the shutdown gap, and `setup_metrics()` restarts with P2
- **THEN** `c_gap` is a `_ProxyCounter` that upgrades to P2 when P2 is installed, and `c_gap.add(...)` measurements are exported by P2

#### Scenario: Tolerating missing proxy meter provider internals

- **WHEN** `shutdown_metrics()` runs against an `opentelemetry-api` build whose proxy meter provider lacks the expected lock or delegate attribute
- **THEN** no exception is raised, the arlogi-owned global slot is still released, and a single warning is logged that re-initialisation may be ignored

### Requirement: Chained LogRecordFactory idempotency for log correlation

`install_log_correlation()` SHALL detect prior installation even when third-party wrappers (via `_arlogi_prev_factory`, `__wrapped__`, `functools.partial` including callable `args` and `keywords`, or closure cells) have subsequently wrapped `logging.getLogRecordFactory()`, avoiding duplicate correlation wrapper stacking.

#### Scenario: Calling install_log_correlation after third-party factory wrapping

- **WHEN** `install_log_correlation()` is called, a third-party closure wraps `logging.setLogRecordFactory()`, and `install_log_correlation()` is called again
- **THEN** no second correlation wrapper is installed on top of the third-party factory

#### Scenario: Calling install_log_correlation after third-party functools.partial wrapping

- **WHEN** `install_log_correlation()` is called, a third-party wrapper wraps the factory via `functools.partial(wrapper, prev_factory)` or `functools.partial(wrapper, prev=prev_factory)`, and `install_log_correlation()` is called again
- **THEN** `_has_arlogi_correlation()` detects the prior correlation factory through `node.args`/`node.keywords` and no duplicate correlation wrapper is stacked
