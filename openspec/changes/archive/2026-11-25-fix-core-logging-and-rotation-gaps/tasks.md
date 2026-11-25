# Tasks

## 1. Shared archive pruning helper (DA-009, DA-025, DA-026)

- [x] 1.1 Create `src/arlogi/_rotation.py` with a stdlib-only `prune_archives(directory, pattern, keep, active_path=None)` per design D4 (regular files only via `is_file(follow_symlinks=False)`, `stat(follow_symlinks=False).st_mtime_ns`, descending `(mtime_ns, stamp, int(suffix or 0))` ordering, realpath active-file exclusion, non-fatal `OSError`); verify `uv run ruff check src/arlogi/_rotation.py` passes and the module imports no `opentelemetry`.
- [x] 1.2 Add unit tests for the helper (new `tests/test_rotation_helper.py`): matching directory and symlink never counted or deleted; equal-`st_mtime_ns` archives `x.jsonl`, `x.1.jsonl`, `x.2.jsonl`, `x.10.jsonl` keep the highest suffixes; active file excluded by resolved path; `OSError` on stat/unlink/scandir swallowed (monkeypatched); verify `uv run pytest tests/test_rotation_helper.py` passes.
- [x] 1.3 Delegate `JSONFileHandler._prune_rotated_files()` to the helper with a pattern precompiled once in `__init__` (named groups `stamp`/`suffix`, same accepted formats as today); verify existing `tests/test_file_rotation.py` pruning tests (sibling `app-audit.jsonl`, `svc[v2]/` directory) still pass.
- [x] 1.4 Add regression tests in `tests/test_file_rotation.py` for the audit reproductions: newer matching directory `app-2026-06-15.jsonl/` and symlink `app-2026-06-16.jsonl` with `rotate_retention_count=2` no longer evict `app-2026-06-10.jsonl`; equal-mtime `.jsonl`/`.1`/`.2` archives prune the unsuffixed one (use `os.utime(..., ns=...)`); assert surviving file names, not just counts; verify the tests fail on the old code and pass after 1.3.
- [x] 1.5 Delegate `_RotatingJsonlWriter._prune()` in `src/arlogi/otel/_files.py` to the helper (add named groups to `_archive_pattern`, `keep = retention_count - 1` when an active file exists); touch nothing else in that module; verify `uv run pytest tests/test_otel_exporter.py` passes.
- [x] 1.6 Add OTEL-guarded regression tests in `tests/test_otel_exporter.py` (`pytest.importorskip` consistent with the file) reproducing DA-009/DA-026: equal-mtime `traces-20200101-000000.jsonl` / `traces-20200101-000001.jsonl` with `retention_count=2` keeps `…000001.jsonl`; a newer matching directory does not evict the real archive; verify the tests pass.
- [x] 1.7 Add a no-otel boundary test asserting that importing `arlogi` and `arlogi._rotation` loads no `opentelemetry*` module in `sys.modules` (run in a subprocess); verify it passes in both the otel and no-otel environments.

## 2. JSON file handler rotation naming and validation (DA-001, DA-008)

- [x] 2.1 Implement design D1 in `JSONFileHandler._rotate_now_locked()` (scheduled: archive under `_active_period_key or current`, advance to current; unscheduled: fresh current-hour key, never persist `_active_period_key`); verify with 2.2.
- [x] 2.2 Add regression tests in `tests/test_file_rotation.py` reproducing DA-001: (a) `get_json_logger("audit", path)` + `rotate_json_logger("audit")` at `2026-06-10 10:00`, `2026-06-13 15:00`, `2026-07-01 09:00` (patched `_now_local`) yields `audit-2026-06-10-10.jsonl`, `audit-2026-06-13-15.jsonl`, `audit-2026-07-01-09.jsonl`; (b) empty-file no-op then rotation on `2026-07-01 09:00` yields `audit-2026-07-01-09.jsonl`; (c) daily handler with `2026-06-10` events and `rotate_now()` at `2026-06-11 00:05` yields `app-2026-06-10.jsonl`; verify all pass and existing boundary tests still pass.
- [x] 2.3 Add a shared `VALID_ROTATE_SCHEDULES` constant in `src/arlogi/config.py`, use it in `LoggingConfig.__post_init__`, and validate `rotate_schedule`/`rotate_retention_count` at the top of `JSONFileHandler.__init__` before any filesystem call (design D3); verify `uv run ruff check src/` passes (complexity ≤ 10).
- [x] 2.4 Add regression tests in `tests/test_rotation_config.py` reproducing DA-008: `JSONFileHandler("sub/app.jsonl", rotate_schedule="invalid")` and `rotate_schedule=""` raise `ValueError`, leave no `sub/` directory, and emit no `ResourceWarning` (use `warnings.catch_warnings(record=True)` + `gc.collect()`); `rotate_retention_count` of `0`, `-1`, `True`, `False`, `"7"` raises `ValueError`; verify they pass.

