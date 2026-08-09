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
from arlogi.otel import set_trace_modules


@pytest.fixture
def memory_spans(reset_otel_globals):
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return exporter


@pytest.fixture(autouse=True)
def _reset_trace_modules():
    """Gating rules are process-global; every test starts and ends clean."""
    set_trace_modules(None)
    yield
    set_trace_modules(None)


def _make_traced(module_name):
    """A traced function whose __module__ is overridden BEFORE decoration,
    so gating (and the span-name prefix) sees the synthetic module path."""

    def fn():
        return 1

    fn.__module__ = module_name
    return traced(fn)


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


def test_gated_off_module_runs_without_span(memory_spans):
    work = _make_traced("acme.api.client")
    set_trace_modules({"acme.api.client": False})
    assert work() == 1
    assert memory_spans.get_finished_spans() == ()


def test_longest_prefix_match_wins(memory_spans):
    gated = _make_traced("acme.api.client")
    sibling = _make_traced("acme.api.transport")
    unmatched = _make_traced("northwind.web")
    set_trace_modules({"acme": True, "acme.api.client": False})
    gated()
    sibling()
    unmatched()
    names = [s.name for s in memory_spans.get_finished_spans()]
    assert len(names) == 2
    assert not any(n.startswith("acme.api.client") for n in names)
    assert any(n.startswith("acme.api.transport") for n in names)
    assert any(n.startswith("northwind.web") for n in names)


def test_prefix_matches_dotted_segments_not_substrings(memory_spans):
    lookalike = _make_traced("acme.apix")
    set_trace_modules({"acme.api": False})
    lookalike()
    assert len(memory_spans.get_finished_spans()) == 1


def test_set_trace_modules_none_resets(memory_spans):
    work = _make_traced("acme.api.client")
    set_trace_modules({"acme": False})
    work()
    assert memory_spans.get_finished_spans() == ()
    set_trace_modules(None)
    work()
    assert len(memory_spans.get_finished_spans()) == 1


def test_gating_applies_after_decoration(memory_spans):
    work = _make_traced("acme.api.client")
    work()
    assert len(memory_spans.get_finished_spans()) == 1
    set_trace_modules({"acme": False})
    work()
    assert len(memory_spans.get_finished_spans()) == 1  # unchanged


def test_gated_off_is_noop_without_sdk():
    work = _make_traced("acme.api.client")
    set_trace_modules({"acme.api.client": False})
    assert work() == 1


def test_traced_attrs_recorded_on_span(memory_spans):
    @traced(attrs={"component": "demo", "kind": "unit"})
    def work():
        return 1

    work()
    span = memory_spans.get_finished_spans()[0]
    assert span.attributes["component"] == "demo"
    assert span.attributes["kind"] == "unit"


def test_traced_attrs_combine_with_custom_name(memory_spans):
    @traced(name="custom.op", attrs={"component": "demo"})
    async def work():
        return 1

    asyncio.run(work())
    span = memory_spans.get_finished_spans()[0]
    assert span.name == "custom.op"
    assert span.attributes["component"] == "demo"


def test_traced_attrs_is_noop_without_sdk():
    @traced(attrs={"component": "demo"})
    def work():
        return 7

    assert work() == 7
