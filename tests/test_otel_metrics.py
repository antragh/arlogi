"""Tests for the arlogi.otel metrics pipeline."""

import json

import pytest

pytest.importorskip("opentelemetry")

from opentelemetry import metrics

from arlogi.otel import setup_metrics


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
