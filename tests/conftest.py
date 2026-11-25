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
    finally:
        logging.setLogRecordFactory(orig_factory)
