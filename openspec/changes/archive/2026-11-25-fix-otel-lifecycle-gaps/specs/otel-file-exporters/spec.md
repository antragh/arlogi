# Spec Delta: otel-file-exporters

## ADDED Requirements

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
