"""Shared pytest fixtures. OTEL fixtures are inert when the [otel] extra is absent."""

import pytest


@pytest.fixture
def reset_otel_globals():
    """Reset OpenTelemetry global provider state after a test that sets it."""
    yield
    try:
        from opentelemetry import metrics, trace
        from opentelemetry.util._once import Once

        from arlogi.otel import shutdown_metrics, shutdown_tracing
    except ImportError:
        return  # [otel] extra absent (partial install); nothing to reset

    # Providers created through arlogi's bootstrap: public teardown, which also
    # releases OpenTelemetry's set-once global slots.
    shutdown_tracing()
    shutdown_metrics()

    # Providers a test registered directly, bypassing arlogi's bootstrap.
    trace._TRACER_PROVIDER_SET_ONCE = Once()
    trace._TRACER_PROVIDER = None
    metrics._internal._METER_PROVIDER_SET_ONCE = Once()
    metrics._internal._METER_PROVIDER = None
