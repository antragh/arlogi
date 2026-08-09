"""Optional OpenTelemetry helpers. Requires the `arlogi[otel]` extra."""

from arlogi.otel.bootstrap import install_log_correlation, setup_tracing
from arlogi.otel.decorator import traced
from arlogi.otel.exporters import RotatingJsonlSpanExporter

__all__ = ["RotatingJsonlSpanExporter", "install_log_correlation", "setup_tracing", "traced"]