## 3. Handler close semantics (DA-004, DA-022)

- [x] 3.1 Implement design D2 in `JSONHandler` (`_owns_stream` excludes `sys.stderr`, `sys.stdout`, `sys.__stderr__`, `sys.__stdout__`; `close()` uses `try: flush() finally:` to close/release owned streams); verify with 3.2.
- [x] 3.2 Add regression tests in `tests/test_resource_management.py` reproducing DA-004: a stream whose `flush()` raises `BrokenPipeError` is closed and `handler.stream is None` after `close()`, and a second `close()` does not raise; `JSONHandler(stream=sys.stderr)` closed inside `contextlib.redirect_stderr(io.StringIO())` leaves the original stderr open; verify the existing `JSONHandler(stream=sys.stderr)` test at line ~167 still passes.
- [x] 3.3 Implement design D11 in `ArlogiSyslogHandler` (`self.socket = None` on failed init, close the socket under lock when `emit()` flips `_failed`, `close()` always delegates to `SysLogHandler.close()` safely); verify with 3.4.
- [x] 3.4 Add regression tests in `tests/test_resource_management.py` reproducing DA-022: a UDP handler to `("localhost", 514)` whose `emit()` path raises `ValueError` (e.g. monkeypatched `handleError` or closed fake `sys.stderr`) has `socket.fileno() == -1` (or `socket is None`) after `close()`; a fully failed-init handler can be closed twice without raising; verify existing `tests/test_coverage_boost.py` syslog tests still pass.

## 4. Logger factory concurrency and attribution (DA-012, DA-017)

- [x] 4.1 Implement design D5: add `LoggerFactory._swap_handlers()` (dedupe, single `logger.handlers = [...]` rebinding, close removed handlers after the swap) and route `_clear_and_add_handlers()`, `_replace_logger_handlers()`, and `_detach_and_close_handlers()` through it under their existing locks; verify existing `tests/test_thread_safety.py` and create-before-detach tests pass.
- [x] 4.2 Add regression tests in `tests/test_thread_safety.py` reproducing DA-012 (with `sys.setswitchinterval(1e-6)` restored in `finally`): concurrent `WARNING` emission to `arlogi.json.audit` while another thread loops `get_json_logger("audit", path)` produces zero `logging.lastResort` writes (patch `logging.lastResort` with a counting handler); concurrent emission on a root logger with three counting handlers while reapplying an equivalent three-handler set via the swap helper yields exactly three hits per record; verify the tests fail on the old remove-before-add code and pass after 4.1.
- [x] 4.3 Implement design D7 in `TraceLogger._apply_caller_attribution()` (bool → no attribution; negative → no attribution); verify with 4.4.
- [x] 4.4 Add regression tests in `tests/test_features.py` reproducing DA-017: `logger.info("test", caller_depth=d)` for `d` in `-1..-5` and for `True`/`False` emits exactly `"test"` with no `_arlogi_attribution` extra; verify existing `caller_depth` tests still pass.

## 5. TRACE registration (DA-005)

- [x] 5.1 Implement design D6 in `register_trace_level()` (independent conditional steps under `_trace_lock`, no overwrite of foreign `logging.TRACE`/`Logger.trace`, first parameter renamed to `msg`); verify `uv run ruff check src/arlogi/levels.py` passes.
- [x] 5.2 Add subprocess-based regression tests in `tests/test_core.py` reproducing DA-005: with `logging.TRACE = 5` and `logging.getLogger("app.worker")` created before `arlogi.get_logger("app.worker")`, assert `logging.getLevelName(5) == "TRACE"`, `hasattr(logger, "trace")`, `isinstance(logger, LoggerProtocol)`; in a clean subprocess, `pre_existing.trace(msg="kwarg")` emits a level-5 record without `TypeError`; replace the assertion-free `test_register_trace_level_hasattr_true_branch` in `tests/test_coverage_boost.py` with meaningful assertions; verify they pass.

