# Tasks

## 1. Configuration & Validation

- [x] 1.1 In `src/arlogi/config.py`, define `SyslogFormat = Literal["text", "json"]`, `VALID_SYSLOG_FORMATS: frozenset[str] = frozenset({"text", "json"})`, and `validate_syslog_format(value: Any) -> SyslogFormat` raising `ValueError` for any value other than exact lowercase `"text"` or `"json"`.
- [x] 1.2 Add `syslog_format: SyslogFormat = "text"` after `syslog_address` on `LoggingConfig` and validate it eagerly in `LoggingConfig.__post_init__` (even when `use_syslog=False`).
- [x] 1.3 In `src/arlogi/config_builder.py`, track `self._syslog_format: SyslogFormat = "text"` in `__init__`, add `syslog_format: SyslogFormat = "text"` to `with_syslog(address="/dev/log", syslog_format="text")`, and forward `syslog_format=self._syslog_format` in `build()`.

## 2. Syslog JSON Formatter, Handler & HandlerFactory

- [x] 2.1 In `src/arlogi/handlers.py`, implement `SyslogJSONFormatter(JSONFormatter)` returning `f"{record.name}[{record.process}]: {super().format(record)}"` and add `_build_syslog_formatter(syslog_format: SyslogFormat) -> logging.Formatter`.
- [x] 2.2 Update `ArlogiSyslogHandler.__init__` in `src/arlogi/handlers.py` to accept `syslog_format: SyslogFormat = "text"`, call `validate_syslog_format(syslog_format)` before checking `/dev/log` or calling `super().__init__()`, store `self.syslog_format`, and attach `_build_syslog_formatter(self.syslog_format)` on primary, UDP `("localhost", 514)` fallback, and degraded `_failed = True` branches while keeping `C901 <= 10`.
- [x] 2.3 Update `HandlerFactory.create_syslog(config)` in `src/arlogi/handler_factory.py` to pass `syslog_format=config.syslog_format` to `ArlogiSyslogHandler`.

## 3. Factory & Public Entrypoints

- [x] 3.1 In `src/arlogi/factory.py`, add keyword-only `syslog_format: SyslogFormat | _Unset = _UNSET` to `LoggerFactory.setup()` and `setup_logging()`, adding `"syslog_format": syslog_format` to `raw_params` so combining `config=` with `syslog_format=` raises `ValueError`.
- [x] 3.2 Add trailing `syslog_format: SyslogFormat = "text"` to `LoggerFactory.get_syslog_logger()` and `get_syslog_logger()` in `src/arlogi/factory.py` and forward it to `ArlogiSyslogHandler(address=address, syslog_format=syslog_format)` before detaching existing handlers.

## 4. Unit Tests

- [x] 4.1 Add tests covering `LoggingConfig(syslog_format=...)` defaults, eager validation (invalid strings, wrong case `"JSON"`, `"jsonl"`, `None`, `True`, unhashable list), `LoggingConfigBuilder.with_syslog(..., syslog_format="json")` parity, and `setup_logging(config=..., syslog_format=...)` / `LoggerFactory.setup(config=..., syslog_format=...)` conflict `ValueError`.
- [x] 4.2 Add tests for `SyslogJSONFormatter` and `ArlogiSyslogHandler` verifying `"text"` vs `"json"` formatting (`<name>[<pid>]: <json>`), single-line output on multiline messages/tracebacks, canonical envelope key protection with nested `"extra"`, custom kwargs, `trace_id`/`span_id` correlation fields, and resilient fallback JSON when `__str__` raises.
- [x] 4.3 Add tests for `ArlogiSyslogHandler` pre-socket validation (invalid `syslog_format` raises `ValueError` for `/dev/log` without opening sockets or silently degrading), formatter preservation across `/dev/log` → `("localhost", 514)` fallback and `_failed` states, `HandlerFactory.create_syslog()` forwarding, and `get_syslog_logger(..., syslog_format="json")` + atomic preservation of existing handlers on invalid `syslog_format` reconfiguration.

## 5. Documentation Updates

- [x] 5.1 Document `syslog_format` (`"text"` default, `"json"` `<name>[<pid>]: {...}`) and `SyslogJSONFormatter` (plus TCP/Unix socket guidance for large payloads) across `README.md`, `docs/API_REFERENCE.md`, `docs/CONFIGURATION_GUIDE.md`, `docs/USER_GUIDE.md`, and `docs/ARCHITECTURE.md`.

## 6. Verification

- [x] 6.1 Run `uv run --no-sync ruff check src/ tests/` and `uv run --no-sync ruff format --check src/ tests/`.
- [x] 6.2 Run `uv run --no-sync pytest` and `uv run --isolated --frozen --no-dev --group test pytest`.
- [x] 6.3 Run `uv run --no-sync mkdocs build --strict`.
- [x] 6.4 Run `openspec validate add-syslog-json-format --strict`.
