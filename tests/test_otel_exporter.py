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


def test_stream_closed_externally_triggers_self_heal_reopen(tmp_path):
    """If something else closes the stream, write_line reopens a fresh file rather than erroring.

    This exercises the `self._stream.closed` self-healing branch in write_line — a different
    code path from the OSError-during-write degrade tested below.
    """
    exporter = RotatingJsonlSpanExporter(tmp_path / "sub", prefix="t")
    provider = _provider_with(exporter)
    with provider.get_tracer("test").start_as_current_span("one"):
        pass
    provider.force_flush()

    # Simulate the stream being closed by something external to the writer
    exporter._writer._stream.close()  # type: ignore[union-attr]
    with provider.get_tracer("test").start_as_current_span("two"):
        pass
    provider.force_flush()  # must not raise; writer transparently reopens a new file
    with provider.get_tracer("test").start_as_current_span("three"):
        pass
    provider.shutdown()  # must not raise
    assert exporter._writer._broken is False


def test_io_error_degrades_to_noop_without_raising(tmp_path):
    """A real OSError raised during write() must permanently degrade the writer to a no-op.

    Telemetry must never break the host app: after an OSError, write_line returns False
    (rather than raising) on every subsequent call, and export()/shutdown() stay silent too.
    """
    exporter = RotatingJsonlSpanExporter(tmp_path, prefix="t")
    provider = _provider_with(exporter)

    # First write succeeds normally, opening the file.
    with provider.get_tracer("test").start_as_current_span("one"):
        pass
    provider.force_flush()
    assert exporter._writer._broken is False

    def _boom(*_args, **_kwargs):
        raise OSError("disk full")

    exporter._writer._stream.write = _boom  # type: ignore[union-attr]

    # Direct write_line call must return False, not raise.
    assert exporter._writer.write_line('{"still": "broken"}') is False
    assert exporter._writer._broken is True

    # Once broken, further calls are silent no-ops (short-circuited before touching the stream).
    assert exporter._writer.write_line('{"also": "broken"}') is False

    # The exporter/provider layers must not let the error (or the FAILURE result) propagate.
    with provider.get_tracer("test").start_as_current_span("two"):
        pass
    provider.force_flush()  # must not raise
    provider.shutdown()  # must not raise
