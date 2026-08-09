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
