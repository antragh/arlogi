# Design

## Context

See `proposal.md` — Why. All `19` findings (`DA-001`..`DA-019`) and both cross-module failure chains (`CHAIN-01`, `CHAIN-02`) were confirmed against the current working tree (`master` @ `c6f137b`) and documented in `docs/_audit_/2611250948-deep-audit.json`.

Constraints shaping the design:

- Core `arlogi` (`src/arlogi/*.py`) MUST remain importable with only `rich` installed (`no-otel` CI matrix leg).
- `ruff` enforces `max-complexity = 10`, requiring small single-purpose helpers rather than growing existing methods.
- Existing lock hierarchy: `LoggerFactory._init_lock`, `LoggerFactory._dedicated_lock`, `Handler.lock` (`threading.RLock`, via `acquire()`/`release()`), `otel.bootstrap._lock`, `otel._files._RotatingJsonlWriter._lock`, and upstream `opentelemetry.metrics._internal._PROXY_METER_PROVIDER._lock` -> `_ProxyMeter._lock`.

## Goals / Non-Goals

**Goals:**

- Break `CHAIN-01` and `CHAIN-02` completely via Python 3.13 `ArlogiSyslogHandler` liveness/degradation fixes plus `_closed` lifecycle guards across `ArlogiSyslogHandler`, `JSONHandler`, and `_RotatingJsonlWriter`.
- Centralize `json_file_name`, `base_dir` / `json_file_base_dir`, `rotate_schedule`, and `rotate_retention_count` validation in `src/arlogi/config.py` with fail-fast `ValueError` before filesystem side effects.
- Harden OpenTelemetry restart-gap resilience (`_ProxyMeter` reset, `ProxyTracerProvider` cache exclusion, `functools.partial` correlation discovery, strict OTLP endpoint parsing, and dead-stream closure).
- Synchronize published `docs/`, `README.md`, `mkdocs.yml`, and `docs/C4-Documentation/` with runtime contracts while removing leaked internal metadata.

**Non-Goals:**

- Introducing new public API functions, configuration fields, or runtime dependencies.
- Modifying `.github/workflows/*.yml` or `pyproject.toml` packaging metadata.
- Changing stdlib `SysLogHandler` globally via monkey-patching; fixes stay encapsulated in `ArlogiSyslogHandler`.

## Decisions

### D1. Shared Configuration & Path Validators (DA-002, DA-018, DA-019) — Fail-Fast

Centralize four small helpers in `src/arlogi/config.py` (stdlib-only, alongside `validate_syslog_format()`):

- `validate_json_file_name(value: Any) -> str`: requires `isinstance(value, str)`, `bool(value.strip())`, and `"\x00" not in value`; raises `ValueError("json_file_name must be a non-empty string when provided")`.
- `validate_base_dir(value: Any) -> str | Path`: rejects `bool` and non-`(str, Path)` types; requires `bool(str(value).strip())` and `"\x00" not in str(value)`; raises `ValueError("base_dir must be a non-empty path when provided")`. (Note: `JSONFileHandler._resolve_within_base()` accepts `str | Path` and `LoggingConfig.json_file_base_dir` stores `str | None` in normal usage; validating `(str, Path)` preserves existing `JSONFileHandler` `Path` support while blocking `""`, `"   "`, `123`, `True`, and `"\x00"`.)
- `validate_rotate_schedule(value: Any) -> RotateSchedule`: checks `isinstance(value, str)` before `value not in VALID_ROTATE_SCHEDULES`, raising `ValueError(f"Invalid rotate_schedule: {value!r}. Valid values: ...")` so unhashable inputs (`["day"]`, `{}`) never raise `TypeError`.
- `validate_rotate_retention_count(value: Any) -> int`: rejects `bool`, non-`int`, or `< 1` with `ValueError`.

Callers:
- `LoggingConfig.__post_init__` delegates `json_file_name`, `json_file_base_dir`, `rotate_schedule`, and `rotate_retention_count` when not `None`.
- `LoggerFactory.get_json_logger()` delegates `json_file_name` and `base_dir` (when not `None`) under input validation before acquiring `_dedicated_lock` / opening handlers.
- `HandlerFactory.create_json_file()` delegates `validate_json_file_name(config.json_file_name)` when not `None` (raising `ValueError("json_file_name must be set in config")` if `None`).
- `JSONFileHandler.__init__()` validates `rotate_schedule`, `rotate_retention_count`, `filename` (always, even when `base_dir is None`), and `base_dir` (inside `_resolve_within_base` / prior to `os.path.abspath` and `os.makedirs`).
- Existing test `tests/test_coverage_boost.py:258` (`match="Unsupported rotate_schedule"`) updates to match unified `"Invalid rotate_schedule"` (consistent with `tests/test_rotation_config.py:25`).

