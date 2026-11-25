import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("opentelemetry")

from opentelemetry.sdk.metrics.export import MetricExportResult
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExportResult

from arlogi.otel import RotatingJsonlMetricExporter, RotatingJsonlSpanExporter
from arlogi.otel._files import _RotatingJsonlWriter


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
    assert exporter._writer._stream is None

    # Once broken, further calls are silent no-ops (short-circuited before touching the stream).
    assert exporter._writer.write_line('{"also": "broken"}') is False

    # The exporter/provider layers must not let the error (or the FAILURE result) propagate.
    with provider.get_tracer("test").start_as_current_span("two"):
        pass
    provider.force_flush()  # must not raise
    provider.shutdown()  # must not raise


def test_post_shutdown_exports_return_failure_without_reopening_files(tmp_path):
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

    span_dir = tmp_path / "spans"
    span_exporter = RotatingJsonlSpanExporter(span_dir, prefix="t")
    tp = TracerProvider()
    tp.add_span_processor(SimpleSpanProcessor(span_exporter))

    in_flight = tp.get_tracer("test").start_span("in_flight")
    tp.shutdown()
    assert span_exporter._writer._closed is True

    # Ending an in-flight span after shutdown must not reopen a file or leak an FD
    in_flight.end()
    assert list(span_dir.glob("t-*.jsonl")) == []
    assert span_exporter.export([MagicMock()]) == SpanExportResult.FAILURE
    assert span_exporter._writer._stream is None

    metric_dir = tmp_path / "metrics"
    metric_exporter = RotatingJsonlMetricExporter(metric_dir, prefix="m")
    reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=60_000)
    mp = MeterProvider(metric_readers=[reader])
    mp.get_meter("test").create_counter("c").add(1)
    mp.force_flush()
    before_files = set(metric_dir.glob("m-*.jsonl"))
    mp.shutdown()
    reader.collect()
    after_files = set(metric_dir.glob("m-*.jsonl"))
    assert after_files == before_files
    assert metric_exporter._writer._stream is None


def test_concurrent_writes_thread_safe(tmp_path):
    """Multiple threads concurrently writing to the writer must produce clean, non-corrupted jsonl."""
    writer = _RotatingJsonlWriter(tmp_path, prefix="concurrent", rotate_hours=24, retention_count=10)
    lines_per_thread = 50
    thread_count = 20

    def worker(worker_id: int):
        for i in range(lines_per_thread):
            line = json.dumps({"worker": worker_id, "seq": i})
            assert writer.write_line(line) is True

    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = [executor.submit(worker, tid) for tid in range(thread_count)]
        for f in as_completed(futures):
            f.result()

    writer.close()

    files = list(tmp_path.glob("concurrent-*.jsonl"))
    assert len(files) >= 1
    total_lines = 0
    for f in files:
        for line in f.read_text(encoding="utf-8").strip().splitlines():
            data = json.loads(line)
            assert "worker" in data
            total_lines += 1

    assert total_lines == thread_count * lines_per_thread


def test_writer_stream_none_handled_gracefully(tmp_path):
    """If _stream is None after opening attempt, writer safely marks broken without assert error."""
    writer = _RotatingJsonlWriter(tmp_path, prefix="none_test", rotate_hours=24, retention_count=10)
    # Patch _open_new_file to be a no-op so _stream remains None
    with patch.object(writer, "_open_new_file", return_value=None):
        ok = writer.write_line('{"msg": "test"}')
        assert ok is False
        assert writer._broken is True


def test_span_exporter_logs_warning_on_encode_failure(tmp_path, caplog):
    """SpanExporter logs warning with exc_info when span encoding fails."""
    exporter = RotatingJsonlSpanExporter(tmp_path, prefix="test")
    span = MagicMock()
    with patch("arlogi.otel.exporters.encode_spans", side_effect=ValueError("Invalid span data")):
        with caplog.at_level(logging.WARNING):
            result = exporter.export([span])
            assert result == SpanExportResult.FAILURE
            assert any("Failed to encode telemetry spans" in record.message for record in caplog.records)


