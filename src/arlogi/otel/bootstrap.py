"""Provider bootstrap and log correlation for host applications."""

import functools
import inspect
import logging
import socket
import threading
import types
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

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


def _validate_netloc_port(parsed: Any, endpoint: str) -> None:
    """Reject dangling empty ports and out-of-range ports including port 0."""
    hostport = parsed.netloc.rsplit("@", 1)[-1]
    if hostport.startswith("["):
        if "]:" in hostport and not hostport.rsplit("]:", 1)[1]:
            raise ValueError(f"Invalid OTLP endpoint: {endpoint!r}")
    elif ":" in hostport and not hostport.rsplit(":", 1)[1]:
        raise ValueError(f"Invalid OTLP endpoint: {endpoint!r}")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError(f"Invalid OTLP endpoint: {endpoint!r}") from exc
    if port is not None and port < 1:
        raise ValueError(f"Invalid OTLP endpoint: {endpoint!r}")


def _validate_otlp_endpoint(endpoint: str) -> str:
    """Validate an OTLP HTTP endpoint before it is handed to an exporter.

    Args:
        endpoint: OTLP endpoint base URL (without scheme prefix handling assumed)

    Returns:
        The endpoint with trailing slash stripped

    Raises:
        ValueError: If the endpoint does not use http/https or has no host
    """
    if not isinstance(endpoint, str) or not endpoint:
        raise ValueError(f"Invalid OTLP endpoint: {endpoint!r}")
    if any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 or ch in "?#;" for ch in endpoint):
        raise ValueError(f"Invalid OTLP endpoint: {endpoint!r}")

    parsed = urlparse(endpoint)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError(f"Invalid OTLP endpoint: {endpoint!r}")
    if parsed.params or parsed.query or parsed.fragment:
        raise ValueError(f"Invalid OTLP endpoint: {endpoint!r}")
    _validate_netloc_port(parsed, endpoint)
    return endpoint.rstrip("/")


def _clear_global_tracer_provider() -> None:
    """Release OpenTelemetry's process-global TracerProvider slot.

    ``trace.set_tracer_provider()`` is a set-once API: without releasing the slot a
    ``setup_tracing()`` call after a shutdown would build a live provider that
    ``trace.get_tracer()`` never routes to, silently dropping every span.
    """
    try:
        from opentelemetry.util._once import Once

        if not (hasattr(trace, "_TRACER_PROVIDER_SET_ONCE") and hasattr(trace, "_TRACER_PROVIDER")):
            logger.warning("could not release the global TracerProvider; re-initialisation may be ignored")
            return
        trace._TRACER_PROVIDER_SET_ONCE = Once()
        trace._TRACER_PROVIDER = None
    except Exception:  # pragma: no cover - upstream internals moved
        logger.warning("could not release the global TracerProvider; re-initialisation may be ignored")


def _reset_proxy_meters_locked(proxy: Any) -> None:
    """Reset cached real meters and instruments on proxy meters under proxy._lock."""
    for meter in getattr(proxy, "_meters", ()):
        meter_lock = getattr(meter, "_lock", None)
        if meter_lock is None or not hasattr(meter, "_real_meter"):
            continue
        with meter_lock:
            meter._real_meter = None
            for inst in getattr(meter, "_instruments", ()):
                if hasattr(inst, "_real_instrument"):
                    inst._real_instrument = None


def _clear_global_meter_provider() -> None:
    """Release OpenTelemetry's process-global MeterProvider slot (see above)."""
    try:
        from opentelemetry.util._once import Once

        internal = getattr(metrics, "_internal", None)
        if internal is None or not (
            hasattr(internal, "_METER_PROVIDER_SET_ONCE") and hasattr(internal, "_METER_PROVIDER")
        ):
            logger.warning("could not release the global MeterProvider; re-initialisation may be ignored")
            return
        internal._METER_PROVIDER_SET_ONCE = Once()
        internal._METER_PROVIDER = None

        proxy = getattr(internal, "_PROXY_METER_PROVIDER", None)
        proxy_lock = getattr(proxy, "_lock", None)
        if proxy is None or proxy_lock is None or not hasattr(proxy, "_real_meter_provider"):
            logger.warning("could not release the global MeterProvider; re-initialisation may be ignored")
        else:
            with proxy_lock:
                proxy._real_meter_provider = None
                _reset_proxy_meters_locked(proxy)
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

        validated_otlp = (
            _validate_otlp_endpoint(otlp_endpoint) if otlp_endpoint is not None and otlp_endpoint != "" else None
        )
        file_exporter = RotatingJsonlSpanExporter(
            file_dir, prefix=file_prefix, rotate_hours=rotate_hours, retention_count=retention_count
        )
        otlp_exporter: Any = None
        if validated_otlp is not None:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

            otlp_exporter = OTLPSpanExporter(endpoint=f"{validated_otlp}/v1/traces", timeout=otlp_timeout)

        provider = TracerProvider(resource=_build_resource(service_name, service_version))
        try:
            provider.add_span_processor(BatchSpanProcessor(file_exporter))
            if otlp_exporter is not None:
                provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            trace.set_tracer_provider(provider)
        except Exception:
            provider.shutdown()
            raise

        if trace.get_tracer_provider() is not provider:
            provider.shutdown()
            logger.warning("An external global TracerProvider is already registered; not replacing it")
            return trace.get_tracer_provider()  # type: ignore[return-value]

        _tracer_provider = provider
        return provider


