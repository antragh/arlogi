# Design: Fix OpenTelemetry Lifecycle Gaps

## Context

`arlogi.otel` wraps `opentelemetry-api` (decorator, log correlation) and `opentelemetry-sdk` (bootstrap, exporters). The decorator module (`src/arlogi/otel/decorator.py`) MUST remain importable with only `opentelemetry-api`; `bootstrap.py` and `_files.py` are reached only through the lazy `arlogi.otel.__getattr__` boundary. Provider restart in-process relies on resetting OpenTelemetry private module globals, guarded by attribute checks (existing `otel-lifecycle` requirement). The installed and locked upstream versions are `opentelemetry-api`/`opentelemetry-sdk` 1.44.0; relevant internals were confirmed in `.venv`:

- `opentelemetry.metrics._internal._PROXY_METER_PROVIDER` is a `_ProxyMeterProvider` with `_lock: threading.Lock`, `_meters: list[_ProxyMeter]`, and `_real_meter_provider: MeterProvider | None`. `get_meter()` delegates to `_real_meter_provider` under `_lock` when it is not `None`; `_set_meter_provider()` calls `on_set_meter_provider()`, which rebinds `_real_meter_provider` and every proxy meter in `_meters`.
- SDK `MeterProvider.shutdown()` flips `_shutdown = True` via a `Once` before iterating readers and raises `Exception` if any reader fails; `TracerProvider.shutdown()` calls `SynchronousMultiSpanProcessor.shutdown()`, which propagates the first processor exception.
- `opentelemetry.trace.get_tracer(name)` re-reads `get_tracer_provider()` when no provider is passed.

## Goals / Non-Goals

**Goals:**

- Fix DA-002, DA-007, DA-019, DA-006, DA-010, and DA-011 exactly as scoped in proposal.md, each with a regression test reproducing the audit scenario.
- Fix CHAIN-03 (DA-010 + DA-006) as one unit (see Decision 5).
- Keep the decorator SDK-free, keep core (`no-otel`) installs unaffected, and keep all private-internal access behind attribute guards.

**Non-Goals:**

- Any change to `_RotatingJsonlWriter._prune()` or core handler pruning (owned by `fix-core-logging-and-rotation-gaps`).
- Swallowing or retrying provider shutdown failures; directory ownership checks on `file_dir`.

## Decisions

### 1. Single forwarding loop for traced and gated-off async generators (DA-002)

Generalize `_step_async_gen` to accept `span: trace.Span | None`. When `span is None` it calls `gen.asend()` / `gen.athrow()` directly; otherwise it enters `trace.use_span(...)` as today. `agen_wrapper` computes `span = get_tracer().start_span(...) if _module_enabled(module) else None` and runs the same `while True` loop. `_record_span_error()` and `span.end()` are guarded by `span is not None`. `agen_wrapper` stays an `async def` containing `yield`, so `inspect.isasyncgenfunction()` remains `True`.

- The gating decision is still taken once per generator invocation (at first `__anext__`), matching current semantics.
- Ordering: the inner generator object `fn(*args, **kwargs)` is still created before the span is started, so argument-binding `TypeError` never leaks a span (existing requirement).
- Alternative considered: a separate hand-written forwarding loop for the gated path. Rejected — duplicates the subtle `GeneratorExit` / `BaseException` handling that the traced loop already gets right.
- The sync path (`return (yield from fn(...))`) already delegates correctly and is unchanged for gating.

### 2. Cleanup inside span context with error recording (DA-007)

Introduce a small helper per flavor, e.g. `_close_async_gen(gen, span)` / `_close_sync_gen(gen, span)`, invoked from the outer `finally:`:

```python
async def _close_async_gen(gen, span):
    if span is None:
        await gen.aclose()
        return
    try:
        with trace.use_span(span, end_on_exit=False, record_exception=False, set_status_on_exception=False):
            await gen.aclose()
    except Exception as exc:
        _record_span_error(span, exc)
        raise
```

The wrapper keeps `span.end()` in the innermost `finally` so the span ends exactly once. Only `Exception` is recorded, so `GeneratorExit`, `asyncio.CancelledError`, and `KeyboardInterrupt` never set `ERROR` (existing non-error semantics preserved).