Alternative rejected: keeping per-module inline checks — already caused behavioral drift (`IsADirectoryError`, `AttributeError`, `TypeError`).

### D2. Python 3.13 `ArlogiSyslogHandler` Liveness, Degradation & `TRACE` Priority (DA-001, DA-003, DA-007, CHAIN-01)

1. **`TRACE` priority (`DA-003`)**: Class attribute `priority_map = {**logging.handlers.SysLogHandler.priority_map, "TRACE": "debug"}` on `ArlogiSyslogHandler` maps `TRACE` (`5`) to RFC syslog `DEBUG` (`<15>` for `LOG_USER`).
2. **Initialization socket liveness check (`DA-001`)**: Extract small helper `_has_live_socket(handler) -> bool` checking `sock is not None and sock.fileno() != -1`. After `super().__init__(address=target_address, ...)` returns normally, if `isinstance(target_address, str)` and not `_has_live_socket(self)`:
   - Close the dead socket via `_close_socket_locked()`.
   - Treat it as a connection failure (`raise OSError(...)` inside the `try:` block) so `address == "/dev/log"` falls back to `("localhost", 514)` (and degrades to `_failed = True` if UDP also fails), while non-`"/dev/log"` custom Unix socket paths fail fast with `OSError` to the caller (aligning with TCP/UDP and `documentation-sync/spec.md:25`).
   - Update `tests/test_coverage_boost.py:188-191` (use `address="/dev/log"` or assert `pytest.raises(OSError)` for custom Unix path) and `:206-213` (mock `sock.sendto` or use `"/dev/log"` fallback rather than assuming nonexistent custom Unix socket succeeds).
3. **Transport `OSError` degradation (`DA-001`)**: Override `handleError(self, record)` on `ArlogiSyslogHandler`: inspect `exc_type = sys.exc_info()[0]`; if `exc_type is not None and issubclass(exc_type, OSError)`, set `self._failed = True` and call `self._close_socket_locked()` without delegating to `logging.Handler.handleError(record)` (stopping `stderr` traceback storms on unreachable/broken sockets). For non-`OSError` errors (e.g., broken custom record formatting), delegate to `super().handleError(record)` so unrelated programming bugs are not masked or permanently fatal to the handler. Keep the `except Exception:` safety net in `emit()`.
4. **Concurrency & `_closed` guards (`DA-007`, `CHAIN-01`)**:
   - Initialize `self._closed = False` in `ArlogiSyslogHandler.__init__()` (including the `_failed = True` fallback branch).
   - In `ArlogiSyslogHandler.close()`, under `self.acquire()`/`self.release()` (which uses `threading.RLock`), set `self._closed = True` before closing any socket.
   - At the top of `ArlogiSyslogHandler.emit()`, return immediately when `getattr(self, "_closed", False) or getattr(self, "_failed", False)` is `True` (before `super().emit(record)` can see `not self.socket` and call `createSocket()`).
   - Locking note: `logging.Handler.handle()` acquires `self.lock` (`RLock`) around `emit()` and `handleError()`; `_close_socket_locked()` re-acquires the same `RLock` cleanly without deadlock.
   - Sibling `JSONHandler.emit()` overrides `StreamHandler.emit()` to return immediately under `self.acquire()`/`self.release()` (or fast-path check) when `getattr(self, "_closed", False)` is `True`, avoiding post-close `AttributeError` into `handleError()`.

Alternative rejected: monkey-patching `SysLogHandler.createSocket` — fragile across CPython point releases and unnecessary when `_has_live_socket()` detects swallowed Unix socket failures directly.

### D3. `JSONFileHandler` Post-`os.replace()` State & Pruning Order (DA-004)

