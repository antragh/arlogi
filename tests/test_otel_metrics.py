"""Tests for the arlogi.otel metrics pipeline."""

import json

import pytest

pytest.importorskip("opentelemetry")

from opentelemetry import metrics

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