def test_metric_exporter_logs_warning_on_encode_failure(tmp_path, caplog):
    """MetricExporter logs warning with exc_info when metric encoding fails."""
    exporter = RotatingJsonlMetricExporter(tmp_path, prefix="test")
    metrics_data = MagicMock()
    with patch("arlogi.otel.exporters.encode_metrics", side_effect=ValueError("Invalid metric data")):
        with caplog.at_level(logging.WARNING):
            result = exporter.export(metrics_data)
            assert result == MetricExportResult.FAILURE
            assert any("Failed to encode telemetry metrics" in record.message for record in caplog.records)


@pytest.mark.parametrize("bad_prefix", ["", ".", "..", "../escape", "/tmp/abs", "sub/dir", "*", "svc[1]", "a\x00b"])
def test_writer_rejects_unsafe_prefix(tmp_path, bad_prefix):
    with pytest.raises(ValueError, match="Invalid telemetry file prefix"):
        _RotatingJsonlWriter(tmp_path, prefix=bad_prefix, rotate_hours=24, retention_count=5)


@pytest.mark.parametrize("bad_hours", [0, -1, True, "1"])
def test_writer_rejects_invalid_rotate_hours(tmp_path, bad_hours):
    with pytest.raises(ValueError, match="rotate_hours"):
        _RotatingJsonlWriter(tmp_path, prefix="traces", rotate_hours=bad_hours, retention_count=5)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_retention", [0, -1, True, "5"])
def test_writer_rejects_invalid_retention_count(tmp_path, bad_retention):
    with pytest.raises(ValueError, match="retention_count"):
        _RotatingJsonlWriter(tmp_path, prefix="traces", rotate_hours=24, retention_count=bad_retention)  # type: ignore[arg-type]


def test_writer_prune_skips_dangling_symlink_and_preserves_sibling_files(tmp_path):
    sibling = tmp_path / "traces-audit.jsonl"
    sibling.write_text('{"keep": true}\n', encoding="utf-8")
    dangling = tmp_path / "traces-20200101-000000.jsonl"
    dangling.symlink_to(tmp_path / "missing-target.jsonl")

    writer = _RotatingJsonlWriter(tmp_path, prefix="traces", rotate_hours=1, retention_count=1)
    assert writer.write_line('{"ok": 1}') is True
    assert writer.write_line('{"ok": 2}') is True
    assert writer._broken is False
    assert sibling.exists()
    writer.close()


