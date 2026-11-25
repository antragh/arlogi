# Design

## Context

See `proposal.md` for motivation and scope. `src/arlogi/otel/bootstrap.py` and `src/arlogi/otel/exporters.py` currently carry partial uncommitted fixes (`_validate_otlp_endpoint` initial draft and `b64_ids_to_hex` inside `try`). `src/arlogi/otel/__init__.py` and `src/arlogi/otel/decorator.py` must remain strictly `opentelemetry-api`-only (`INV-7`), and `src/arlogi/otel/decorator.py` currently violates `.ruff.toml`'s `C901 <= 10` complexity limit (`22` and `21`).

## Goals / Non-Goals

**Goals:**

- Make `@traced` resilient to `TracerProvider` restarts while keeping hot-path tracer lookup fast and strictly `opentelemetry-api`-only.
- Fix sync/async generator lifecycle (`close`/`aclose`, `send`/`asend`, `throw`/`athrow`, `StopIteration.value`, argument-binding span leaks) while decomposing `decorator.py` below `C901 <= 10`.
- Eliminate background thread leaks, silent external-provider clobbering, and prefix-traversal / `stat()`-TOCTOU failures in `bootstrap.py` and `_files.py`.

**Non-Goals:**

- Modifying core `src/arlogi/*.py` modules (completed in Wave 1) or CI/CD / Markdown docs (deferred to Wave 3).

## Decisions

### 1. Provider-Keyed Tracer Cache in `decorator.py` (`DA-003`, `DA-031`)

- **Choice**: Extract `_resolve_tracer(module, state)` or a small closure cache `cached_provider = None; cached_tracer = None` inside each wrapper factory (`_wrap_async_gen`, `_wrap_sync_gen`, `_wrap_async`, `_wrap_sync`) that checks `current_provider = trace.get_tracer_provider()` and refreshes `cached_tracer = trace.get_tracer(module)` only when `current_provider is not cached_provider`.
- **Generator Lifecycle**:
  - Construct `gen = fn(*args, **kwargs)` *inside* the `try` block (or before starting the span if argument binding errors should propagate without creating a span — wait: if `fn(*args, **kwargs)` raises `TypeError`, no generator was started, so starting the span *after* `gen = fn(*args, **kwargs)` or ending the span in `finally` prevents leaked open spans; starting the span after `gen = fn(*args, **kwargs)` is cleanest for argument-binding errors, and `try ... finally: gen.close(); span.end()` ensures both generator and span always close!).
  - For sync generators (`_wrap_sync_gen`): manually drive `gen.send(sent)` / `gen.throw(exc)` inside `try`, yielding yielded items, catching `StopIteration as stop: return stop.value`, and calling `gen.close()` + `span.end()` in `finally`.
  - For async generators (`_wrap_async_gen`): manually drive `await gen.asend(sent)` / `await gen.athrow(exc)` inside `try`, catching `StopAsyncIteration`, handling `GeneratorExit` / `asyncio.CancelledError` without marking span error, and calling `await gen.aclose()` + `span.end()` in `finally`.
  - Extract `_record_span_error(span, exc)` to keep every wrapper helper well below `C901 <= 10`.

### 2. Endpoint Validation, Rollback & External Provider Safety in `bootstrap.py` (`DA-009`, `DA-010`, `DA-024`)

- **Choice**:
  - In `_validate_otlp_endpoint(endpoint)`: reject non-strings/empty strings, reject any `c.isspace() or ord(c) < 32 or ord(c) == 127`, parse with `urlparse`, require `parsed.scheme in ("http", "https")`, `bool(parsed.hostname)`, valid `parsed.port` (catching `ValueError`), and empty `parsed.params`, `parsed.query`, `parsed.fragment`.
  - Validate `otlp_endpoint` (if truthy) and `RotatingJsonl*Exporter` (including `file_prefix`, `rotate_hours`, `retention_count`) *before* constructing `TracerProvider` / `BatchSpanProcessor` / `PeriodicExportingMetricReader`. Wrap processor/reader assembly in `try/except` that calls `.shutdown()` on any already-created readers/processors/provider before re-raising.
  - After `trace.set_tracer_provider(provider)` / `metrics.set_meter_provider(provider)`, verify `trace.get_tracer_provider() is provider` / `metrics.get_meter_provider() is provider`; if False, shut down the newly created `provider`, log a warning, and return the active global provider without setting `_tracer_provider` / `_meter_provider`.
  - In `_clear_global_tracer_provider()` / `_clear_global_meter_provider()`, check `hasattr(...)` on both `_TRACER_PROVIDER_SET_ONCE`/`_TRACER_PROVIDER` (and `_METER_PROVIDER_SET_ONCE`/`_METER_PROVIDER`) before assignment, logging the warning if missing.
  - In `install_log_correlation()`, attach `factory._arlogi_prev_factory = current` and implement `_has_arlogi_correlation(factory)` using BFS/DFS with a `visited: set[int]` over `_arlogi_prev_factory`, `__wrapped__`, `functools.partial.func`, and `__closure__` cell contents.

### 3. `_RotatingJsonlWriter` Prefix/Bounds Validation & Safe Pruning (`DA-002`, `DA-006`)

- **Choice**:
  - Validate `prefix` in `_RotatingJsonlWriter.__init__`: must be non-empty `str`, must not contain `/`, `\`, `\x00`, `..`, `*`, `?`, `[`, `]`, and `Path(prefix).name == prefix` and `prefix not in (".", "..")`.
  - Validate `rotate_hours` and `retention_count` as non-boolean `int >= 1`.
  - In `_prune()`, use `os.scandir(self._directory)` with compiled regex `rf"^{re.escape(self._prefix)}-\d{{8}}-\d{{6}}(?:\.\d+)?\.jsonl$"`, skip active `self._active_path` (if open) and collect `(entry.stat().st_mtime, Path(entry.path))` inside per-entry `try/except OSError`, wrapped in an outer `try/except OSError: return`.

### 4. `tests/conftest.py` Teardown Hygiene (`DA-022`)

- **Choice**: In `reset_otel_globals()`, capture `orig_factory = logging.getLogRecordFactory()` before `yield`, and in `try ... finally` teardown restore `logging.setLogRecordFactory(orig_factory)`, reset `set_trace_modules(None)`, invoke `shutdown_tracing()` and `shutdown_metrics()`, and call `.shutdown()` (best-effort) on any directly registered `trace._TRACER_PROVIDER` / `metrics._internal._METER_PROVIDER` before resetting `Once()` slots.

## Risks / Trade-offs

- **[Stricter `prefix` and `otlp_endpoint` validation]** -> Callers passing `../` or glob characters in `file_prefix` or query strings in `otlp_endpoint` will now get `ValueError` instead of silent corruption or path escape. Mitigation: matches documented contracts and `INV-8`.
- **[`decorator.py` complexity split]** -> Extracting 5 module-private helpers increases function count slightly while keeping all functions cleanly below `C901 <= 10` and preserving `@traced`'s public signature and `opentelemetry-api`-only imports (`INV-7`).
