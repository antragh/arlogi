"""Tests for the arlogi.otel metrics pipeline."""

import json
import logging

import pytest

pytest.importorskip("opentelemetry")

from opentelemetry import metrics
from opentelemetry.metrics import NoOpMeter

from arlogi.otel import setup_metrics, shutdown_metrics


def test_setup_metrics_writes_otlp_json_metrics_file(tmp_path, reset_otel_globals):
    provider = setup_metrics("svc", "1.0.0", file_dir=tmp_path, file_prefix="svc-metrics")
    counter = metrics.get_meter("test").create_counter("requests")
    counter.add(3)
    provider.force_flush()
    provider.shutdown()

    files = list(tmp_path.glob("svc-metrics-*.jsonl"))
    assert files
    payload = json.loads(files[0].read_text(encoding="utf-8").strip().splitlines()[0])
    metric = payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"][0]
    assert metric["name"] == "requests"


def test_setup_metrics_is_idempotent(tmp_path, reset_otel_globals):
    first = setup_metrics("svc", file_dir=tmp_path)
    second = setup_metrics("svc", file_dir=tmp_path)
    assert first is second
    first.shutdown()


def test_shutdown_metrics_without_setup_is_a_noop(reset_otel_globals):
    shutdown_metrics()  # never initialised
    shutdown_metrics()  # and still safe to repeat


def test_setup_metrics_after_shutdown_creates_a_new_working_provider(tmp_path, reset_otel_globals):
    first = setup_metrics("svc", file_dir=tmp_path / "first", file_prefix="first")
    shutdown_metrics()

    second = setup_metrics("svc", file_dir=tmp_path / "second", file_prefix="second")
    assert second is not first
    assert metrics.get_meter_provider() is second

    metrics.get_meter("test").create_counter("restarted").add(1)
    second.force_flush()
    second.shutdown()

    lines = next((tmp_path / "second").glob("second-*.jsonl")).read_text(encoding="utf-8").strip().splitlines()
    payload = json.loads(lines[0])
    assert payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"][0]["name"] == "restarted"


def test_setup_metrics_with_otlp_endpoint_adds_reader_with_timeout(tmp_path, reset_otel_globals):
    provider = setup_metrics(
        "svc",
        file_dir=tmp_path,
        otlp_endpoint="http://localhost:19999",  # unused local port: fails fast, reaches nothing
        otlp_timeout=1,
    )
    readers = provider._metric_readers
    assert len(readers) == 2  # rotating file + OTLP

    otlp_exporter = readers[1]._exporter
    assert otlp_exporter._endpoint == "http://localhost:19999/v1/metrics"
    assert otlp_exporter._timeout == 1
    provider.shutdown()


def test_meter_acquired_between_shutdown_and_setup_upgrades_to_new_provider(tmp_path, reset_otel_globals, caplog):
    setup_metrics("svc", file_dir=tmp_path / "run1", file_prefix="m1")
    shutdown_metrics()

    with caplog.at_level(logging.WARNING):
        gap_meter = metrics.get_meter("app.between")
        counter = gap_meter.create_counter("gap_hits")
    assert not isinstance(gap_meter, NoOpMeter)
    assert not any("shut down `MeterProvider`" in rec.message for rec in caplog.records)

    second = setup_metrics("svc", file_dir=tmp_path / "run2", file_prefix="m2")
    counter.add(1)
    second.force_flush()
    second.shutdown()

    lines = next((tmp_path / "run2").glob("m2-*.jsonl")).read_text(encoding="utf-8").strip().splitlines()
    payload = json.loads(lines[0])
    assert payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"][0]["name"] == "gap_hits"


def test_clear_global_meter_provider_tolerates_missing_proxy_lock(tmp_path, reset_otel_globals, caplog, monkeypatch):
    setup_metrics("svc", file_dir=tmp_path, file_prefix="m")
    proxy = metrics._internal._PROXY_METER_PROVIDER
    monkeypatch.delattr(proxy, "_lock")

    with caplog.at_level(logging.WARNING):
        shutdown_metrics()

    assert metrics._internal._METER_PROVIDER is None
    assert sum("could not release the global MeterProvider" in r.message for r in caplog.records) == 1


def test_shutdown_metrics_clears_state_when_reader_shutdown_raises(tmp_path, reset_otel_globals, caplog, monkeypatch):
    first = setup_metrics("svc", file_dir=tmp_path / "run1", file_prefix="m1")
    reader = first._metric_readers[0]
    shutdown_calls = 0

    def failing_shutdown(*args, **kwargs):
        nonlocal shutdown_calls
        shutdown_calls += 1
        raise RuntimeError("reader shutdown boom")

    monkeypatch.setattr(reader, "shutdown", failing_shutdown)

    with pytest.raises(Exception, match="reader shutdown boom"):
        shutdown_metrics()
    assert shutdown_calls == 1

    # Repeated shutdown is a no-op and does not invoke the dead provider again
    shutdown_metrics()
    assert shutdown_calls == 1

    with caplog.at_level(logging.WARNING):
        second = setup_metrics("svc", file_dir=tmp_path / "run2", file_prefix="m2")
    assert second is not first
    assert not any("called more than once" in r.message for r in caplog.records)

    metrics.get_meter("test").create_counter("after_fail").add(2)
    second.force_flush()
    second.shutdown()

    lines = next((tmp_path / "run2").glob("m2-*.jsonl")).read_text(encoding="utf-8").strip().splitlines()
    assert json.loads(lines[0])["resourceMetrics"][0]["scopeMetrics"][0]["metrics"][0]["name"] == "after_fail"


def test_chain03_failing_shutdown_and_gap_meter_still_recovers(tmp_path, reset_otel_globals, monkeypatch):
    first = setup_metrics("svc", file_dir=tmp_path / "run1", file_prefix="m1")
    monkeypatch.setattr(
        first._metric_readers[0], "shutdown", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    )

    with pytest.raises(Exception, match="boom"):
        shutdown_metrics()

    gap_counter = metrics.get_meter("chain03").create_counter("recovered")
    second = setup_metrics("svc", file_dir=tmp_path / "run2", file_prefix="m2")
    gap_counter.add(5)
    second.force_flush()
    second.shutdown()

    lines = next((tmp_path / "run2").glob("m2-*.jsonl")).read_text(encoding="utf-8").strip().splitlines()
    metric = json.loads(lines[0])["resourceMetrics"][0]["scopeMetrics"][0]["metrics"][0]
    assert metric["name"] == "recovered"


def test_preexisting_module_level_meter_creates_gap_instrument_that_upgrades(tmp_path, reset_otel_globals):
    pre_meter = metrics.get_meter("app.preexisting")
    pre_counter = pre_meter.create_counter("pre_hits")

    setup_metrics("svc", file_dir=tmp_path / "run1", file_prefix="m1")
    pre_counter.add(1)
    shutdown_metrics()

    # Instrument created during shutdown gap on pre-existing module-level meter
    gap_counter = pre_meter.create_counter("gap_hits")

    second = setup_metrics("svc", file_dir=tmp_path / "run2", file_prefix="m2")
    gap_counter.add(7)
    second.force_flush()
    second.shutdown()

    lines = next((tmp_path / "run2").glob("m2-*.jsonl")).read_text(encoding="utf-8").strip().splitlines()
    names = [
        m["name"]
        for line in lines
        for sm in json.loads(line)["resourceMetrics"][0]["scopeMetrics"]
        for m in sm["metrics"]
    ]
    assert "gap_hits" in names
