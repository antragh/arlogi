# Spec Delta: logging-configuration

## ADDED Requirements

### Requirement: Syslog format configuration and validation

The configuration system SHALL provide a `syslog_format` setting defaulting to `"text"` and accepting only exact lowercase `"text"` or `"json"`, SHALL validate it eagerly on configuration creation (even when `use_syslog=False`), SHALL expose it on `LoggingConfigBuilder.with_syslog()`, and SHALL support keyword-only `syslog_format` in `setup_logging()` and `LoggerFactory.setup()` with conflict detection when combined with `config=`.

#### Scenario: Default syslog_format parity between LoggingConfig and builder

- **WHEN** a caller constructs `LoggingConfig()` or `LoggingConfigBuilder().build()` without syslog format overrides
- **THEN** `config.syslog_format == "text"` and `LoggingConfigBuilder().build() == LoggingConfig()`

#### Scenario: Configuring JSON syslog output through builder and setup_logging

- **WHEN** a caller configures `LoggingConfigBuilder().with_syslog(address=("syslog.example.com", 514), syslog_format="json").build()` or calls `setup_logging(use_syslog=True, syslog_format="json")`
- **THEN** the resulting configuration has `use_syslog=True`, `syslog_address` as configured, and `syslog_format="json"`

#### Scenario: Rejecting invalid syslog_format values

- **WHEN** `LoggingConfig` is constructed with `syslog_format="jsonl"`, `"JSON"`, `None`, `True`, `123`, or `["json"]` (including when `use_syslog=False`)
- **THEN** construction MUST raise `ValueError`

#### Scenario: Rejecting simultaneous config object and syslog_format override

- **WHEN** a caller invokes `setup_logging(config=built_config, syslog_format="text")` or `LoggerFactory.setup(config=built_config, syslog_format="json")`
- **THEN** the call MUST raise `ValueError`
