# Design: Add Syslog JSON Format Support (`syslog_format`)

## Context

`ArlogiSyslogHandler` (`src/arlogi/handlers.py:709-788`) subclasses `logging.handlers.SysLogHandler` and currently attaches a hardcoded plain-text formatter in both its primary socket setup and its `/dev/log` → `("localhost", 514)` fallback branch (`logging.Formatter("%(name)s[%(process)d]: %(levelname)s: %(message)s")`). Meanwhile:

- `JSONFormatter` (`src/arlogi/handlers.py:249-368`) already implements canonical envelope key protection, nested `"extra"` collision routing, extra-field merging, OpenTelemetry `trace_id`/`span_id` inclusion (when `install_log_correlation()` is active on records), and non-raising fallback JSON serialization.
- `LoggingConfig` (`src/arlogi/config.py:14-82`) establishes the pattern for literal enum-like string options (`RotateSchedule`, `VALID_ROTATE_SCHEDULES`).
- `LoggerFactory.setup()` and `setup_logging()` (`src/arlogi/factory.py:197-261`, `514-564`) use `_Unset`/`_UNSET` sentinels to apply field defaults from `LoggingConfig` cleanly and to reject combining `config=` with any explicit keyword override.

## Goals / Non-Goals

### Goals

- Expose `syslog_format: Literal["text", "json"] = "text"` uniformly across `LoggingConfig`, `LoggingConfigBuilder.with_syslog()`, `HandlerFactory.create_syslog()`, `setup_logging()`, `LoggerFactory.setup()`, `get_syslog_logger()`, `LoggerFactory.get_syslog_logger()`, and `ArlogiSyslogHandler`.
- Emit RFC 3164-compatible single-line TAG+JSON output (`<name>[<pid>]: {...}`) in `"json"` mode so standard syslog receivers (`syslog-ng`, `rsyslog`, `systemd-journald`, `Promtail`/`Alloy`, `Vector`, `Fluent Bit`) parse `APP-NAME`/`PROCID` cleanly and pass pure JSON in `MSG` to JSON parsers.
- Reuse `JSONFormatter` serialization, envelope protection, correlation fields, and fallback error recovery without duplicating logic.
- Validate `syslog_format` eagerly in both `LoggingConfig.__post_init__` and `ArlogiSyslogHandler.__init__` before any socket check or allocation, avoiding swallowed exceptions or socket leaks.
- Keep cyclomatic complexity (`C901 <= 10`) within `.ruff.toml` bounds.

### Non-Goals

- Adding a headerless raw JSON mode (`json_raw`) or `@cee:` / RFC 5424 structured-data framing.
- Modifying `LoggingConfig.has_json_output` semantics (which continues to represent local JSON file/console output only).
- Changing `ArlogiSyslogHandler` fallback behavior beyond ensuring formatter consistency (fallback still applies only to default `/dev/log`).

## Decisions

### 1. Parameter Naming and Accepted Values (`"text"` | `"json"`, strictly lowercase)

Syslog ingestion systems (`syslog-ng` `json-parser()`, `rsyslog` `mmjsonparse`, `Vector` `parse_json`, `Fluent Bit` `json`, `Promtail`/`Alloy` `stage.json`, `Logstash`, `Splunk`) refer to single-event JSON syslog payloads as **`json`** (whereas `jsonl` denotes newline-delimited files).

- Define `SyslogFormat = Literal["text", "json"]` and `VALID_SYSLOG_FORMATS: frozenset[str] = frozenset({"text", "json"})` in `src/arlogi/config.py`.
- Require exact lowercase strings `"text"` or `"json"` (matching `RotateSchedule` strictness). Wrong case (`"JSON"`), synonyms (`"jsonl"`), `None`, booleans, integers, or unhashable types (such as lists/dicts) raise `ValueError`.

### 2. Wire Format (`<name>[<pid>]: <JSONFormatter output>`) via `SyslogJSONFormatter(JSONFormatter)`

When `syslog_format="json"`, standard Python `SysLogHandler` sends `<PRI>` followed by the formatted string. Standard RFC 3164 collectors expect `TAG[PID]: MSG`; emitting bare `{...}` directly after `<PRI>` causes RFC 3164 parsers to treat `{"timestamp":` as `APP-NAME`/`TAG`, breaking JSON parsing in `MSG`.

- Subclass `JSONFormatter` as `SyslogJSONFormatter` in `src/arlogi/handlers.py`:
  ```python
  class SyslogJSONFormatter(JSONFormatter):
      def format(self, record: logging.LogRecord) -> str:
          payload = super().format(record)
          return f"{record.name}[{record.process}]: {payload}"
  ```
