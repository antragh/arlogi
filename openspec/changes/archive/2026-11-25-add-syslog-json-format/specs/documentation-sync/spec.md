# Spec Delta: documentation-sync

## ADDED Requirements

### Requirement: Syslog format documentation

Published documentation (`README.md`, `docs/API_REFERENCE.md`, `docs/CONFIGURATION_GUIDE.md`, `docs/USER_GUIDE.md`, and `docs/ARCHITECTURE.md`) SHALL document `syslog_format` (`"text"` default and `"json"` `<name>[<pid>]: {...}` output) and `SyslogJSONFormatter`, including TCP/Unix socket guidance for large payloads.

#### Scenario: Guides and API reference document syslog_format accurately

- **WHEN** a reader consults `README.md`, `docs/API_REFERENCE.md`, `docs/CONFIGURATION_GUIDE.md`, `docs/USER_GUIDE.md`, and `docs/ARCHITECTURE.md` for syslog JSON configuration
- **THEN** every documented signature, valid `syslog_format` literal (`"text"` / `"json"`), and wire format example (`<name>[<pid>]: {...}`) matches the runtime implementation and `uv run mkdocs build --strict` exits 0