- Double recording: if the body already raised and was recorded in the outer `except Exception`, `aclose()` on an already-finished inner generator is a no-op and cannot raise again, so no duplicate exception events occur. If cleanup raises while another exception is propagating, Python chains them (`__context__`) and both are recorded once each — accepted.
- Extracting helpers also keeps `ruff` max-complexity=10 satisfied after Decision 1 adds `span is None` branches.

### 3. Atomic tracer cache publication (DA-019)

Replace the two `nonlocal` variables with one `cache: tuple[Any, trace.Tracer] | None`. Each call reads `entry = cache` once into a local, compares `entry[0] is current_provider`, and on miss does `tracer = current_provider.get_tracer(module)` followed by a single assignment `cache = (current_provider, tracer)`.

- Concurrency: rebinding a closure cell to a new tuple is a single atomic store under the GIL and safe under free-threaded CPython because readers only ever see a fully constructed immutable tuple. No lock is needed; two racing misses may both call `get_tracer()` and the last writer wins with a consistent pair (benign; SDK `TracerProvider.get_tracer` is thread-safe).
- Calling `current_provider.get_tracer(module)` instead of `trace.get_tracer(module)` guarantees the pair is consistent even if the global changes mid-call. Both `ProxyTracerProvider` and SDK `TracerProvider` implement `get_tracer(name)` (API contract, not a private internal), so this stays SDK-free.

### 4. Release the proxy meter provider delegate (DA-006)

`_clear_global_meter_provider()` additionally performs:

```python
proxy = getattr(internal, "_PROXY_METER_PROVIDER", None)
proxy_lock = getattr(proxy, "_lock", None)
if proxy is None or proxy_lock is None or not hasattr(proxy, "_real_meter_provider"):
    logger.warning("could not release the global MeterProvider; re-initialisation may be ignored")
else:
    with proxy_lock:
        proxy._real_meter_provider = None
```

- `_meters` is deliberately left intact: proxy meters created before the first setup stay registered and are rebound to the next provider by `on_set_meter_provider()`; meters created during the gap are appended as fresh `_ProxyMeter`s and likewise upgrade on the next `set_meter_provider()`.
- Lock ordering: the proxy lock is acquired while arlogi's bootstrap `_lock` is held (call path `shutdown_metrics()` → `_clear_global_meter_provider()`). OpenTelemetry never calls back into arlogi while holding `proxy._lock`, and arlogi never takes `_lock` while holding `proxy._lock`, so the order `_lock → proxy._lock` is acyclic and deadlock-free. `_set_meter_provider()` acquires `proxy._lock` inside its `Once` lock; arlogi calls it only under `_lock`, consistent with the same order.
- Guard semantics: the proxy guard is independent of the `_METER_PROVIDER` guard, so a missing proxy attribute logs one warning but still resets the slot (spec scenario "Tolerating missing proxy meter provider internals"). The whole helper remains wrapped in the existing `except Exception` fallback.
- `tests/conftest.py::reset_otel_globals` gets the same guarded reset so test isolation does not leak a stale delegate between tests.
- The trace side needs no counterpart: `ProxyTracerProvider` reads the module-global `_TRACER_PROVIDER` on every call and caches nothing.

### 5. Shutdown cleanup in try/finally; fail-fast after cleanup (DA-010, CHAIN-03)

```python
with _lock:
    provider = _meter_provider
    if provider is None:
        return
    try:
        provider.shutdown()
    finally:
        _meter_provider = None
        _clear_global_meter_provider()
```

and the identical shape for tracing. The exception from `provider.shutdown()` is re-raised after cleanup (**fail-fast after cleanup**).

- Justification: the current contract already propagates shutdown errors and callers (and existing tests) may rely on seeing them, e.g. to report an unreachable collector; swallowing would hide data loss. What was broken is only the *state* left behind, which `finally` fixes. A retried `shutdown_*()` becomes a no-op because state is already cleared, matching "safe to call repeatedly". The SDK's own `Once` already prevents a second `provider.shutdown()` from doing work, so not retrying loses nothing.
- Alternative considered: fail-open (catch, log warning, return). Rejected as a silent behavior change to a public function; it can be layered later by host code (`contextlib.suppress`). Flagged for user confirmation.
- Concurrency: everything stays under bootstrap `_lock`, so a concurrent `setup_*()` observes either the old provider (before shutdown starts) or `None` plus a released global slot — never a half-cleared state.
- CHAIN-03 coupling: Decision 5 guarantees `_clear_global_meter_provider()` runs on the failure path; Decision 4 guarantees that running it actually unbinds the proxy. With only Decision 5, a failing shutdown still leaves the proxy bound to the dead provider so gap-time meters become permanent no-ops; with only Decision 4, a failing shutdown never reaches the helper and `setup_metrics()` keeps returning the dead provider. Both MUST land in the same change, and the CHAIN-03 regression test exercises them together (failing reader shutdown → gap-time `get_meter()` → restart → measurement exported).