## 6. Configuration entrypoints (DA-013, DA-018, DA-020, DA-021)

- [x] 6.1 Implement design D8: introduce the `_Unset` enum sentinel, make it the default for all configuration parameters of `LoggerFactory.setup()` and `setup_logging()`, reject any non-sentinel parameter combined with `config`, drop sentinels before `LoggingConfig.from_kwargs()`, delete `_SETUP_DEFAULTS`, and update docstrings to state effective defaults; verify the type checker (`uv run ty check` if configured locally) reports no new errors.
- [x] 6.2 Add regression tests in `tests/test_core.py` reproducing DA-013: with `cfg = LoggingConfigBuilder().with_level("DEBUG").with_syslog().with_json_file("app.jsonl", console_also=False).build()`, each of `level=logging.INFO`, `use_syslog=False`, `json_file_name=None`, `json_file_only=False`, `show_time=False`, `show_level=True`, `show_path=True`, `syslog_address="/dev/log"`, `rotate_schedule=None`, `rotate_retention_count=None`, `module_levels=None`, `json_file_base_dir=None` combined with `config=cfg` raises `ValueError` (parametrized, for both `setup_logging` and `LoggerFactory.setup`); `setup_logging()` without `config` still yields default behavior; verify they pass.
- [x] 6.3 Implement design D9 in `LoggerFactory.get_logger()` (resolve via `LoggingConfig._parse_level`, with case-insensitive `"NOTSET"` → `0`, before `setLevel()`); verify with 6.4.
- [x] 6.4 Add regression tests in `tests/test_core.py` reproducing DA-018: `get_logger("x", level="trace")` → level `5`, `level="debug"` → `10`, `level="NOTSET"` and `logging.NOTSET` → `0`, `level=True`/`False` raise `ValueError` and leave the prior level unchanged; verify they pass.
- [x] 6.5 Implement design D10: non-empty `str` validation of `json_file_name` in `LoggingConfig.__post_init__` and `LoggerFactory.get_json_logger()`, `is not None` checks in `HandlerFactory.create_handlers()`, `create_json_handler()`, `create_json_file()`, and the `get_json_logger()` `base_dir` guard; clear `_json_file_base_dir` in `LoggingConfigBuilder.with_json_console_only()`; verify with 6.6.
- [x] 6.6 Add regression tests reproducing DA-020/DA-021 (in `tests/test_core.py` / `tests/test_rotation_config.py`): `LoggingConfig(json_file_name="")`, `"   "` with `json_file_base_dir="/tmp"`, `123`, `LoggingConfigBuilder().with_json_file("").build()`, `setup_logging(json_file_name="", json_file_base_dir=...)`, `get_json_logger("audit", "")`, and `get_json_logger("audit", "", base_dir="/tmp")` all raise `ValueError` (message mentions non-empty file name); `get_json_logger("audit")` still attaches a stderr `JSONHandler`; `.with_json_file("a.jsonl").with_json_base_dir("/tmp").with_json_console_only().build().json_file_base_dir is None`; verify they pass.

## 7. Integration verification

- [x] 7.1 Run `uv run pytest` in the full environment (`uv sync --frozen --group test --extra otel`) and verify all tests pass.
- [x] 7.2 Run `uv run pytest` in a no-otel environment (`uv sync --frozen --group test`, mirroring the CI "Core Only (no-otel)" job) and verify all core tests pass with OTEL tests skipped.
- [x] 7.3 Run `uv run ruff check src/ tests/` and verify it reports no errors (including `max-complexity=10`).
- [x] 7.4 Run `uv run ruff format --check src/ tests/` and verify no files would be reformatted.
- [x] 7.5 Run `openspec validate fix-core-logging-and-rotation-gaps --strict` and verify the change is valid.

## Workflow follow-up

- User-facing docs (`docs/API_REFERENCE.md`, `docs/CONFIGURATION_GUIDE.md`) for the behavior changes listed in proposal Impact are refreshed by the sibling change `remove-graphify-and-sync-ci-docs`.
- Archive the change after review; verify the merged main specs afterwards.
