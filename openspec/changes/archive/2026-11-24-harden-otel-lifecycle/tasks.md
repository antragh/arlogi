# Tasks

## 1. Rotating JSONL Writer & Exporter Hardening (`otel-file-exporters`)

- [x] 1.1 Harden `src/arlogi/otel/_files.py` (`_RotatingJsonlWriter`): validate `prefix` as a safe single filename component (rejecting empty, `/`, `\`, `..`, NUL, `*`, `?`, `[`, `]`), validate `rotate_hours` and `retention_count` as non-boolean `int >= 1`, replace `Path.glob()` in `_prune()` with `os.scandir()` + anchored timestamp regex (`^<escaped_prefix>-\d{8}-\d{6}(?:\.\d+)?\.jsonl$`), per-entry `try/except OSError` `stat()`, and outer `try/except OSError`, and verify unit tests in `tests/test_otel_exporter.py` and `tests/test_otel_metrics.py` pass via `uv run pytest tests/test_otel_exporter.py tests/test_otel_metrics.py`.

## 2. `@traced` Lifecycle & Complexity Refactor (`otel-lifecycle`)

- [x] 2.1 Refactor `src/arlogi/otel/decorator.py` to extract `_wrap_async_gen`, `_wrap_sync_gen`, `_wrap_async`, `_wrap_sync`, and `_record_span_error` (bringing `traced` and `decorate` below Ruff `C901 <= 10`), use provider-keyed tracer lookup so `@traced` survives `shutdown_tracing()`/`setup_tracing()` restarts, fix argument-binding span leaks, close inner generators on `close()`/`aclose()`, and forward `send()`/`asend()`, `throw()`/`athrow()`, and `StopIteration.value`; verify `INV-7` (no `opentelemetry.sdk` on bare import) and all tests in `tests/test_otel_decorator.py` pass via `uv run pytest tests/test_otel_decorator.py` and `uv run ruff check src/arlogi/otel/decorator.py`.

## 3. OTLP Bootstrap, Correlation & Test Teardown (`otel-lifecycle`)

- [x] 3.1 Harden `src/arlogi/otel/bootstrap.py`: strengthen `_validate_otlp_endpoint()` (rejecting whitespace/control chars, host-less netlocs, invalid ports, and `params`/`query`/`fragment`), validate before creating providers/threads with rollback shutdown on failure, add `hasattr()` checks in `_clear_global_*_provider()`, detect external global provider rejection in `setup_tracing()`/`setup_metrics()` without caching orphaned providers, and traverse chained `LogRecordFactory` wrappers in `install_log_correlation()`; verify tests in `tests/test_otel_bootstrap.py` and `tests/test_otel_metrics.py` pass via `uv run pytest tests/test_otel_bootstrap.py tests/test_otel_metrics.py`.
- [x] 3.2 Harden `tests/conftest.py` (`reset_otel_globals`) to restore `logging.getLogRecordFactory()`, reset `set_trace_modules(None)`, and shut down directly registered providers with `try/finally` teardown, clean up `tests/test_otel_bootstrap.py`'s `Grab` handler and assert `once is not before` in `test_install_log_correlation_is_idempotent`, and verify via `uv run pytest tests/test_otel_bootstrap.py tests/test_otel_decorator.py`.

## 4. Cross-Module Verification

- [x] 4.1 Run full `uv run pytest`, `uv run ruff check src/ tests/`, `uv run ruff format --check src/arlogi/otel/*.py tests/conftest.py tests/test_otel_*.py`, and `openspec validate "harden-otel-lifecycle" --strict`, verifying zero failures.
