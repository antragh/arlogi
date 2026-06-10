# File Logging Rotation Design

Date: 2026-06-10

Status: Approved for planning

Scope: arlogi file logging only (JSON file handler path)

## 1. Objective

Add optional file rotation to existing file logging with two capabilities:

- On-demand rotation via API.
- Schedule-based rotation checked on each file log emit.

Rotation is disabled by default. If no schedule is configured, behavior remains unchanged.

## 2. Requirements (Validated)

- Rotation boundary source: local machine wall-clock time.
- Supported schedules: hour, day, week, month.
- Weekly boundary: Sunday at 00:00 local time.
- On-demand API style: both handler-level and public helper.
- Rotated filename style: period key suffix before extension, e.g. app-2026-06-10-14.jsonl.
- Retention: keep last N rotated files.
- Default retention count: 7.
- Rotation check moment: before writing each log record to file.

## 3. Non-Goals

- Compression of rotated files.
- Size-based rotation.
- Multi-process locking guarantees across separate processes.
- Remote storage lifecycle management.

## 4. High-Level Architecture

Approach: extend existing JSONFileHandler with optional internal time-window rotation logic.

Components impacted:

- src/arlogi/handlers.py
  - Extend JSONFileHandler with rotation configuration and runtime state.
  - Add rotate_now() method.
- src/arlogi/config.py
  - Add optional config fields for schedule and retention.
- src/arlogi/config_builder.py
  - Add builder method(s) for rotation options.
- src/arlogi/handler_factory.py
  - Pass rotation options when creating JSONFileHandler.
- src/arlogi/factory.py
  - Expose convenience helper rotate_json_logger(...).
  - Add optional setup kwargs so legacy entrypoint can configure rotation.

## 5. Public API Design

### 5.1 Configuration Surface

Add optional setup/config options:

- rotate_schedule: Literal["hour", "day", "week", "month"] | None = None
- rotate_retention_count: int | None = None

Behavior:

- rotate_schedule is None: no rotation checks, current behavior unchanged.
- rotate_schedule set and rotate_retention_count omitted: default retention is 7.
- rotate_retention_count must be >= 1 when provided.

### 5.2 Handler Surface

On JSONFileHandler:

- rotate_now() -> bool
  - Returns True when a rotation action completed.
  - Returns False for no-op conditions (no existing base file content to rotate).

### 5.3 Convenience Helper

Public function:

- rotate_json_logger(name: str = "json") -> int
  - Finds JSONFileHandler instances on arlogi.<name> logger.
  - Calls rotate_now() on each.
  - Returns count of handlers successfully rotated.
  - No-op and returns 0 when logger/handlers are absent.

## 6. Rotation Semantics

## 6.1 Period Keys (local time)

- hour: YYYY-MM-DD-HH
- day: YYYY-MM-DD
- week: YYYY-Www where ww uses Sunday-based week numbering equivalent to strftime("%U"), with Sunday 00:00 as boundary and zero-padded 2-digit week number
- month: YYYY-MM

The handler stores active_period_key after open/rotate.
On each emit (when schedule enabled):

1. compute current period key from datetime.now() in local time.
2. if key differs from active_period_key, rotate first.
3. write current record to base file.

## 6.2 Filename Mapping

Base active file remains unchanged, e.g. app.jsonl.
Rotated file target uses period key suffix before extension:

- app-2026-06-10-14.jsonl
- app-2026-06-10.jsonl
- app-2026-W23.jsonl
- app-2026-06.jsonl

Collision handling in same period (for repeated manual rotation):

- append .1, .2, ... before extension, e.g. app-2026-06-10-14.1.jsonl.

## 6.3 Retention

When schedule is enabled, prune rotated files after a successful rotate.
Policy:

- keep newest N rotated files matching this base name pattern.
- N defaults to 7 unless explicitly configured.
- never delete active base file.

## 7. Error Handling and Recovery

Design principle: logging remains non-fatal.

Rotation order (under handler lock):

1. flush stream
2. close stream
3. rename base file to rotated target
4. reopen base stream
5. prune old rotated files

Failure behavior:

- Any error during rotate/prune must not crash caller.
- Handler attempts to restore writable base stream before returning.
- Use standard logging handler error path for diagnostics.
- Missing/empty base file at rotate time is treated as no-op; ensure writable base stream.

## 8. Concurrency and Isolation

- Use existing Handler lock path to keep emit and rotate atomic per handler instance.
- No additional global locks.
- Directory creation semantics remain as currently implemented.
- Cross-process races for same file are out of scope for this change.

## 9. Backward Compatibility

- If rotate_schedule is not provided, API and behavior remain identical.
- Existing setup_logging/get_json_logger usage continues to work.
- Existing tests should remain valid except signature assertions that need expansion for new optional args.

## 10. Test Plan

Unit tests:

- period key generation for hour/day/week/month around boundaries.
- weekly Sunday boundary logic.
- rotated filename generation and collision suffixing.
- retention pruning keeps newest N and excludes active base file.

Integration tests:

- emit-triggered rotate when period key changes.
- rotate_now() behavior on non-empty and missing base file.
- rotate_json_logger(...) rotates applicable handlers and returns count.

Concurrency tests:

- concurrent emits around boundary transition do not crash and keep writes valid.

Compatibility tests:

- no schedule configured yields current file output behavior.
- resource management expectations still hold (close/reopen/cleanup patterns).

## 11. Rollout Notes

- Feature is opt-in and safe to release in minor version.
- Document in user guide/config guide with examples for each schedule.
- Mention retention default of 7 when schedule is enabled.

## 12. Open Questions

None. All requirement choices were explicitly validated with user input.
