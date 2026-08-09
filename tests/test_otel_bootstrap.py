"""Tests for arlogi.otel.bootstrap."""

import json
import logging

import pytest

pytest.importorskip("opentelemetry")

from opentelemetry import trace

from arlogi.otel import install_log_correlation, setup_tracing


def test_setup_tracing_sets_global_provider_and_writes_file(tmp_path, reset_otel_globals):
    provider = setup_tracing("svc", "1.0.0", file_dir=tmp_path, file_prefix="svc-traces")
    assert trace.get_tracer_provider() is provider

    with trace.get_tracer("t").start_as_current_span("probe"):
        pass
    provider.shutdown()

    payload = json.loads(next(tmp_path.glob("svc-traces-*.jsonl")).read_text(encoding="utf-8").strip())
    resource_attrs = {
        a["key"]: a["value"]["stringValue"] for a in payload["resourceSpans"][0]["resource"]["attributes"]
    }
    assert resource_attrs["service.name"] == "svc"
    assert resource_attrs["service.version"] == "1.0.0"
    assert "host.name" in resource_attrs


def test_setup_tracing_is_idempotent(tmp_path, reset_otel_globals):
    first = setup_tracing("svc", file_dir=tmp_path)
    second = setup_tracing("svc", file_dir=tmp_path)
    assert first is second
    first.shutdown()


def test_install_log_correlation_stamps_active_span_ids(tmp_path, reset_otel_globals):
    provider = setup_tracing("svc", file_dir=tmp_path)
    install_log_correlation()
    captured: list[logging.LogRecord] = []

    class Grab(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured.append(record)

    log = logging.getLogger("corr-test")
    log.addHandler(Grab())
    log.setLevel(logging.INFO)

    with trace.get_tracer("t").start_as_current_span("op"):
        log.info("inside")
    log.info("outside")
    provider.shutdown()

    inside, outside = captured
    assert len(inside.trace_id) == 32  # type: ignore[attr-defined]
    assert len(inside.span_id) == 16  # type: ignore[attr-defined]
    assert not hasattr(outside, "trace_id")


def test_install_log_correlation_is_idempotent(reset_otel_globals):
    before = logging.getLogRecordFactory()
    install_log_correlation()
    once = logging.getLogRecordFactory()
    install_log_correlation()
    assert logging.getLogRecordFactory() is once
    logging.setLogRecordFactory(before)
