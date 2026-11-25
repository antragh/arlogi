"""Tests for arlogi.otel.decorator.traced."""

import asyncio
import inspect
import subprocess
import sys
import threading

import pytest

pytest.importorskip("opentelemetry")

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from arlogi.otel import set_trace_modules, traced


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


def test_traced_async_gen_span_covers_full_iteration(memory_spans):
    @traced
    async def stream():
        yield 1
        yield 2

    async def consume():
        agen = stream()
        first = await agen.__anext__()
        # Mid-iteration: the generator's span must still be open.
        assert memory_spans.get_finished_spans() == ()
        rest = [item async for item in agen]
        return [first, *rest]

    assert asyncio.run(consume()) == [1, 2]
    spans = memory_spans.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name.endswith("stream")


def test_traced_async_gen_exception_recorded_and_span_ended(memory_spans):
    @traced
    async def broken():
        yield 1
        raise ValueError("mid-iteration")

    async def consume():
        items = []
        with pytest.raises(ValueError):
            async for item in broken():
                items.append(item)
        return items

    assert asyncio.run(consume()) == [1]
    span = memory_spans.get_finished_spans()[0]
    assert span.status.status_code == StatusCode.ERROR
    assert any(e.name == "exception" for e in span.events)


def test_traced_async_gen_aclose_ends_span_without_error(memory_spans):
    @traced
    async def stream():
        yield 1
        yield 2

    async def consume():
        agen = stream()
        assert await agen.__anext__() == 1
        await agen.aclose()

    asyncio.run(consume())
    spans = memory_spans.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code != StatusCode.ERROR


def test_consumer_spans_between_yields_not_parented_under_gen_span(memory_spans):
    tracer = trace.get_tracer(__name__)

    @traced
    async def stream():
        yield 1
        yield 2

    async def consume():
        agen = stream()
        await agen.__anext__()
        with tracer.start_as_current_span("consumer-work"):
            pass
        async for _ in agen:
            pass

    asyncio.run(consume())
    spans = {s.name: s for s in memory_spans.get_finished_spans()}
    assert spans["consumer-work"].parent is None


def test_spans_inside_gen_body_parent_under_gen_span(memory_spans):
    tracer = trace.get_tracer(__name__)

    @traced
    async def stream():
        with tracer.start_as_current_span("inner-work"):
            pass
        yield 1

    async def consume():
        async for _ in stream():
            pass

    asyncio.run(consume())
    spans = {s.name: s for s in memory_spans.get_finished_spans()}
    gen_span = next(s for n, s in spans.items() if n.endswith("stream"))
    inner = spans["inner-work"]
    assert inner.parent is not None
    assert inner.parent.span_id == gen_span.context.span_id


def test_traced_async_gen_gated_off_yields_without_span(memory_spans):
    @traced
    async def stream():
        yield 1
        yield 2

    set_trace_modules({stream.__module__: False})

    async def consume():
        return [item async for item in stream()]

    assert asyncio.run(consume()) == [1, 2]
    assert memory_spans.get_finished_spans() == ()


def test_traced_async_gen_attrs_recorded(memory_spans):
    @traced(attrs={"component": "demo"})
    async def stream():
        yield 1

    async def consume():
        return [item async for item in stream()]

    assert asyncio.run(consume()) == [1]
    assert memory_spans.get_finished_spans()[0].attributes["component"] == "demo"


def test_traced_async_gen_is_noop_without_sdk():
    @traced
    async def stream():
        yield 1
        yield 2

    async def consume():
        return [item async for item in stream()]

    assert asyncio.run(consume()) == [1, 2]


def test_traced_sync_gen_span_covers_full_iteration(memory_spans):
    @traced
    def counter():
        yield 1
        yield 2

    gen = counter()
    assert next(gen) == 1
    assert memory_spans.get_finished_spans() == ()
    assert list(gen) == [2]
    spans = memory_spans.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name.endswith("counter")


def test_traced_sync_gen_close_ends_span_without_error(memory_spans):
    @traced
    def counter():
        yield 1
        yield 2

    gen = counter()
    assert next(gen) == 1
    gen.close()
    spans = memory_spans.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code != StatusCode.ERROR


