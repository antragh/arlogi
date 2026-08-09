"""Provider bootstrap and log correlation for host applications."""

import logging
import socket
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from arlogi.otel.exporters import RotatingJsonlSpanExporter

if TYPE_CHECKING:
    from opentelemetry.sdk.metrics import MeterProvider

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_tracer_provider: TracerProvider | None = None
_meter_provider: "MeterProvider | None" = None


def _build_resource(service_name: str, service_version: str | None) -> Resource:
    attributes: dict[str, str] = {"service.name": service_name, "host.name": socket.gethostname()}
    if service_version:
        attributes["service.version"] = service_version
    return Resource.create(attributes)


def setup_tracing(
    service_name: str,
    service_version: str | None = None,
    *,
    file_dir: str | Path,
    file_prefix: str = "traces",
    rotate_hours: int = 24,
    retention_count: int = 20,
    otlp_endpoint: str | None = None,
) -> TracerProvider:
    """Create and register the global TracerProvider. Idempotent."""
    global _tracer_provider
    with _lock:
        if _tracer_provider is not None:
            logger.warning("setup_tracing() called more than once; keeping existing provider")
            return _tracer_provider

        provider = TracerProvider(resource=_build_resource(service_name, service_version))
        provider.add_span_processor(
            BatchSpanProcessor(
                RotatingJsonlSpanExporter(
                    file_dir, prefix=file_prefix, rotate_hours=rotate_hours, retention_count=retention_count
                )
            )
        )
        if otlp_endpoint:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

            provider.add_span_processor(
                BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{otlp_endpoint.rstrip('/')}/v1/traces"))
            )
        trace.set_tracer_provider(provider)
        _tracer_provider = provider
        return provider


def install_log_correlation() -> None:
    """Stamp trace_id/span_id (hex) onto LogRecords while a span is active.

    Implemented via the process-global LogRecord factory (not a Filter) so it
    survives handler reconfiguration by the host application.
    """
    with _lock:
        current = logging.getLogRecordFactory()
        if getattr(current, "_arlogi_otel_correlation", False):
            return

        def factory(*args: object, **kwargs: object) -> logging.LogRecord:
            record = current(*args, **kwargs)  # type: ignore[arg-type]
            context = trace.get_current_span().get_span_context()
            if context.is_valid:
                record.trace_id = format(context.trace_id, "032x")
                record.span_id = format(context.span_id, "016x")
            return record

        factory._arlogi_otel_correlation = True  # type: ignore[attr-defined]
        logging.setLogRecordFactory(factory)