In `JSONFileHandler._rotate_now_locked()`:
- Immediately after `os.replace(self.baseFilename, target)` succeeds on disk, update `self._active_period_key = next_key` and call `self._prune_rotated_files()` **before** `self.stream = self._open()`.
- Extract `_reopen_after_rotation_error()` or pass/avoid double reporting: in `except OSError:` inside `_try_ensure_stream_open()`, only report if not already inside `_rotate_now_locked()`'s outer `except Exception:` (or let `_try_ensure_stream_open()` stay non-reporting when called from `except Exception:` which already calls `_report_rotation_error()`). This ensures persistent `_open()` failures report once and `rotate_now()` returns `False` on `_open()` failure without leaving `_active_period_key` stale or leaving expired archives unpruned.

### D4. OpenTelemetry Proxy Meter Reset & `functools.partial` Correlation (DA-005, DA-008)

1. **`_clear_global_meter_provider()` (`DA-005`)**: Inside `with proxy_lock:`, extract `_reset_proxy_meters_locked(proxy)` to iterate `getattr(proxy, "_meters", ())`:
   - For each `meter` exposing `_lock` and `_real_meter`, acquire `with meter._lock:` (preserving upstream `_ProxyMeterProvider._lock` -> `_ProxyMeter._lock` acquisition order, preventing deadlocks), set `meter._real_meter = None`, and iterate `getattr(meter, "_instruments", ())` setting `inst._real_instrument = None` when `hasattr(inst, "_real_instrument")`.
   - Mirror the identical reset in `tests/conftest.py:reset_otel_globals` so test teardown cleans pre-existing proxy meters as well.
2. **`_child_factories()` (`DA-008`)**: When `isinstance(node, functools.partial)`, append `node.func`, `[arg for arg in node.args if callable(arg)]`, and `[val for val in (node.keywords or {}).values() if callable(val)]`.

### D5. Strict OTLP Endpoint Validation (DA-011) — Fail-Fast

- In `setup_tracing()` (`bootstrap.py:162`) and `setup_metrics()` (`bootstrap.py:303`), check `if otlp_endpoint is not None and otlp_endpoint != "":` so `None` and `""` (e.g., `os.environ.get("OTLP_ENDPOINT", "")`) disable remote OTLP export cleanly (keeping file-only export enabled), while whitespace (`" "`), falsy non-`str` values (`0`, `False`), and malformed strings still enter `_validate_otlp_endpoint()` and fail fast before constructing exporters or threads.
- In `_validate_otlp_endpoint(endpoint)`:
  - Reject any `'?'`, `'#'`, or `';'` character anywhere in `endpoint` (catching trailing empty delimiters like `http://collector:4318?`, `#`, `/otlp;`).
  - Extract a small helper `_validate_netloc_port(parsed)` to inspect `parsed.netloc` (after any `@` userinfo): detect dangling empty port `:` (handling IPv6 `[...]:` vs host`:` cleanly) and check `parsed.port` is either `None` or `1 <= port <= 65535` (rejecting port `0`).

### D6. `@traced` Proxy Cache Exclusion (DA-014)

- In `_make_tracer_getter()` (`src/arlogi/otel/decorator.py:42-50`), do not update `cache` when `isinstance(current_provider, trace.ProxyTracerProvider)` — return `current_provider.get_tracer(module)` directly. Once a real SDK `TracerProvider` is active, `(current_provider, tracer)` is cached normally, so hot-path overhead with an active SDK provider is unchanged, while proxy-provider calls during startup races or shutdown gaps never cache or latch an SDK tracer under `_PROXY_TRACER_PROVIDER`.
- `trace.ProxyTracerProvider` is imported from `opentelemetry.trace` (`opentelemetry-api`), preserving the `no-otel` / SDK-free `INV-1` boundary.

### D7. `_RotatingJsonlWriter` Close Guard & Dead-Stream Cleanup (DA-006, DA-013, CHAIN-02)

- Add `self._closed = False` in `_RotatingJsonlWriter.__init__()`.
- Extract `_close_stream_locked(self) -> None` to best-effort close `self._stream` (suppressing `OSError`) and set `self._stream = None`.
- In `close()`: under `self._lock`, set `self._closed = True`, `self._active_path = None`, and call `self._close_stream_locked()`.
- In `write_line()`: check `if self._broken or self._closed: return False` both before and inside `with self._lock:`. Because external `_stream.close()` calls do not invoke `writer.close()`, `self._closed` stays `False` and external-stream self-healing remains intact.
- In `write_line()`'s `except OSError` handler: set `self._broken = True`, call `self._close_stream_locked()` under `self._lock`, and log one warning, releasing the dead FD immediately.