### 6. Exclusive, no-follow file creation (DA-011)

Replace the `exists()` loop and `target.open("a")` in `_open_new_file()` with a bounded exclusive-create loop:

```python
flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
for suffix in range(_MAX_COLLISION_SUFFIX + 1):
    name = f"{prefix}-{stamp}.jsonl" if suffix == 0 else f"{prefix}-{stamp}.{suffix}.jsonl"
    target = self._directory / name
    try:
        fd = os.open(target, flags, 0o666)
    except (FileExistsError, IsADirectoryError):
        continue
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.EISDIR):
            continue
        raise
    self._stream = os.fdopen(fd, "a", encoding="utf-8")
    break
else:
    raise OSError(errno.EEXIST, "no free telemetry file name", str(self._directory / f"{prefix}-{stamp}.jsonl"))
```

- `O_CREAT | O_EXCL` fails with `EEXIST` if the final path component exists in any form, including a dangling or live symlink (POSIX guarantees `O_EXCL` does not follow a symlink in the last component). This closes CWE-59 and the cross-process TOCTOU in one syscall. `O_NOFOLLOW` is defense in depth; `ELOOP` is treated as "occupied".
- Non-POSIX: `getattr(os, "O_NOFOLLOW", 0)` degrades to `0` on Windows, where `O_CREAT | O_EXCL` maps to `CREATE_NEW`, which also fails on any existing entry including reparse points. `getattr(os, "O_BINARY", 0)` matches what `open()` does internally so CRT text-mode does not double-translate newlines on Windows; it is `0` on POSIX.
- Mode `0o666` is filtered by umask, identical to the previous `Path.open("a")` behavior; no permission change.
- `_MAX_COLLISION_SUFFIX` (e.g. 1000) bounds the loop; exhaustion raises `OSError`, which the existing `write_line()` handler converts to one warning plus `_broken = True` (non-fatal degradation invariant).
- If `os.fdopen` itself fails after `os.open` succeeded, close the fd before re-raising to avoid a descriptor leak.
- Only symlinks in the final component are addressed; a symlinked `file_dir` itself is the operator's configuration and is out of scope (consistent with no directory ownership checks).
- `_active_path = target.resolve()` and the subsequent `self._prune()` call are kept byte-for-byte; `_prune()` itself is not touched (owned by the sibling change).

### 7. Optional-dependency boundary

- `decorator.py` keeps importing only `opentelemetry.trace` (API). Decisions 1–3 add no imports.
- `bootstrap.py` changes touch only `opentelemetry.metrics._internal` (API package) via `getattr`.
- `_files.py` adds `errno` only (stdlib). It remains free of any `opentelemetry` import.
- Core-only (`uv sync --frozen --group test`, no `--extra otel`) behavior is unchanged; OTel tests continue to skip via existing `importorskip` gating, and the `reset_otel_globals` fixture keeps its `ImportError` early-return.

## Risks / Trade-offs

- [Private OTel internals may move in a future release] → All accesses are `getattr`/`hasattr`-guarded with a single warning fallback; a test simulates a proxy missing `_lock` to lock in fail-safe behavior.
- [Fail-fast after cleanup still raises to host cleanup paths] → Matches current behavior; documented in the `shutdown_*()` docstrings that state is cleared even when an exception is raised.
- [Exclusive create changes file-collision naming in rare same-second restarts] → Names still follow the exact `<prefix>-YYYYMMDD-HHMMSS(.N)?.jsonl` pattern, so the archive regex and pruning are unaffected.
- [Recording cleanup exceptions may change span status for existing users whose cleanup raises] → This is the intended fix; such exceptions already propagate to the caller, so marking the span `ERROR` aligns telemetry with observed behavior.
- [Racing tracer-cache misses call `get_tracer()` twice] → Benign and bounded to provider transitions.
