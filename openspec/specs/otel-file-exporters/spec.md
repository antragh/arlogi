# otel-file-exporters Specification

## Purpose
Defines safe prefix and parameter validation, non-fatal retention pruning, and exporter resilience for `arlogi.otel`'s rotating JSONL span and metric file writers.

## Requirements

### Requirement: Safe prefix and positive integer bounds validation in rotating JSONL writers

`_RotatingJsonlWriter` (and the `setup_tracing`, `setup_metrics`, `RotatingJsonlSpanExporter`, and `RotatingJsonlMetricExporter` entrypoints) SHALL require `prefix`/`file_prefix` to be a non-empty single filename component free of path separators (`/`, `\`), parent segments (`..`), NUL bytes, and glob metacharacters (`*`, `?`, `[`, `]`), and SHALL require `rotate_hours` and `retention_count` to be non-boolean integers `>= 1`.

#### Scenario: Rejecting path traversal, absolute paths, and glob metacharacters in prefix

- **WHEN** `_RotatingJsonlWriter` or `setup_tracing(..., file_prefix=...)` is constructed with `"../escape"`, `"/tmp/abs"`, `"sub/dir"`, `"*"`, or `"svc[1]"`
- **THEN** initialization MUST raise `ValueError`

#### Scenario: Rejecting non-positive or boolean rotate_hours and retention_count

- **WHEN** `_RotatingJsonlWriter` is constructed with `retention_count=0`, `retention_count=-1`, `rotate_hours=0`, or `retention_count=True`
- **THEN** initialization MUST raise `ValueError`

### Requirement: Non-fatal, exact-pattern retention pruning in rotating JSONL writers

Retention pruning in `_RotatingJsonlWriter` SHALL scan only files matching the exact `<prefix>-YYYYMMDD-HHMMSS(.N)?.jsonl` archive format, SHALL ignore per-entry `OSError`s during `stat()` (such as concurrent deletion or dangling symlinks), and MUST never allow pruning errors to set `_broken = True` or halt subsequent telemetry writes.

#### Scenario: Continuing telemetry writes when a matched file vanishes or a dangling symlink exists

- **WHEN** `_RotatingJsonlWriter._prune()` encounters a dangling symlink or a file deleted concurrently between directory scan and `stat()`
- **THEN** pruning skips the vanished entry without raising, `_broken` remains `False`, and subsequent `write_line()` calls succeed