def test_traced_sync_gen_exception_recorded(memory_spans):
    @traced
    def broken():
        yield 1
        raise ValueError("mid-iteration")

    gen = broken()
    assert next(gen) == 1
    with pytest.raises(ValueError):
        next(gen)
    span = memory_spans.get_finished_spans()[0]
    assert span.status.status_code == StatusCode.ERROR


def test_traced_sync_gen_gated_off_yields_without_span(memory_spans):
    @traced
    def counter():
        yield 1
        yield 2

    set_trace_modules({counter.__module__: False})
    assert list(counter()) == [1, 2]
    assert memory_spans.get_finished_spans() == ()


def test_traced_sync_gen_is_noop_without_sdk():
    @traced
    def counter():
        yield 1
        yield 2

    assert list(counter()) == [1, 2]


def test_decorator_module_never_imports_otel_sdk():
    """cpaiops-class consumers import arlogi.otel.decorator directly with only
    opentelemetry-api installed. Importing it must not pull the SDK."""
    code = (
        "import sys\n"
        "import arlogi.otel.decorator\n"
        "sdk = [m for m in sys.modules if m.startswith('opentelemetry.sdk')]\n"
        "assert not sdk, f'decorator imported the OTEL SDK: {sdk}'\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_traced_survives_shutdown_and_restart(tmp_path, reset_otel_globals):
    from arlogi.otel import setup_tracing, shutdown_tracing

    @traced
    def work():
        return 42

    dir1 = tmp_path / "run1"
    dir2 = tmp_path / "run2"
    setup_tracing("svc", file_dir=dir1)
    assert work() == 42
    shutdown_tracing()

    setup_tracing("svc", file_dir=dir2)
    assert work() == 42
    shutdown_tracing()

    assert list(dir1.glob("traces-*.jsonl"))
    assert list(dir2.glob("traces-*.jsonl"))


def test_traced_sync_gen_forwards_send_throw_return_and_closes_inner(memory_spans):
    closed = {"flag": False}

    @traced
    def echo(required_arg: int):
        try:
            received = yield required_arg
            try:
                yield received + 1
            except RuntimeError as exc:
                yield f"caught:{exc}"
            return "done"
        finally:
            closed["flag"] = True

    gen = echo(10)
    assert next(gen) == 10
    assert gen.send(20) == 21
    assert gen.throw(RuntimeError("oops")) == "caught:oops"
    with pytest.raises(StopIteration) as stop_info:
        next(gen)
    assert stop_info.value.value == "done"
    assert closed["flag"] is True

    # Early close triggers inner generator finally block
    closed["flag"] = False
    gen2 = echo(1)
    assert next(gen2) == 1
    gen2.close()
    assert closed["flag"] is True

    # Argument binding TypeError must not leak an open span
    with pytest.raises(TypeError):
        list(echo())  # type: ignore[call-arg]
    assert len(memory_spans.get_finished_spans()) == 2


def test_traced_async_gen_closes_inner_and_forwards_asend_athrow(memory_spans):
    closed = {"flag": False}

    @traced
    async def astream(required_arg: int):
        try:
            val = yield required_arg
            try:
                yield val * 2
            except RuntimeError as exc:
                yield f"caught:{exc}"
        finally:
            closed["flag"] = True

    async def drive():
        agen = astream(5)
        assert await agen.__anext__() == 5
        assert await agen.asend(7) == 14
        assert await agen.athrow(RuntimeError("boom")) == "caught:boom"
        await agen.aclose()
        assert closed["flag"] is True

        closed["flag"] = False
        agen2 = astream(3)
        assert await agen2.__anext__() == 3
        await agen2.aclose()
        assert closed["flag"] is True

        with pytest.raises(TypeError):
            [x async for x in astream()]  # type: ignore[call-arg]

    asyncio.run(drive())
    assert len(memory_spans.get_finished_spans()) == 2


def test_traced_async_gen_gated_off_forwards_asend_athrow_aclose(memory_spans):
    cleaned = {"flag": False}

    @traced
    async def astream(start: int):
        try:
            val = yield start
            try:
                yield val
            except RuntimeError as exc:
                yield f"caught:{exc}"
            yield "unreachable-if-closed"
        finally:
            cleaned["flag"] = True

    assert inspect.isasyncgenfunction(astream)
    set_trace_modules({astream.__module__: False})

    async def drive():
        agen = astream(5)
        assert await agen.__anext__() == 5
        assert await agen.asend(7) == 7
        assert await agen.athrow(RuntimeError("boom")) == "caught:boom"
        await agen.aclose()
        assert cleaned["flag"] is True

    asyncio.run(drive())
    assert memory_spans.get_finished_spans() == ()


def test_traced_sync_and_async_gen_cleanup_runs_inside_span_context(memory_spans):
    tracer = trace.get_tracer(__name__)
    captured: list[int] = []

    @traced
    def sync_stream():
        try:
            yield 1
            yield 2
        finally:
            captured.append(trace.get_current_span().get_span_context().span_id)
            with tracer.start_as_current_span("sync-cleanup-child"):
                pass

    @traced
    async def async_stream():
        try:
            yield 1
            yield 2
        finally:
            captured.append(trace.get_current_span().get_span_context().span_id)
            with tracer.start_as_current_span("async-cleanup-child"):
                pass

    g = sync_stream()
    assert next(g) == 1
    g.close()

    async def close_async():
        ag = async_stream()
        assert await ag.__anext__() == 1
        await ag.aclose()

    asyncio.run(close_async())

    spans = {s.name: s for s in memory_spans.get_finished_spans()}
    sync_parent = next(s for n, s in spans.items() if n.endswith("sync_stream"))
    async_parent = next(s for n, s in spans.items() if n.endswith("async_stream"))
    assert captured[0] == sync_parent.context.span_id
    assert captured[1] == async_parent.context.span_id
    assert spans["sync-cleanup-child"].parent is not None
    assert spans["sync-cleanup-child"].parent.span_id == sync_parent.context.span_id
    assert spans["async-cleanup-child"].parent is not None
    assert spans["async-cleanup-child"].parent.span_id == async_parent.context.span_id


def test_traced_gen_cleanup_exception_marks_span_error_and_cancellation_stays_non_error(memory_spans):
    @traced
    def sync_boom():
        try:
            yield 1
        finally:
            raise RuntimeError("cleanup boom")

    @traced
    async def async_boom():
        try:
            yield 1
        finally:
            raise RuntimeError("cleanup boom")

    @traced
    async def async_cancellable(ready: asyncio.Event):
        yield 1
        ready.set()
        await asyncio.sleep(10)

    g = sync_boom()
    assert next(g) == 1
    with pytest.raises(RuntimeError, match="cleanup boom"):
        g.close()

    async def drive_async():
        ag = async_boom()
        assert await ag.__anext__() == 1
        with pytest.raises(RuntimeError, match="cleanup boom"):
            await ag.aclose()

        ready = asyncio.Event()
        ag_cancel = async_cancellable(ready)
        assert await ag_cancel.__anext__() == 1
        task = asyncio.create_task(ag_cancel.__anext__())
        await ready.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await ag_cancel.aclose()

    asyncio.run(drive_async())

    spans = list(memory_spans.get_finished_spans())
    assert len(spans) == 3
    for err_span in spans[:2]:
        assert err_span.status.status_code == StatusCode.ERROR
        assert len([e for e in err_span.events if e.name == "exception"]) == 1
    assert spans[2].status.status_code != StatusCode.ERROR
    assert not [e for e in spans[2].events if e.name == "exception"]


def test_tracer_cache_atomic_under_concurrent_provider_swap(reset_otel_globals):
    from opentelemetry.util._once import Once

    exp0, exp1 = InMemorySpanExporter(), InMemorySpanExporter()
    p0, p1 = TracerProvider(), TracerProvider()
    p0.add_span_processor(SimpleSpanProcessor(exp0))
    p1.add_span_processor(SimpleSpanProcessor(exp1))
    trace.set_tracer_provider(p0)

    @traced
    def work() -> str:
        return "ok"

    assert work() == "ok"
    assert len(exp0.get_finished_spans()) == 1

    trace._TRACER_PROVIDER_SET_ONCE = Once()
    trace._TRACER_PROVIDER = None
    trace.set_tracer_provider(p1)

    entered = threading.Event()
    release = threading.Event()
    orig_get_tracer = p1.get_tracer
    lock = threading.Lock()
    first_call = {"done": False}

    def gated_get_tracer(*args, **kwargs):
        with lock:
            is_first = not first_call["done"]
            if is_first:
                first_call["done"] = True
        if is_first:
            entered.set()
            release.wait(timeout=5)
        return orig_get_tracer(*args, **kwargs)

    p1.get_tracer = gated_get_tracer  # type: ignore[method-assign]
    t_a = threading.Thread(target=work)
    t_a.start()
    assert entered.wait(timeout=5)
    try:
        assert work() == "ok"
        # Thread B must record to P1 immediately rather than stale P0
        assert len(exp1.get_finished_spans()) == 1
        assert len(exp0.get_finished_spans()) == 1
    finally:
        release.set()
        t_a.join(timeout=5)

    assert len(exp1.get_finished_spans()) == 2
    p0.shutdown()
    p1.shutdown()


def test_tracer_cache_acquires_tracer_from_read_provider(reset_otel_globals):
    from opentelemetry.util._once import Once

    exp_a, exp_b = InMemorySpanExporter(), InMemorySpanExporter()
    p_a, p_b = TracerProvider(), TracerProvider()
    p_a.add_span_processor(SimpleSpanProcessor(exp_a))
    p_b.add_span_processor(SimpleSpanProcessor(exp_b))
    trace.set_tracer_provider(p_a)

    orig_a_get_tracer = p_a.get_tracer

    def swapping_get_tracer(*args, **kwargs):
        trace._TRACER_PROVIDER_SET_ONCE = Once()
        trace._TRACER_PROVIDER = None
        trace.set_tracer_provider(p_b)
        return orig_a_get_tracer(*args, **kwargs)

    p_a.get_tracer = swapping_get_tracer  # type: ignore[method-assign]

    @traced
    def op() -> int:
        return 1

    assert op() == 1
    assert len(exp_a.get_finished_spans()) == 1
    assert len(exp_b.get_finished_spans()) == 0
    # Next call picks up p_b cleanly
    assert op() == 1
    assert len(exp_b.get_finished_spans()) == 1
    p_a.shutdown()
    p_b.shutdown()


def test_proxy_tracer_provider_not_cached_across_setup_and_shutdown(reset_otel_globals):
    from opentelemetry.util._once import Once

    exp = InMemorySpanExporter()
    p1 = TracerProvider()
    p1.add_span_processor(SimpleSpanProcessor(exp))
    seen_recording: list[bool] = []

    @traced
    def work() -> None:
        seen_recording.append(trace.get_current_span().is_recording())

    # Prime while global provider is still ProxyTracerProvider
    work()
    assert seen_recording[-1] is False

    # Now install p1 and invoke work() (latches ProxyTracer if cached)
    trace.set_tracer_provider(p1)
    work()
    assert seen_recording[-1] is True

    # Simulate shutdown_tracing() clearing global TracerProvider slot
    p1.shutdown()
    trace._TRACER_PROVIDER_SET_ONCE = Once()
    trace._TRACER_PROVIDER = None

    # Gap call must observe a NonRecordingSpan, never shut-down p1
    work()
    assert seen_recording[-1] is False

    # Also test provider-read race during setup_tracing()
    @traced
    def raced() -> None:
        seen_recording.append(trace.get_current_span().is_recording())

    proxy = trace._PROXY_TRACER_PROVIDER
    orig_get_tracer = proxy.get_tracer
    exp2 = InMemorySpanExporter()
    p2 = TracerProvider()
    p2.add_span_processor(SimpleSpanProcessor(exp2))

    def install_during_get_tracer(*args, **kwargs):
        trace.set_tracer_provider(p2)
        return orig_get_tracer(*args, **kwargs)

    proxy.get_tracer = install_during_get_tracer  # type: ignore[method-assign]
    try:
        raced()
    finally:
        proxy.get_tracer = orig_get_tracer  # type: ignore[method-assign]

    p2.shutdown()
    trace._TRACER_PROVIDER_SET_ONCE = Once()
    trace._TRACER_PROVIDER = None
    raced()
    assert seen_recording[-1] is False
