# Spec Delta: logger-lifecycle

## ADDED Requirements

### Requirement: Dedicated syslog logger format selection

`get_syslog_logger()` and `LoggerFactory.get_syslog_logger()` SHALL accept `syslog_format: Literal["text", "json"] = "text"`, forward it to `ArlogiSyslogHandler`, and preserve atomic create-before-detach handler replacement so an invalid `syslog_format` fails without disturbing previously attached handlers.

#### Scenario: Dedicated JSON-formatted syslog logger emission

- **WHEN** a caller obtains `get_syslog_logger("security", syslog_format="json")` and logs a structured event with custom kwargs and `caller_depth`
- **THEN** the attached `ArlogiSyslogHandler` formats the emitted syslog payload via `SyslogJSONFormatter` as `arlogi.syslog.security[<pid>]: <json_payload>` containing the structured kwargs

#### Scenario: Preserving active dedicated syslog handler on invalid syslog_format

- **WHEN** `get_syslog_logger("security", syslog_format="text")` is active and a subsequent call `get_syslog_logger("security", syslog_format="invalid")` raises `ValueError`
- **THEN** the previously attached `ArlogiSyslogHandler` remains attached and open on `arlogi.syslog.security`
