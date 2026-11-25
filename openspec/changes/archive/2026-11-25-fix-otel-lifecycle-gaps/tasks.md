# Tasks

## 1. Async generator forwarding when gated off (DA-002)

- [x] 1.1 Add a failing regression test in `tests/test_otel_decorator.py` reproducing the DA-002 scenario: with `set_trace_modules({<test module>: False})`, a `@traced` async generator doing `val = yield x`, catching `RuntimeError` to yield `"caught:<msg>"`, and recording cleanup in `finally`; assert `await agen.asend(7)` delivers `7`, `await agen.athrow(RuntimeError("boom"))` returns `"caught:boom"`, `await agen.aclose()` runs the inner `finally`, no span is exported, and `inspect.isasyncgenfunction()` is `True`. Verify it fails on the current code.
- [x] 1.2 Refactor `src/arlogi/otel/decorator.py` so `_step_async_gen` accepts `span: trace.Span | None` and `agen_wrapper` uses the single forwarding loop for both gated-on and gated-off paths (design Decision 1), guarding `_record_span_error` and `span.end()` on `span is not None`. Verify test 1.1 and all existing `tests/test_otel_decorator.py` tests pass.

## 2. Generator cleanup inside span context (DA-007)

- [x] 2.1 Add failing regression tests (sync and async, parametrized) in `tests/test_otel_decorator.py`: (a) early break with a `finally` that captures `trace.get_current_span()` and starts a child span → captured span is the generator span and the child is parented to it; (b) `finally` raising `RuntimeError("cleanup boom")` on early `close()`/`aclose()` → error propagates and the exported span has `StatusCode.ERROR` with exactly one exception event; (c) clean early close and task cancellation → status is not `ERROR`, no exception event, span ended once. Verify (a) and (b) fail on the current code.
- [x] 2.2 Implement `_close_sync_gen` / `_close_async_gen` helpers (design Decision 2) and call them from the outer `finally:` of both wrappers, keeping `span.end()` in the innermost `finally`. Verify tests 2.1 and 1.1 pass and `uv run ruff check src/arlogi/otel/decorator.py` reports no complexity violation.

## 3. Atomic tracer cache (DA-019)

- [x] 3.1 Add a failing deterministic two-thread regression test in `tests/test_otel_decorator.py`: wrap provider P1's `get_tracer` with a `threading.Barrier`/`Event` so thread A pauses inside acquisition while thread B invokes the same `@traced` function after a P0 → P1 swap; assert thread B's span is exported by P1 and zero spans go to P0. Add a test that the cached tracer is obtained from the provider instance read (provider swapped mid-call via a stub). Verify they fail on the current code.
- [x] 3.2 Replace the two `nonlocal` variables in `_make_tracer_getter()` with a single immutable `(provider, tracer)` tuple and `current_provider.get_tracer(module)` (design Decision 3). Verify tests 3.1 and the existing restart test pass and that `python -c "import arlogi.otel.decorator, sys; assert not any(m.startswith('opentelemetry.sdk') for m in sys.modules)"` succeeds.

## 4. Metrics shutdown/restart chain (DA-006 + DA-010, CHAIN-03)

