"""Optional OpenTelemetry helpers. Requires the `arlogi[otel]` extra."""

import importlib
from typing import Any

from arlogi.otel.decorator import set_trace_modules, traced

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

# decorator.py depends only on opentelemetry-api; bootstrap/exporters pull in
# opentelemetry-sdk. Importing them lazily keeps `import arlogi.otel.decorator`
# (or `arlogi.otel`) SDK-free for consumers who only installed the api.
_LAZY_MODULES = {
    "install_log_correlation": "arlogi.otel.bootstrap",
    "setup_metrics": "arlogi.otel.bootstrap",
    "setup_tracing": "arlogi.otel.bootstrap",
    "shutdown_metrics": "arlogi.otel.bootstrap",
    "shutdown_tracing": "arlogi.otel.bootstrap",
    "RotatingJsonlMetricExporter": "arlogi.otel.exporters",
    "RotatingJsonlSpanExporter": "arlogi.otel.exporters",
}


def __getattr__(name: str) -> Any:
    module_name = _LAZY_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(importlib.import_module(module_name), name)