### D8. Documentation Sync, C4 Scrubbing & MkDocs Enforcement (DA-009, DA-010, DA-012, DA-015, DA-016, DA-017)

- Delete `docs/C4-Documentation/c4-code-docs-scripts.md` and `docs/C4-Documentation/c4-code-subdir.md`, remove both entries from `mkdocs.yml`, and scrub all occurrences of `192.168.168.5`, `http://192.168.168.5/cpaiops/`, `root`, `$HOME/.ssh/il-ed25519`, `/opt/c/nginx/html/arlogi`, and `/opt/Code/2026/_Libs/arlogi` across `docs/C4-Documentation/` and `README.md:167` (using the public GitHub Pages URL `https://antragh.github.io/arlogi/` and repo-relative file paths).
- Update `docs/C4-Documentation/` (`c4-component-core-logging.md`, `c4-container.md`, `c4-code-tests-example.md`, `c4-code-src-arlogi.md`, `apis/arlogi-api.yaml`), `docs/ARCHITECTURE.md`, `docs/API_REFERENCE.md`, `docs/CONFIGURATION_GUIDE.md`, `docs/CALLER_ATTRIBUTION_EXAMPLES.md`, `docs/DEVELOPER_GUIDE.md`, `docs/index.md`, and `README.md` to eliminate all documented drift (`DA-009`, `DA-010`, `DA-015`, `DA-016`, `DA-017`).
- Add `validation: links: anchors: warn` to `mkdocs.yml` so `uv run mkdocs build --strict` fails on any broken heading anchor.

### Error-Recovery & Boundary Matrix

| Component / Path | Policy | Behavior |
| --- | --- | --- |
| Config, `base_dir`, `filename`, `rotate_schedule`, `retention`, OTLP endpoint, custom Unix syslog socket | **Fail-fast** | Raise `ValueError` or `OSError` before directory creation, file open, handler swap, or OTEL background thread creation |
| `ArlogiSyslogHandler("/dev/log")` init & runtime transport `OSError` | **Fail-open** | Fall back to UDP `("localhost", 514)` or latch `_failed = True`, close socket under lock, drop records silently without `stderr` flooding |
| `JSONFileHandler` rotation / `_open()` / pruning I/O errors | **Fail-open** | Advance period key & prune right after `os.replace()`; return `False` on `_open()` failure without uncaught exceptions |
| Post-close `emit()` / post-shutdown `write_line()` | **Fail-open (no-op / `FAILURE`)** | Return immediately (`_closed == True`) without reopening sockets/files; exporters return `FAILURE` |
| `arlogi` core without `[otel]` (`no-otel` matrix leg) | **Zero OTEL imports** | Shared validators in `src/arlogi/config.py` use stdlib only; `decorator.py` uses `opentelemetry-api` only (`ProxyTracerProvider`); `conftest.py` keeps `ImportError` guard |

## Risks / Trade-offs

- [Custom nonexistent Unix syslog socket path raises `OSError` on Python 3.13] -> Matches TCP/UDP behavior and `documentation-sync/spec.md:25`; `tests/test_coverage_boost.py` updated to test `/dev/log` fallback and custom Unix fail-fast explicitly.
- [Stricter `base_dir` and `otlp_endpoint` validation rejects previously ignored inputs (`""`, `"   "`, `:0`, trailing `?`/`#`/`;`)] -> Prevents silent CWD containment weakening and malformed OTLP URLs/thread creation; documented in `proposal.md`.
- [`JSONFileHandler` error string changes from `"Unsupported rotate_schedule"` to `"Invalid rotate_schedule"`] -> Unifies with `LoggingConfig`; `tests/test_coverage_boost.py:258` updated accordingly.
- [Resetting `_ProxyMeter._real_meter` during `_clear_global_meter_provider()` relies on upstream `opentelemetry-api` private attributes] -> Guarded by `hasattr`/`getattr` checks and lock-ordered (`proxy._lock` -> `meter._lock`) inside existing `try/except Exception` fallback so incompatible upstream builds still clear the global slot cleanly.

## Migration Plan

Single non-schema release. No on-disk log/telemetry format changes; rollback is a clean revert.
