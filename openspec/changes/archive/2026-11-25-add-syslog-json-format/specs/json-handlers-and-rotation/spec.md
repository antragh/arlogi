# Spec Delta: json-handlers-and-rotation

## ADDED Requirements

### Requirement: Structured JSON formatting for syslog handler

`ArlogiSyslogHandler` SHALL accept `syslog_format` (`"text"` or `"json"`, default `"text"`), validate it before opening any socket, store `self.syslog_format`, and attach either the standard text formatter or `SyslogJSONFormatter(JSONFormatter)` (`<name>[<pid>]: <single-line JSON>`) across primary, UDP fallback, and `_failed` paths; `HandlerFactory.create_syslog(config)` SHALL forward `config.syslog_format`.

#### Scenario: Formatting records in text and json syslog modes

- **WHEN** a `LogRecord` with `user_id=42` and colliding attribute `level="FAKE"` (plus optional `trace_id`/`span_id`) is formatted by `ArlogiSyslogHandler(syslog_format="text")` vs `ArlogiSyslogHandler(syslog_format="json")`
- **THEN** `"text"` emits `"%(name)s[%(process)d]: %(levelname)s: %(message)s"`, while `"json"` uses `SyslogJSONFormatter` emitting `<record.name>[<record.process>]: <json_payload>` where `<json_payload>` is valid single-line JSON preserving canonical envelope keys, top-level custom fields, nested `"extra"` collisions, and correlation IDs

#### Scenario: Escaping multiline messages and tracebacks to single-line syslog JSON

- **WHEN** `SyslogJSONFormatter.format()` formats a record whose message or `exc_info` traceback contains newline characters
- **THEN** the resulting formatted string contains no literal `\n` line breaks so syslog frames remain single-line events

#### Scenario: Failing fast on invalid syslog_format without opening or leaking sockets

- **WHEN** `ArlogiSyslogHandler(address="/dev/log", syslog_format="jsonl")` or `ArlogiSyslogHandler(address=("localhost", 514), syslog_format="JSON")` is instantiated
- **THEN** `ValueError` is raised immediately before creating any socket or falling back silently

#### Scenario: Preserving SyslogJSONFormatter across fallback and degraded states

- **WHEN** `ArlogiSyslogHandler(address="/dev/log", syslog_format="json")` falls back to UDP `("localhost", 514)` or enters `_failed = True` when both fail
- **THEN** `handler.syslog_format == "json"` and `isinstance(handler.formatter, SyslogJSONFormatter)` holds in all initialization outcomes

#### Scenario: Resilient fallback JSON on unserializable field in syslog JSON mode

- **WHEN** a custom structured attribute raises in `__str__` while formatting with `SyslogJSONFormatter`
- **THEN** formatting succeeds and emits `<record.name>[<record.process>]: <fallback_json>` containing canonical metadata and an `"error"` field without raising

#### Scenario: Forwarding syslog_format through HandlerFactory

- **WHEN** `HandlerFactory.create_syslog(LoggingConfig(use_syslog=True, syslog_format="json"))` is called
- **THEN** the returned `ArlogiSyslogHandler` has `syslog_format == "json"` and uses `SyslogJSONFormatter`
