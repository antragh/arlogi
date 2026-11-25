# Proposal: Add Syslog JSON Format Support (`syslog_format`)

## Why

`ArlogiSyslogHandler` currently hardcodes a plain-text formatter (`%(name)s[%(process)d]: %(levelname)s: %(message)s`). Applications that forward logs through syslog to structured log collectors and SIEM pipelines (`syslog-ng` with `json-parser()`, `rsyslog`, `systemd-journald`, Grafana `Promtail`/`Alloy`, `Vector`, `Fluent Bit`) cannot configure `arlogi` to emit structured JSON payloads over syslog with custom `extra`/keyword fields, protected envelope keys, and OpenTelemetry correlation IDs (`trace_id`, `span_id`).

## What Changes

- Add `SyslogFormat = Literal["text", "json"]`, `VALID_SYSLOG_FORMATS = frozenset({"text", "json"})`, and a shared validation helper `validate_syslog_format()` in `src/arlogi/config.py`.
- Add `syslog_format: SyslogFormat = "text"` to `LoggingConfig` and validate it eagerly in `LoggingConfig.__post_init__`.
- Add `SyslogJSONFormatter(JSONFormatter)` in `src/arlogi/handlers.py` producing RFC 3164 TAG+JSON single-line output (`<record.name>[<record.process>]: <json_payload>`), inheriting canonical envelope key protection, extra-field merging, OpenTelemetry `trace_id`/`span_id` correlation fields, and resilient fallback JSON serialization from `JSONFormatter`.
- Add `syslog_format: SyslogFormat = "text"` parameter (and `self.syslog_format` attribute) to `ArlogiSyslogHandler.__init__`, validated before opening any socket and applied consistently across primary initialization, `/dev/log` → `("localhost", 514)` fallback, and degraded `_failed` states.
- Propagate `syslog_format` across all configuration and factory entrypoints:
  - `LoggingConfigBuilder.with_syslog(address="/dev/log", syslog_format="text")`
  - `HandlerFactory.create_syslog(config)`
  - Keyword-only `syslog_format: SyslogFormat | _Unset = _UNSET` in `LoggerFactory.setup(...)` and `setup_logging(...)` (rejecting combinations with `config=...`)
  - `LoggerFactory.get_syslog_logger(..., syslog_format="text")` and `get_syslog_logger(..., syslog_format="text")`
- Add comprehensive unit tests covering configuration, builder, handler fallback, formatting, envelope protection, OpenTelemetry correlation fields, and atomic dedicated-logger reconfiguration.
- Update published documentation (`README.md`, `docs/API_REFERENCE.md`, `docs/CONFIGURATION_GUIDE.md`, `docs/USER_GUIDE.md`, `docs/ARCHITECTURE.md`) to document `syslog_format` and `SyslogJSONFormatter`.

## Capabilities

### Modified Capabilities (Additive Delta Specs)

- `logging-configuration`: Add `syslog_format` field validation, builder support, and `setup_logging()`/`LoggerFactory.setup()` override checks.
- `json-handlers-and-rotation`: Add `SyslogJSONFormatter`, `ArlogiSyslogHandler(syslog_format=...)`, eager pre-socket validation, fallback formatter consistency, and `HandlerFactory.create_syslog()` propagation.
- `logger-lifecycle`: Add `syslog_format` parameter to `get_syslog_logger()` / `LoggerFactory.get_syslog_logger()` with atomic handler preservation on validation failure.
- `documentation-sync`: Document `syslog_format` (`"text"` and `"json"`), `SyslogJSONFormatter`, and UDP payload sizing guidance in user-facing guides and API reference.

## Impact

- Fully backward compatible: `syslog_format` defaults to `"text"`, preserving existing syslog wire formatting.
- Keyword-only `syslog_format` addition to `setup_logging()` and `LoggerFactory.setup()` preserves all positional callers.
- Trailing optional `syslog_format="text"` on `LoggingConfigBuilder.with_syslog()`, `ArlogiSyslogHandler.__init__()`, `LoggerFactory.get_syslog_logger()`, and `get_syslog_logger()` preserves existing calls without breaking changes.
- Zero new runtime or optional dependencies.
