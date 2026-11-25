## v0.611.25 (2026-11-25)

### Fix

- **core**: strictly confine JSON file paths within `json_file_base_dir`, fix elapsed-period archive naming, guard rotation I/O against `OSError`, make `JSONHandler.close()` lock-protected and idempotent, protect JSON envelope keys by nesting `extra` collisions, disable Rich markup by default in `ColoredConsoleHandler`, preserve caller `extra` mapping immutability, unify level parsing, and support `fatal()` / single-pass `exception()`
- **lifecycle**: perform atomic root handler replacement with rollback on factory setup failure, export `LoggingConfigBuilder`, fix `LoggerFactory.setup()` defaults and keyword-only options, detach dedicated JSON/syslog loggers safely under lock, and fix monkey-patched `trace()` `stacklevel`
- **otel**: bound prefix/retention validation and atomic `os.scandir()` pruning in rotating JSONL exporters, harden OTLP endpoint validation and lifecycle rollback, preserve external global providers, support full `send`/`throw`/`close` in `@traced` sync/async generators, and re-key `@traced` tracer cache per provider

### Docs & CI

- **ci,packaging**: add dedicated `ci.yml`, harden `publish.yml` and `deploy-docs.yml` permissions and tag/version verification, slim down source distributions (`sdist`), and split optional dependency groups (`test`, `docs`, `graph`, `dev`)
- **docs**: add `arlogi.otel` MkDocs API reference pages, sync `README.md`, `index.md`, `API_REFERENCE.md`, `ARCHITECTURE.md`, `CONFIGURATION_GUIDE.md`, `USER_GUIDE.md`, and `DEVELOPER_GUIDE.md` with current behavior and v0.611.25

## v0.611.3 (2026-10-02)

### Fix

- **deps**: graphifyy is no longer a runtime dependency

## v0.611.2 (2026-09-19)

### Fix

- **core,otel**: address audit findings 1-5 for thread safety and syslog fallback

## v0.611.1 (2026-08-11)

### Fix

- **ci**: bump pypa/gh-action-pypi-publish to v1.14.2

## v0.611.0 (2026-08-09)

### Feat

- **otel**: trace sync generators across their full iteration
- **otel**: trace async generators across their full iteration
- **otel**: static span attributes via @traced(attrs=...)
- **otel**: per-module span gating via set_trace_modules

### Fix

- **otel**: keep arlogi.otel.decorator import free of the OTEL SDK

## v0.610.0 (2026-08-09)

### Feat

- **otel**: bound OTLP export time with an otlp_timeout parameter
- **otel**: add shutdown_tracing()/shutdown_metrics() for clean re-init

## v0.609.0 (2026-08-09)

### Feat

- arlogi.otel metrics pipeline (RotatingJsonlMetricExporter, setup_metrics)
- arlogi.otel setup_tracing bootstrap and log correlation
- arlogi.otel @traced decorator (sync + async)
- arlogi.otel package with RotatingJsonlSpanExporter ([otel] extra)

### Fix

- make install_log_correlation atomic under the module lock

## v0.608.0 (2026-07-25)

### Feat

- configure commitizen and add GitHub Actions release workflow for PyPI
- add logo
- added logo
- Migrate global logging configuration from `setup_logging()` to `LoggingConfig` and `LoggerFactory._apply_configuration()` pattern, updating examples and documentation accordingly.
- Add comprehensive logging library with documentation and features

### Fix

- handler.py for log rotation on Windows
- some docs
