"""Optional OpenTelemetry helpers. Requires the `arlogi[otel]` extra."""

from arlogi.otel.decorator import traced
from arlogi.otel.exporters import RotatingJsonlSpanExporter

__all__ = ["RotatingJsonlSpanExporter", "traced"]
