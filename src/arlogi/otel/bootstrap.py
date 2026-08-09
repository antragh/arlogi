"""Provider bootstrap and log correlation for host applications."""

import logging
import socket
import threading
from pathlib import Path

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from arlogi.otel.exporters import RotatingJsonlMetricExporter, RotatingJsonlSpanExporter

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_tracer_provider: TracerProvider | None = None
_meter_provider: MeterProvider | None = None


def _clear_global_tracer_provider() -> None:
    """Release OpenTelemetry's process-global TracerProvider slot.

    ``trace.set_tracer_provider()`` is a set-once API: without releasing the slot a
    ``setup_tracing()`` call after a shutdown would build a live provider that
    ``trace.get_tracer()`` never routes to, silently dropping every span.
    """
    try:
        from opentelemetry.util._once import Once

        trace._TRACER_PROVIDER_SET_ONCE = Once()
        trace._TRACER_PROVIDER = None
    except Exception:  # pragma: no cover - upstream internals moved
        logger.warning("could not release the global TracerProvider; re-initialisation may be ignored")


def _clear_global_meter_provider() -> None:
    """Release OpenTelemetry's process-global MeterProvider slot (see above)."""
    try:
        from opentelemetry.util._once import Once

        metrics._internal._METER_PROVIDER_SET_ONCE = Once()
        metrics._internal._METER_PROVIDER = None
    except Exception:  # pragma: no cover - upstream internals moved
        logger.warning("could not release the global MeterProvider; re-initialisation may be ignored")


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
    otlp_timeout: int = 5,
) -> TracerProvider:
    """Create and register the global TracerProvider. Idempotent.

    Call :func:`shutdown_tracing` before calling this again if the host
    application needs to tear the pipeline down and re-initialise it.

    Args:
        otlp_timeout: Per-export timeout in seconds for the OTLP exporter. Keeps an
            unreachable collector from stalling shutdown with retry backoff.
    """
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
                BatchSpanProcessor(
                    OTLPSpanExporter(endpoint=f"{otlp_endpoint.rstrip('/')}/v1/traces", timeout=otlp_timeout)
                )
            )
        trace.set_tracer_provider(provider)
        _tracer_provider = provider
        return provider


def shutdown_tracing() -> None:
    """Shut down and unregister the global TracerProvider.

    A no-op when tracing was never set up, so it is safe to call unconditionally
    (and repeatedly) from host-application cleanup paths. After this returns,
    :func:`setup_tracing` builds a fresh, working provider.
    """
    global _tracer_provider
    with _lock:
        if _tracer_provider is None:
            return
        _tracer_provider.shutdown()
        _tracer_provider = None
        _clear_global_tracer_provider()


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


def setup_metrics(
    service_name: str,
    service_version: str | None = None,
    *,
    file_dir: str | Path,
    file_prefix: str = "metrics",
    rotate_hours: int = 24,
    retention_count: int = 20,
    otlp_endpoint: str | None = None,
    otlp_timeout: int = 5,
    export_interval_millis: int = 60_000,
) -> MeterProvider:
    """Create and register the global MeterProvider. Idempotent.

    Call :func:`shutdown_metrics` before calling this again if the host
    application needs to tear the pipeline down and re-initialise it.

    Args:
        otlp_timeout: Per-export timeout in seconds for the OTLP exporter. Keeps an
            unreachable collector from stalling shutdown with retry backoff.
    """
    global _meter_provider
    with _lock:
        if _meter_provider is not None:
            logger.warning("setup_metrics() called more than once; keeping existing provider")
            return _meter_provider

        readers = [
            PeriodicExportingMetricReader(
                RotatingJsonlMetricExporter(
                    file_dir, prefix=file_prefix, rotate_hours=rotate_hours, retention_count=retention_count
                ),
                export_interval_millis=export_interval_millis,
            )
        ]
        if otlp_endpoint:
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

            readers.append(
                PeriodicExportingMetricReader(
                    OTLPMetricExporter(endpoint=f"{otlp_endpoint.rstrip('/')}/v1/metrics", timeout=otlp_timeout),
                    export_interval_millis=export_interval_millis,
                )
            )
        provider = MeterProvider(resource=_build_resource(service_name, service_version), metric_readers=readers)
        metrics.set_meter_provider(provider)
        _meter_provider = provider
        return provider


def shutdown_metrics() -> None:
    """Shut down and unregister the global MeterProvider.

    A no-op when metrics were never set up, so it is safe to call unconditionally
    (and repeatedly) from host-application cleanup paths. After this returns,
    :func:`setup_metrics` builds a fresh, working provider.
    """
    global _meter_provider
    with _lock:
        if _meter_provider is None:
            return
        _meter_provider.shutdown()
        _meter_provider = None
        _clear_global_meter_provider()