def shutdown_tracing() -> None:
    """Shut down and unregister the global TracerProvider.

    A no-op when tracing was never set up, so it is safe to call unconditionally
    (and repeatedly) from host-application cleanup paths. Cached and global
    provider state is always cleared even if ``provider.shutdown()`` raises,
    so :func:`setup_tracing` can still build a fresh, working provider.
    """
    global _tracer_provider
    with _lock:
        provider = _tracer_provider
        if provider is None:
            return
        try:
            provider.shutdown()
        finally:
            _tracer_provider = None
            _clear_global_tracer_provider()


def _child_factories(node: Any) -> list[Any]:
    """Collect wrapped callables reachable from a LogRecordFactory node."""
    children: list[Any] = []
    for attr in ("_arlogi_prev_factory", "__wrapped__"):
        child = inspect.getattr_static(node, attr, None)
        if child is not None:
            children.append(child)
    if isinstance(node, functools.partial):
        children.append(node.func)
        children.extend(arg for arg in node.args if callable(arg))
        if node.keywords:
            children.extend(val for val in node.keywords.values() if callable(val))
    if isinstance(node, types.FunctionType):
        for cell in node.__closure__ or ():
            try:
                val = cell.cell_contents
            except ValueError:
                continue
            if callable(val):
                children.append(val)
    return children


def _has_arlogi_correlation(factory: Any) -> bool:
    """Traverse chained LogRecordFactory wrappers to detect prior correlation."""
    stack: list[Any] = [factory]
    visited: set[int] = set()
    while stack:
        node = stack.pop()
        if node is None or id(node) in visited:
            continue
        visited.add(id(node))
        try:
            if inspect.getattr_static(node, "_arlogi_otel_correlation", False) is True:
                return True
            stack.extend(_child_factories(node))
        except Exception:
            continue
    return False


def install_log_correlation() -> None:
    """Stamp trace_id/span_id (hex) onto LogRecords while a span is active.

    Implemented via the process-global LogRecord factory (not a Filter) so it
    survives handler reconfiguration by the host application.
    """
    with _lock:
        current = logging.getLogRecordFactory()
        if _has_arlogi_correlation(current):
            return

        def factory(*args: object, **kwargs: object) -> logging.LogRecord:
            record = current(*args, **kwargs)  # type: ignore[arg-type]
            context = trace.get_current_span().get_span_context()
            if context.is_valid:
                record.trace_id = format(context.trace_id, "032x")
                record.span_id = format(context.span_id, "016x")
            return record

        factory._arlogi_otel_correlation = True  # type: ignore[attr-defined]
        factory._arlogi_prev_factory = current  # type: ignore[attr-defined]
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

        validated_otlp = (
            _validate_otlp_endpoint(otlp_endpoint) if otlp_endpoint is not None and otlp_endpoint != "" else None
        )
        file_exporter = RotatingJsonlMetricExporter(
            file_dir, prefix=file_prefix, rotate_hours=rotate_hours, retention_count=retention_count
        )
        otlp_exporter: Any = None
        if validated_otlp is not None:
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

            otlp_exporter = OTLPMetricExporter(endpoint=f"{validated_otlp}/v1/metrics", timeout=otlp_timeout)

        readers: list[Any] = []
        provider: MeterProvider | None = None
        try:
            readers.append(PeriodicExportingMetricReader(file_exporter, export_interval_millis=export_interval_millis))
            if otlp_exporter is not None:
                readers.append(
                    PeriodicExportingMetricReader(otlp_exporter, export_interval_millis=export_interval_millis)
                )
            provider = MeterProvider(resource=_build_resource(service_name, service_version), metric_readers=readers)
            metrics.set_meter_provider(provider)
        except Exception:
            if provider is not None:
                provider.shutdown()
            else:
                for reader in readers:
                    reader.shutdown()
            raise

        if metrics.get_meter_provider() is not provider:
            provider.shutdown()
            logger.warning("An external global MeterProvider is already registered; not replacing it")
            return metrics.get_meter_provider()  # type: ignore[return-value]

        _meter_provider = provider
        return provider


def shutdown_metrics() -> None:
    """Shut down and unregister the global MeterProvider.

    A no-op when metrics were never set up, so it is safe to call unconditionally
    (and repeatedly) from host-application cleanup paths. Cached and global
    provider state is always cleared even if ``provider.shutdown()`` raises,
    so :func:`setup_metrics` can still build a fresh, working provider.
    """
    global _meter_provider
    with _lock:
        provider = _meter_provider
        if provider is None:
            return
        try:
            provider.shutdown()
        finally:
            _meter_provider = None
            _clear_global_meter_provider()
