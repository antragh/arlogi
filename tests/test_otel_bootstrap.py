"""Tests for arlogi.otel.bootstrap."""

import json
import logging

import pytest

pytest.importorskip("opentelemetry")

from opentelemetry import trace

from arlogi.otel import install_log_correlation, setup_tracing, shutdown_tracing


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


def test_shutdown_tracing_without_setup_is_a_noop(reset_otel_globals):
    shutdown_tracing()  # never initialised
    shutdown_tracing()  # and still safe to repeat


def test_setup_tracing_after_shutdown_creates_a_new_working_provider(tmp_path, reset_otel_globals):
    first = setup_tracing("svc", file_dir=tmp_path / "first", file_prefix="first")
    shutdown_tracing()

    second = setup_tracing("svc", file_dir=tmp_path / "second", file_prefix="second")
    assert second is not first
    assert trace.get_tracer_provider() is second

    with trace.get_tracer("t").start_as_current_span("after-restart"):
        pass
    second.shutdown()

    payload = json.loads(next((tmp_path / "second").glob("second-*.jsonl")).read_text(encoding="utf-8").strip())
    assert payload["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["name"] == "after-restart"


def test_setup_tracing_with_otlp_endpoint_adds_exporter_with_timeout(tmp_path, reset_otel_globals):
    provider = setup_tracing(
        "svc",
        file_dir=tmp_path,
        otlp_endpoint="http://localhost:19999",  # unused local port: fails fast, reaches nothing
        otlp_timeout=1,
    )
    processors = provider._active_span_processor._span_processors
    assert len(processors) == 2  # rotating file + OTLP

    otlp_exporter = processors[1].span_exporter
    assert otlp_exporter._endpoint == "http://localhost:19999/v1/traces"
    assert otlp_exporter._timeout == 1
    provider.shutdown()


def test_install_log_correlation_stamps_active_span_ids(tmp_path, reset_otel_globals):
    provider = setup_tracing("svc", file_dir=tmp_path)
    install_log_correlation()
    captured: list[logging.LogRecord] = []

    class Grab(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured.append(record)

    log = logging.getLogger("corr-test")
    grab = Grab()
    log.addHandler(grab)
    log.setLevel(logging.INFO)

    try:
        with trace.get_tracer("t").start_as_current_span("op"):
            log.info("inside")
        log.info("outside")
    finally:
        log.removeHandler(grab)
    provider.shutdown()

    inside, outside = captured
    assert len(inside.trace_id) == 32  # type: ignore[attr-defined]
    assert len(inside.span_id) == 16  # type: ignore[attr-defined]
    assert not hasattr(outside, "trace_id")


def test_install_log_correlation_is_idempotent(reset_otel_globals):
    before = logging.getLogRecordFactory()
    install_log_correlation()
    once = logging.getLogRecordFactory()
    assert once is not before
    install_log_correlation()
    assert logging.getLogRecordFactory() is once

    # Chained third-party closure wrapper must still be detected as already installed
    def third_party(*args: object, **kwargs: object) -> logging.LogRecord:
        return once(*args, **kwargs)  # type: ignore[arg-type]

    logging.setLogRecordFactory(third_party)
    install_log_correlation()
    assert logging.getLogRecordFactory() is third_party

    # Chained third-party functools.partial wrappers (positional & keyword) must also be detected
    import functools

    def partial_pos(prev, *args: object, **kwargs: object) -> logging.LogRecord:
        return prev(*args, **kwargs)

    wrapped_pos = functools.partial(partial_pos, once)
    logging.setLogRecordFactory(wrapped_pos)
    install_log_correlation()
    assert logging.getLogRecordFactory() is wrapped_pos

    def partial_kw(*args: object, prev: object = None, **kwargs: object) -> logging.LogRecord:
        assert callable(prev)
        return prev(*args, **kwargs)  # type: ignore[operator]

    wrapped_kw = functools.partial(partial_kw, prev=once)
    logging.setLogRecordFactory(wrapped_kw)
    install_log_correlation()
    assert logging.getLogRecordFactory() is wrapped_kw

    # Proxy object whose __getattr__ raises must not break correlation detection
    class RaisingProxy:
        def __getattr__(self, name: str) -> object:
            raise RuntimeError("proxy getattr failure")

        def __call__(self, *args: object, **kwargs: object) -> logging.LogRecord:
            return before(*args, **kwargs)  # type: ignore[arg-type]

    proxy = RaisingProxy()
    logging.setLogRecordFactory(proxy)
    install_log_correlation()
    assert logging.getLogRecordFactory() is not proxy


@pytest.mark.parametrize(
    "bad_endpoint",
    [
        " ",
        "   ",
        0,
        False,
        "ftp://localhost:4318",
        "http://:4318",
        "http://user@",
        "http://   ",
        "http://localhost:99999",
        "http://localhost:0",
        "http://[::1]:0",
        "http://localhost:",
        "http://[::1]:",
        "http://localhost:abc",
        "http://localhost:4318\r\nfoo",
        "http://collector:4318?",
        "http://collector:4318#",
        "http://collector:4318/otlp;",
        "http://collector:4318?token=abc",
        "http://collector:4318#frag",
    ],
)
def test_setup_tracing_and_metrics_reject_bad_endpoints_without_leaking_threads(
    tmp_path, reset_otel_globals, bad_endpoint
):
    import threading

    from arlogi.otel import setup_metrics

    threads_before = {t.ident for t in threading.enumerate()}
    with pytest.raises(ValueError, match="Invalid OTLP endpoint"):
        setup_tracing("svc", file_dir=tmp_path, otlp_endpoint=bad_endpoint)
    with pytest.raises(ValueError, match="Invalid OTLP endpoint"):
        setup_metrics("svc", file_dir=tmp_path, otlp_endpoint=bad_endpoint)
    threads_after = {t.ident for t in threading.enumerate()}
    assert threads_after - threads_before == set()


def test_setup_tracing_and_metrics_treat_empty_string_otlp_endpoint_as_disabled(tmp_path, reset_otel_globals):
    from arlogi.otel import setup_metrics, shutdown_metrics

    tp = setup_tracing("svc", file_dir=tmp_path / "traces", otlp_endpoint="")
    assert len(tp._active_span_processor._span_processors) == 1
    shutdown_tracing()

    mp = setup_metrics("svc", file_dir=tmp_path / "metrics", otlp_endpoint="")
    assert len(mp._metric_readers) == 1
    shutdown_metrics()


def test_setup_tracing_preserves_external_global_provider(tmp_path, reset_otel_globals):
    from opentelemetry.sdk.trace import TracerProvider

    ext = TracerProvider()
    trace.set_tracer_provider(ext)

    returned = setup_tracing("svc", file_dir=tmp_path)
    assert returned is ext
    shutdown_tracing()
    assert trace.get_tracer_provider() is ext


def test_shutdown_tracing_clears_state_when_processor_shutdown_raises(tmp_path, reset_otel_globals, monkeypatch):
    from arlogi.otel import traced

    first = setup_tracing("svc", file_dir=tmp_path / "run1", file_prefix="t1")
    processor = first._active_span_processor._span_processors[0]
    shutdown_calls = 0

    def failing_shutdown(*args, **kwargs):
        nonlocal shutdown_calls
        shutdown_calls += 1
        raise RuntimeError("processor shutdown boom")

    monkeypatch.setattr(processor, "shutdown", failing_shutdown)

    with pytest.raises(RuntimeError, match="processor shutdown boom"):
        shutdown_tracing()
    assert shutdown_calls == 1

    # Repeated shutdown is a no-op and does not re-invoke the dead processor
    shutdown_tracing()
    assert shutdown_calls == 1

    second = setup_tracing("svc", file_dir=tmp_path / "run2", file_prefix="t2")
    assert second is not first
    assert trace.get_tracer_provider() is second

    @traced
    def after_fail() -> str:
        return "ok"

    assert after_fail() == "ok"
    shutdown_tracing()

    payload = json.loads(next((tmp_path / "run2").glob("t2-*.jsonl")).read_text(encoding="utf-8").strip())
    assert payload["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["name"].endswith("after_fail")
