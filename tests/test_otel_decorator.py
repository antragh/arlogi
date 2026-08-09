"""Tests for arlogi.otel.decorator.traced."""

import asyncio

import pytest

pytest.importorskip("opentelemetry")

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from arlogi.otel import traced


@pytest.fixture
def memory_spans(reset_otel_globals):
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return exporter


def test_traced_sync_records_span(memory_spans):
    @traced
    def add(a, b):
        return a + b

    assert add(2, 3) == 5
    spans = memory_spans.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name.endswith("add")


def test_traced_async_records_span(memory_spans):
    @traced
    async def fetch():
        return "ok"

    assert asyncio.run(fetch()) == "ok"
    spans = memory_spans.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name.endswith("fetch")


def test_traced_custom_name(memory_spans):
    @traced(name="custom.op")
    def work():
        return 1

    work()
    assert memory_spans.get_finished_spans()[0].name == "custom.op"


def test_traced_records_exception_and_error_status(memory_spans):
    @traced
    def boom():
        raise ValueError("nope")

    with pytest.raises(ValueError):
        boom()
    span = memory_spans.get_finished_spans()[0]
    assert span.status.status_code == StatusCode.ERROR
    assert any(e.name == "exception" for e in span.events)


def test_traced_is_noop_without_sdk():
    # No provider configured in this test — must still execute transparently.
    @traced
    def plain(x):
        return x * 2

    assert plain(21) == 42