- [x] 4.1 Add a failing DA-006 regression test in `tests/test_otel_metrics.py`: `setup_metrics()` → `shutdown_metrics()` → `metrics.get_meter("app.between").create_counter(...)` → `setup_metrics()` → `counter.add(1)` → force flush; assert no "shut down `MeterProvider`" warning is logged, the meter is not `NoOpMeter`, and the measurement is exported by the second provider. Add a test where `_PROXY_METER_PROVIDER` lacks `_lock` (monkeypatched) asserting no exception, `_METER_PROVIDER` is still reset, and one warning is logged. Verify the first test fails on the current code.
- [x] 4.2 Add failing DA-010 regression tests in `tests/test_otel_bootstrap.py` / `tests/test_otel_metrics.py`: a metric reader (resp. span processor) whose `shutdown()` raises; assert `shutdown_metrics()` / `shutdown_tracing()` re-raise, the next `setup_*()` returns a new provider (not the dead one) without a "called more than once" warning, telemetry is exported by it, and a repeated `shutdown_*()` before setup is a no-op that does not call the dead provider's `shutdown()` again. Verify they fail on the current code.
- [x] 4.3 Add a combined CHAIN-03 regression test: failing reader shutdown → `shutdown_metrics()` raises → gap-time `metrics.get_meter()` counter → `setup_metrics()` → measurement exported by the new provider. Verify it fails on the current code.
- [x] 4.4 Extend `_clear_global_meter_provider()` in `src/arlogi/otel/bootstrap.py` to reset `_PROXY_METER_PROVIDER._real_meter_provider = None` under the proxy's `_lock` with independent `getattr`/`hasattr` guards (design Decision 4). Verify test 4.1 passes.
- [x] 4.5 Wrap `provider.shutdown()` in `try/finally` in both `shutdown_metrics()` and `shutdown_tracing()` so state clearing and slot release always run under `_lock` and the original exception propagates (design Decision 5); update both docstrings to state that state is cleared even when an exception is raised. Verify tests 4.2 and 4.3 pass.
- [x] 4.6 Apply the same guarded proxy-delegate reset to `reset_otel_globals` in `tests/conftest.py`, keeping its `ImportError` early return. Verify both `uv run pytest tests/test_otel_metrics.py tests/test_otel_bootstrap.py` and the reversed file order `uv run pytest tests/test_otel_bootstrap.py tests/test_otel_metrics.py` pass.

## 5. Exclusive, symlink-safe JSONL file creation (DA-011)

- [x] 5.1 Add failing regression tests in `tests/test_otel_exporter.py` (POSIX-only symlink tests marked `skipif(os.name == "nt")`), pinning `_now()` to a fixed timestamp: (a) dangling symlink named like the next file pointing outside `tmp_path/telem` → `write_line()` returns `True`, outside target not created, line lands in `<prefix>-<stamp>.1.jsonl`, symlink untouched; (b) dangling symlink to a missing parent dir → `write_line()` returns `True` and `_broken` stays `False`; (c) live symlink to an outside file and a pre-existing regular file → neither modified, next free suffix used; (d) two writers with the same directory/prefix/timestamp → distinct files, each line appears once; (e) suffix exhaustion (monkeypatched small limit) → `write_line()` returns `False`, one warning, `_broken` is `True`. Verify (a)–(c) fail on the current code.
- [x] 5.2 Replace the `exists()` loop and `target.open("a")` in `_RotatingJsonlWriter._open_new_file()` with the bounded `os.open(..., O_WRONLY|O_APPEND|O_CREAT|O_EXCL|getattr(os,"O_NOFOLLOW",0)|getattr(os,"O_BINARY",0), 0o666)` loop plus `os.fdopen(fd, "a", encoding="utf-8")`, closing the fd if `fdopen` fails (design Decision 6). Do not modify `_prune()`. Verify tests 5.1 and the existing `tests/test_otel_exporter.py` tests (including `test_writer_prune_skips_dangling_symlink_and_preserves_sibling_files`) pass, and `git diff src/arlogi/otel/_files.py` shows no change inside `_prune()`.

## 6. Integration verification

- [x] 6.1 Run the full suite with the otel extra: `uv run pytest` — all tests pass.
- [x] 6.2 Run the core-only (no-otel) suite as CI's "Core Only (no-otel)" job does (`uv sync --frozen --group test` then `uv run pytest`), locally via an isolated env without the extra, e.g. `uv run --isolated --frozen --group test pytest` — all tests pass and OTel test modules are skipped.
- [x] 6.3 Run `uv run ruff check src/ tests/` — no errors.
- [x] 6.4 Run `uv run ruff format --check src/ tests/` — no files would be reformatted.
- [x] 6.5 Run `openspec validate fix-otel-lifecycle-gaps --strict` — change is valid.
