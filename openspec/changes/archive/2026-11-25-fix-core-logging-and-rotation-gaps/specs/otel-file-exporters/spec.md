# Spec Delta

## ADDED Requirements

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
