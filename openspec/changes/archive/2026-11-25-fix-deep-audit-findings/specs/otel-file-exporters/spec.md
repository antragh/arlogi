# Spec Delta: otel-file-exporters

## ADDED Requirements

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
