"""Shared pytest fixtures. OTEL fixtures are inert when the [otel] extra is absent."""

import pytest


@pytest.fixture
def reset_otel_globals():
    """Reset OpenTelemetry global provider state after a test that sets it."""
    yield
    from opentelemetry import metrics, trace
    from opentelemetry.util._once import Once

    trace._TRACER_PROVIDER_SET_ONCE = Once()
    trace._TRACER_PROVIDER = None
    metrics._internal._METER_PROVIDER_SET_ONCE = Once()
    metrics._internal._METER_PROVIDER = None

    try:
        import arlogi.otel.bootstrap as bootstrap

        bootstrap._tracer_provider = None
        bootstrap._meter_provider = None
    except ImportError:
        pass  # bootstrap module may be absent (partial install)
