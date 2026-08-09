"""Tests for arlogi.otel.exporters.RotatingJsonlSpanExporter."""

import json

import pytest

pytest.importorskip("opentelemetry")

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from arlogi.otel import RotatingJsonlSpanExporter


def _provider_with(exporter):
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider


def test_export_writes_valid_otlp_json_line(tmp_path):
    exporter = RotatingJsonlSpanExporter(tmp_path, prefix="t")
    provider = _provider_with(exporter)
    with provider.get_tracer("test").start_as_current_span("hello"):
        pass
    provider.shutdown()

    files = list(tmp_path.glob("t-*.jsonl"))
    assert len(files) == 1
    lines = files[0].read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    span = payload["resourceSpans"][0]["scopeSpans"][0]["spans"][0]
    assert span["name"] == "hello"


def test_ids_are_hex_not_base64(tmp_path):
    exporter = RotatingJsonlSpanExporter(tmp_path, prefix="t")
    provider = _provider_with(exporter)
    with provider.get_tracer("test").start_as_current_span("parent"):
        with provider.get_tracer("test").start_as_current_span("child"):
            pass
    provider.shutdown()

    text = next(tmp_path.glob("t-*.jsonl")).read_text(encoding="utf-8")
    for line in text.strip().splitlines():
        for scope_spans in json.loads(line)["resourceSpans"][0]["scopeSpans"]:
            for span in scope_spans["spans"]:
                assert len(span["traceId"]) == 32
                int(span["traceId"], 16)
                assert len(span["spanId"]) == 16
                int(span["spanId"], 16)
                if "parentSpanId" in span:
                    assert len(span["parentSpanId"]) == 16
                    int(span["parentSpanId"], 16)


def test_rotation_creates_new_file_and_prunes_old(tmp_path):
    exporter = RotatingJsonlSpanExporter(tmp_path, prefix="t", rotate_hours=1, retention_count=2)
    clock = {"now": 1_700_000_000.0}
    exporter._writer._now = lambda: clock["now"]  # type: ignore[method-assign]
    provider = _provider_with(exporter)
    tracer = provider.get_tracer("test")

    for _ in range(4):
        with tracer.start_as_current_span("tick"):
            pass
        provider.force_flush()
        clock["now"] += 3700  # past the 1h boundary

    provider.shutdown()
    files = list(tmp_path.glob("t-*.jsonl"))
    assert len(files) == 2  # retention_count caps total files, oldest deleted


def test_io_error_degrades_to_noop_without_raising(tmp_path):
    exporter = RotatingJsonlSpanExporter(tmp_path / "sub", prefix="t")
    provider = _provider_with(exporter)
    with provider.get_tracer("test").start_as_current_span("one"):
        pass
    provider.force_flush()

    # Simulate the stream dying mid-run
    exporter._writer._stream.close()  # type: ignore[union-attr]
    with provider.get_tracer("test").start_as_current_span("two"):
        pass
    provider.force_flush()  # must not raise
    with provider.get_tracer("test").start_as_current_span("three"):
        pass
    provider.shutdown()  # must not raise
