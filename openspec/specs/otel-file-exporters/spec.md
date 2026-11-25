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

### Requirement: Deterministic regular-file-only retention in rotating JSONL writers

Retention pruning in `_RotatingJsonlWriter` SHALL follow the same rules as JSON file handler pruning: it SHALL count and delete only regular files (never directories or symlinks, evaluated without following symlinks), SHALL exclude the active file by resolved path, and SHALL order archives newest-first by nanosecond modification time, then by archive timestamp, then by numeric collision suffix (unsuffixed counts as `0`).

#### Scenario: Matching directory does not evict a real telemetry archive

- **WHEN** a telemetry directory contains a real archive `traces-20200101-000000.jsonl` and a newer directory named `traces-20200102-000000.jsonl/`, and a writer with `retention_count=2` opens a new file
- **THEN** `traces-20200101-000000.jsonl` is retained alongside the active file and the directory is left untouched

#### Scenario: Equal modification times keep the newer telemetry archive

- **WHEN** archives `traces-20200101-000000.jsonl` and `traces-20200101-000001.jsonl` share an identical `st_mtime_ns` and a writer with `retention_count=2` opens a new active file
- **THEN** `traces-20200101-000001.jsonl` is retained and `traces-20200101-000000.jsonl` is deleted regardless of directory enumeration order

#### Scenario: Pruning stays non-fatal and needs no OpenTelemetry for the core helper

- **WHEN** pruning encounters `OSError` on `stat()` or unlink, or the core package is imported in an environment without the `otel` extra
- **THEN** telemetry writes continue with `_broken` remaining `False`, and importing the core package never imports `opentelemetry`

### Requirement: Exclusive, symlink-safe creation of rotating JSONL files

When `_RotatingJsonlWriter` starts a new `<prefix>-YYYYMMDD-HHMMSS(.N)?.jsonl` file, it SHALL create it atomically and exclusively inside the configured directory without following symlinks, advancing the `.N` suffix past any existing entry (regular file, live or dangling symlink, or directory), and MUST never append to a pre-existing entry.

#### Scenario: Dangling symlink pointing outside the telemetry directory is not followed

- **WHEN** the telemetry directory contains a dangling symlink named exactly like the next file to be created, pointing to a non-existent path outside that directory, and `write_line()` is called
- **THEN** `write_line()` returns `True`, the symlink target is not created, the line is written to a regular file named `<prefix>-<stamp>.1.jsonl` inside the telemetry directory, and the symlink is left untouched

#### Scenario: Dangling symlink with a missing parent directory does not disable the writer

- **WHEN** the next file name is occupied by a dangling symlink whose target's parent directory does not exist, and `write_line()` is called
- **THEN** `write_line()` returns `True`, `_broken` remains `False`, and the line is written to the next free `.N` suffix

#### Scenario: Live symlink and pre-existing regular file are skipped

- **WHEN** the next file name is occupied by a live symlink to a file outside the directory, or by a pre-existing regular file with content
- **THEN** neither the symlink target nor the existing file is modified, and the writer creates the next free `.N` suffix file

#### Scenario: Two writers starting in the same second write to distinct files

- **WHEN** two independent `_RotatingJsonlWriter` instances with the same directory and prefix open their first file with the same timestamp
- **THEN** each writes to a different file, and every line written by each writer appears exactly once in its own file

#### Scenario: Exhausting collision suffixes degrades non-fatally

- **WHEN** no free `.N` suffix can be claimed within the writer's bounded attempt limit
- **THEN** `write_line()` returns `False` without raising, a single warning is logged, and `_broken` is set to `True`

### Requirement: Closed-state guard and immediate stream release on I/O failure in rotating JSONL writers

`_RotatingJsonlWriter.close()` SHALL set a closed flag and clear `_active_path` under lock while closing `_stream`, so post-shutdown `write_line()` calls return `False` without opening files or leaking descriptors (while preserving self-healing if `_stream` is closed externally without `close()`). On write/flush `OSError`, `write_line()` SHALL close and clear `_stream` under lock when setting `_broken`.

#### Scenario: Post-shutdown span or metric export returns FAILURE without reopening files

- **WHEN** `RotatingJsonlSpanExporter.shutdown()` or `RotatingJsonlMetricExporter.shutdown()` closes the writer and a subsequent `export()` runs (for example an in-flight `SimpleSpanProcessor` span ending or `PeriodicExportingMetricReader.collect()`)
- **THEN** `write_line()` returns `False`, the exporter returns `FAILURE`, no new `.jsonl` file is created or pruned, and no file descriptor is leaked

#### Scenario: External stream closure still self-heals when writer was not closed

- **WHEN** `writer._stream.close()` is called externally without calling `writer.close()` and `write_line()` is invoked
- **THEN** `write_line()` opens a new file and returns `True`

#### Scenario: Write or flush OSError immediately closes the dead stream

- **WHEN** `self._stream.write()` or `self._stream.flush()` raises `OSError` inside `write_line()`
- **THEN** `_broken` is set to `True`, `self._stream` is best-effort closed and reset to `None` under lock, and no dead file descriptor remains open until `shutdown()`