- Because `super().format(record)` uses `json.dumps(log_data, default=str)` (without `indent`), newlines in `record.msg` or tracebacks are JSON-escaped (`\n`), ensuring single-line `MSG` output per record.
- Inheriting `JSONFormatter` gives syslog JSON logs identical canonical envelope key protection, nested `"extra"` collision routing, structured kwargs/correlation fields (`trace_id`/`span_id`), and non-raising fallback JSON serialization.
- Because `SyslogJSONFormatter` is still a `logging.Formatter`, advanced callers can still override formatting via `handler.setFormatter(...)`.

### 3. Shared Eager Validation Helper (`validate_syslog_format`)

- Add `validate_syslog_format(value: Any) -> SyslogFormat` in `src/arlogi/config.py`:
  ```python
  def validate_syslog_format(value: Any) -> SyslogFormat:
      if not isinstance(value, str) or value not in VALID_SYSLOG_FORMATS:
          valid = ", ".join(sorted(VALID_SYSLOG_FORMATS))
          raise ValueError(f"Invalid syslog_format: {value!r}. Valid values: {valid}")
      return value  # type: ignore[return-value]
  ```
- Call `validate_syslog_format(self.syslog_format)` in `LoggingConfig.__post_init__` eagerly even when `use_syslog=False` (consistent with eager `rotate_schedule` validation even when `json_file_name=None`).
- Call `validate_syslog_format(syslog_format)` at the very start of `ArlogiSyslogHandler.__init__` **before** checking `os.path.exists("/dev/log")` or calling `super().__init__(...)`. This ensures an invalid `syslog_format` with default `address="/dev/log"` raises `ValueError` immediately rather than being caught by the fallback `except Exception:` block or leaking a socket.

### 4. Consistent Formatter Attachment Across `ArlogiSyslogHandler` Branches

Extract a small module-level or static helper `_build_syslog_formatter(syslog_format: SyslogFormat) -> logging.Formatter` that returns `SyslogJSONFormatter()` for `"json"` and `logging.Formatter("%(name)s[%(process)d]: %(levelname)s: %(message)s")` for `"text"`.

- `ArlogiSyslogHandler.__init__` validates `syslog_format`, sets `self.syslog_format = validated_format`, builds `formatter = _build_syslog_formatter(validated_format)`, and calls `self.setFormatter(formatter)` in:
  1. Primary `super().__init__` success path
  2. `/dev/log` → `("localhost", 514)` fallback success path
  3. Degraded `self._failed = True` path (`logging.Handler.__init__(self)`)
- Extracting `_build_syslog_formatter` keeps `ArlogiSyslogHandler.__init__` cyclomatic complexity unchanged (`<= 10`) and guarantees `handler.formatter` is deterministically `SyslogJSONFormatter` vs `logging.Formatter` on any host (even without a running syslog daemon).

### 5. Public Signature Compatibility and Atomic Lifecycle

- `LoggingConfig`: add `syslog_format: SyslogFormat = "text"` immediately after `syslog_address`.
- `LoggingConfigBuilder`: track `self._syslog_format: SyslogFormat = "text"` in `__init__`, update `with_syslog(self, address: str | tuple[str, int] = "/dev/log", syslog_format: SyslogFormat = "text") -> "LoggingConfigBuilder"`, and pass `syslog_format=self._syslog_format` in `build()`. Default `LoggingConfigBuilder().build() == LoggingConfig()` remains preserved.
- `HandlerFactory.create_syslog(config)`: pass `ArlogiSyslogHandler(address=config.syslog_address, syslog_format=config.syslog_format)`.
- `LoggerFactory.setup(...)` and `setup_logging(...)`: add keyword-only `syslog_format: SyslogFormat | _Unset = _UNSET` (after `*`, alongside `json_file_base_dir`) and add `"syslog_format": syslog_format` to `raw_params`. Thus:
  - Existing positional calls are unaffected.
  - Passing `config=` together with `syslog_format=` (even `syslog_format="text"`) raises `ValueError`.
- `LoggerFactory.get_syslog_logger(...)` and `get_syslog_logger(...)`: add optional trailing `syslog_format: SyslogFormat = "text"` and pass `syslog_format=syslog_format` to `ArlogiSyslogHandler(address=address, syslog_format=syslog_format)` **before** replacing handlers on the dedicated logger, preserving existing handlers atomically if `syslog_format` is invalid.

## Risks / Trade-offs

- **UDP Datagram Size / MTU Truncation**: JSON records containing custom extras or multi-frame exception tracebacks can exceed traditional UDP syslog limits (~1 KB–2 KB depending on MTU/daemon). Mitigation: document recommending TCP (`socktype=socket.SOCK_STREAM`) or a local Unix socket (`/dev/log`) when shipping large JSON records via syslog.
- **Documentation Maintenance**: Adding a new parameter touches five guide/reference files; all examples will use valid Python matching runtime signatures and be covered by `uv run --no-sync mkdocs build --strict`.
