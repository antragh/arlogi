"""Optional OpenTelemetry helpers. Requires the `arlogi[otel]` extra."""

from arlogi.otel.bootstrap import (
    install_log_correlation,
    setup_metrics,
    setup_tracing,
    shutdown_metrics,
    shutdown_tracing,
)
from arlogi.otel.decorator import set_trace_modules, traced
from arlogi.otel.exporters import RotatingJsonlMetricExporter, RotatingJsonlSpanExporter

__all__ = [
    "RotatingJsonlMetricExporter",
    "RotatingJsonlSpanExporter",
    "install_log_correlation",
    "set_trace_modules",
    "setup_metrics",
    "setup_tracing",
    "shutdown_metrics",
    "shutdown_tracing",
    "traced",
]
