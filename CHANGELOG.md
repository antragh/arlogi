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
