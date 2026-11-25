"""Shared pytest fixtures. OTEL fixtures are inert when the [otel] extra is absent."""

import logging

import pytest


@pytest.fixture
def reset_otel_globals():
    """Reset OpenTelemetry global provider state after a test that sets it."""
    orig_factory = logging.getLogRecordFactory()
    yield
    try:
        from opentelemetry import metrics, trace
        from opentelemetry.util._once import Once

        from arlogi.otel import set_trace_modules, shutdown_metrics, shutdown_tracing
    except ImportError:
        return  # [otel] extra absent (partial install); nothing to reset

    try:
        set_trace_modules(None)
        shutdown_tracing()
        shutdown_metrics()

        for existing in (getattr(trace, "_TRACER_PROVIDER", None), getattr(metrics._internal, "_METER_PROVIDER", None)):
            if existing is not None and hasattr(existing, "shutdown"):
                try:
                    existing.shutdown()
                except Exception:
                    pass

        trace._TRACER_PROVIDER_SET_ONCE = Once()
        trace._TRACER_PROVIDER = None
        metrics._internal._METER_PROVIDER_SET_ONCE = Once()
        metrics._internal._METER_PROVIDER = None
        proxy = getattr(metrics._internal, "_PROXY_METER_PROVIDER", None)
        proxy_lock = getattr(proxy, "_lock", None)
        if proxy is not None and proxy_lock is not None and hasattr(proxy, "_real_meter_provider"):
            with proxy_lock:
                proxy._real_meter_provider = None
                for meter in getattr(proxy, "_meters", ()):
                    meter_lock = getattr(meter, "_lock", None)
                    if meter_lock is not None and hasattr(meter, "_real_meter"):
                        with meter_lock:
                            meter._real_meter = None
                            for inst in getattr(meter, "_instruments", ()):
                                if hasattr(inst, "_real_instrument"):
                                    inst._real_instrument = None
    finally:
        logging.setLogRecordFactory(orig_factory)
