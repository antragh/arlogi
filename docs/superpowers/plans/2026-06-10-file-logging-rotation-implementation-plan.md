# Implementation Plan: Optional File Logging Rotation

Date: 2026-06-10

Source spec: docs/superpowers/specs/2026-06-10-file-logging-rotation-design.md

Status: Ready for implementation

## 1. Scope and Guardrails

- Implement optional schedule-based rotation for JSON file logging.
- Implement on-demand rotation APIs (handler + convenience helper).
- Preserve backward compatibility when schedule is not configured.
- Do not introduce mirror-related commits or behavior changes.

## 2. Work Breakdown Structure

### Phase A - Config and API Contracts

1. Add rotation config fields to LoggingConfig in src/arlogi/config.py:

- rotate_schedule: Literal["hour", "day", "week", "month"] | None = None
- rotate_retention_count: int | None = None

2. Validation rules in LoggingConfig.__post_init__:

- rotate_schedule must be one of hour/day/week/month when provided.
- rotate_retention_count must be >= 1 when provided.
- if rotate_schedule is set and rotate_retention_count is None, resolve default to 7 at handler/config-consumer boundary.

3. Extend kwargs compatibility path in LoggingConfig.from_kwargs valid_keys.

4. Extend setup surfaces:

- src/arlogi/factory.py setup_logging(...) new optional kwargs.
- src/arlogi/config_builder.py add fluent method for rotation config.

Acceptance checks:

- Existing calls to setup_logging and builder methods remain valid.
- New options are optional and validated.

### Phase B - Handler Factory Wiring

1. Update src/arlogi/handler_factory.py create_json_file(...) to pass rotation fields to JSONFileHandler.
2. Keep behavior identical when rotate_schedule is None.

Acceptance checks:

- Existing handler creation tests still pass.
- Rotation params are only used for file handler path.

### Phase C - JSONFileHandler Rotation Engine

1. Extend src/arlogi/handlers.py JSONFileHandler:

- store rotation config and active_period_key.
- add helpers:
  - _compute_period_key(now_local)
  - _build_rotated_path(period_key)
  - _build_collision_safe_path(base_target)
  - _prune_rotated_files()
  - _should_rotate_on_emit()

2. Add rotate_now() -> bool:

- lock handler
- flush/close stream
- rename base file to rotated target (collision-safe)
- reopen base stream
- prune rotated files based on retention count
- recover writable stream on errors, return False on no-op/error

3. Integrate scheduled check on emit path:

- if schedule enabled and period key changes, rotate before write.
- then write current record.

4. Weekly key semantics:

- Sunday-based week numbering equivalent to strftime("%U").

Acceptance checks:

- No schedule: file writing behavior unchanged.
- Scheduled boundary crossing rotates first, then writes.
- rotate_now works independently of schedule.

### Phase D - Public Convenience API

1. Add rotate_json_logger(name: str = "json") -> int in src/arlogi/factory.py.
2. Export helper in public package surface if needed by current API conventions.
3. Helper behavior:

- find logger arlogi.<name>
- rotate JSONFileHandler instances
- return count of successful rotations

Acceptance checks:

- No handlers present -> returns 0, no exception.
- Works for configured JSON file loggers.

### Phase E - Tests

1. Unit tests (new or expanded):

- config validation for rotate_schedule and rotate_retention_count
- period key generation for hour/day/week/month
- filename mapping and collision suffixing
- retention pruning keeps newest N (default 7 when scheduled)

2. Integration tests:

- emit-triggered rotation across mocked boundary transitions
- rotate_now on non-empty and missing base file
- rotate_json_logger helper returns correct counts

3. Concurrency/resource tests:

- concurrent emits around boundary do not crash
- stream reopen/cleanup still correct

Acceptance checks:

- full test suite passes
- no regressions in existing resource/thread-safety tests

### Phase F - Documentation Updates

1. Update docs/CONFIGURATION_GUIDE.md with rotation options and defaults.
2. Update docs/USER_GUIDE.md examples for hour/day/week/month schedules.
3. Mention Sunday week boundary and retention default behavior.

Acceptance checks:

- docs reflect exact API names and defaults.
- examples are executable/consistent with tests.

## 3. Suggested Implementation Order

1. Phase A
2. Phase B
3. Phase C
4. Phase D
5. Phase E
6. Phase F

## 4. Risk Register and Mitigations

- Risk: boundary logic ambiguity for weekly keys.
  - Mitigation: enforce strftime("%U") semantics in helper + tests.
- Risk: rotation failures break logging.
  - Mitigation: best-effort recovery and non-fatal error handling path.
- Risk: filename collisions on repeated manual rotate.
  - Mitigation: deterministic numeric suffix collision resolver.
- Risk: backward-compat regressions.
  - Mitigation: keep no-schedule fast path and explicit regression tests.

## 5. Definition of Done

- All phases completed.
- Existing test suite passes.
- New tests cover schedule + on-demand + retention behavior.
- No behavior change when rotation schedule is not provided.
- Documentation updated for new configuration and helper API.