def test_writer_prune_equal_mtime_keeps_newer_and_ignores_matching_dir(tmp_path):
    older = tmp_path / "traces-20200101-000000.jsonl"
    newer = tmp_path / "traces-20200101-000001.jsonl"
    older.write_text('{"seq": 0}\n', encoding="utf-8")
    newer.write_text('{"seq": 1}\n', encoding="utf-8")
    equal_ns = 1_700_000_000_000_000_000
    os.utime(older, ns=(equal_ns, equal_ns))
    os.utime(newer, ns=(equal_ns, equal_ns))

    matching_dir = tmp_path / "traces-20200102-000000.jsonl"
    matching_dir.mkdir()
    os.utime(matching_dir, ns=(equal_ns + 1_000_000_000, equal_ns + 1_000_000_000))

    writer = _RotatingJsonlWriter(tmp_path, prefix="traces", rotate_hours=1, retention_count=2)
    writer._now = lambda: 1_750_000_000.0  # type: ignore[method-assign]
    assert writer.write_line('{"seq": 2}') is True
    writer.close()

    assert not older.exists()
    assert newer.exists()
    assert matching_dir.is_dir()


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlink semantics")
def test_writer_open_skips_dangling_live_symlinks_and_existing_files(tmp_path):
    telem = tmp_path / "telem"
    telem.mkdir()
    outside = tmp_path / "outside.jsonl"

    writer = _RotatingJsonlWriter(telem, prefix="traces", rotate_hours=1, retention_count=10)
    writer._now = lambda: 1_700_000_000.0  # type: ignore[method-assign]
    from datetime import datetime

    stamp = datetime.fromtimestamp(1_700_000_000.0).strftime("%Y%m%d-%H%M%S")

    # (a) Dangling symlink pointing outside telem
    dangling = telem / f"traces-{stamp}.jsonl"
    dangling.symlink_to(outside)
    assert writer.write_line('{"case": "a"}') is True
    assert not outside.exists()
    assert dangling.is_symlink()
    assert (telem / f"traces-{stamp}.1.jsonl").read_text(encoding="utf-8").strip() == '{"case": "a"}'
    writer.close()

    # (b) Dangling symlink pointing to missing parent dir does not mark writer broken
    dangling_missing_parent = telem / f"traces-{stamp}.2.jsonl"
    dangling_missing_parent.symlink_to(tmp_path / "missing_dir" / "target.jsonl")
    writer2 = _RotatingJsonlWriter(telem, prefix="traces", rotate_hours=1, retention_count=10)
    writer2._now = lambda: 1_700_000_000.0  # type: ignore[method-assign]
    assert writer2.write_line('{"case": "b"}') is True
    assert writer2._broken is False
    assert (telem / f"traces-{stamp}.3.jsonl").read_text(encoding="utf-8").strip() == '{"case": "b"}'
    writer2.close()

    # (c) Live symlink to outside file and pre-existing regular file are skipped untouched
    live_outside = tmp_path / "live_outside.jsonl"
    live_outside.write_text("do-not-touch\n", encoding="utf-8")
    (telem / f"traces-{stamp}.4.jsonl").symlink_to(live_outside)
    existing_reg = telem / f"traces-{stamp}.5.jsonl"
    existing_reg.write_text("existing\n", encoding="utf-8")
    writer3 = _RotatingJsonlWriter(telem, prefix="traces", rotate_hours=1, retention_count=10)
    writer3._now = lambda: 1_700_000_000.0  # type: ignore[method-assign]
    assert writer3.write_line('{"case": "c"}') is True
    assert live_outside.read_text(encoding="utf-8") == "do-not-touch\n"
    assert existing_reg.read_text(encoding="utf-8") == "existing\n"
    assert (telem / f"traces-{stamp}.6.jsonl").read_text(encoding="utf-8").strip() == '{"case": "c"}'
    writer3.close()


def test_writer_open_two_writers_same_second_and_suffix_exhaustion(tmp_path, caplog, monkeypatch):
    w1 = _RotatingJsonlWriter(tmp_path, prefix="traces", rotate_hours=1, retention_count=10)
    w2 = _RotatingJsonlWriter(tmp_path, prefix="traces", rotate_hours=1, retention_count=10)
    w1._now = lambda: 1_700_000_000.0  # type: ignore[method-assign]
    w2._now = lambda: 1_700_000_000.0  # type: ignore[method-assign]
    assert w1.write_line('{"writer": 1}') is True
    assert w2.write_line('{"writer": 2}') is True
    p1, p2 = w1._active_path, w2._active_path
    w1.close()
    w2.close()
    assert p1 is not None and p2 is not None and p1 != p2
    assert p1.read_text(encoding="utf-8").strip() == '{"writer": 1}'
    assert p2.read_text(encoding="utf-8").strip() == '{"writer": 2}'

    # Suffix exhaustion sets _broken and logs one warning
    monkeypatch.setattr("arlogi.otel._files._MAX_COLLISION_SUFFIX", 1)
    w3 = _RotatingJsonlWriter(tmp_path, prefix="traces", rotate_hours=1, retention_count=10)
    w3._now = lambda: 1_700_000_000.0  # type: ignore[method-assign]
    with caplog.at_level(logging.WARNING):
        assert w3.write_line('{"writer": 3}') is False
    assert w3._broken is True
    assert sum("Telemetry file writer disabled" in r.message for r in caplog.records) == 1
    w3.close()
