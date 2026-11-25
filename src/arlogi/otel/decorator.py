"""@traced decorator for sync and async functions."""

import asyncio
import functools
import inspect
from collections.abc import Callable
from typing import Any, overload

from opentelemetry import trace

_trace_modules: dict[str, bool] = {}


def set_trace_modules(rules: dict[str, bool] | None) -> None:
    """Replace per-module span gating rules.

    Keys are dotted module prefixes; values enable/disable spans for that
    subtree. Longest-prefix match wins. Modules matching no rule default to
    enabled. None or {} clears all rules (trace everything).
    """
    global _trace_modules
    _trace_modules = dict(rules) if rules else {}


def _module_enabled(module: str) -> bool:
    rules = _trace_modules
    if not rules:
        return True
    parts = module.split(".")
    while parts:
        enabled = rules.get(".".join(parts))
        if enabled is not None:
            return enabled
        parts.pop()
    return True


def _make_tracer_getter(module: str) -> Callable[[], trace.Tracer]:
    """Return a provider-keyed tracer lookup that tracks global provider restarts."""
    cache: tuple[Any, trace.Tracer] | None = None

    def get_tracer() -> trace.Tracer:
        nonlocal cache
        current_provider = trace.get_tracer_provider()
        if isinstance(current_provider, trace.ProxyTracerProvider):
            return current_provider.get_tracer(module)
        entry = cache
        if entry is not None and entry[0] is current_provider:
            return entry[1]
        tracer = current_provider.get_tracer(module)
        cache = (current_provider, tracer)
        return tracer

    return get_tracer


def _record_span_error(span: trace.Span | None, exc: BaseException) -> None:
    """Record an exception and ERROR status on an active span."""
    if span is None:
        return
    span.record_exception(exc)
    span.set_status(trace.StatusCode.ERROR, str(exc))


async def _step_async_gen(
    gen: Any,
    span: trace.Span | None,
    pending_exc: BaseException | None,
    send_val: Any,
) -> Any:
    if span is None:
        if pending_exc is not None:
            return await gen.athrow(pending_exc)
        return await gen.asend(send_val)
    with trace.use_span(span, end_on_exit=False, record_exception=False, set_status_on_exception=False):
        if pending_exc is not None:
            return await gen.athrow(pending_exc)
        return await gen.asend(send_val)


async def _close_async_gen(gen: Any, span: trace.Span | None) -> None:
    if span is None:
        await gen.aclose()
        return
    try:
        with trace.use_span(span, end_on_exit=False, record_exception=False, set_status_on_exception=False):
            await gen.aclose()
    except Exception as exc:
        _record_span_error(span, exc)
        raise


def _step_sync_gen(
    gen: Any,
    span: trace.Span,
    pending_exc: BaseException | None,
    send_val: Any,
) -> Any:
    with trace.use_span(span, end_on_exit=False, record_exception=False, set_status_on_exception=False):
        if pending_exc is not None:
            return gen.throw(pending_exc)
        return gen.send(send_val)


def _close_sync_gen(gen: Any, span: trace.Span) -> None:
    try:
        with trace.use_span(span, end_on_exit=False, record_exception=False, set_status_on_exception=False):
            gen.close()
    except Exception as exc:
        _record_span_error(span, exc)
        raise


def _wrap_async_gen(
    fn: Callable[..., Any],
    span_name: str,
    attrs: dict[str, Any] | None,
    module: str,
    get_tracer: Callable[[], trace.Tracer],
) -> Callable[..., Any]:
    @functools.wraps(fn)
    async def agen_wrapper(*args: Any, **kwargs: Any) -> Any:
        gen = fn(*args, **kwargs)
        span = get_tracer().start_span(span_name, attributes=attrs) if _module_enabled(module) else None
        pending_exc: BaseException | None = None
        send_val: Any = None
        try:
            while True:
                try:
                    item = await _step_async_gen(gen, span, pending_exc, send_val)
                    pending_exc = None
                except StopAsyncIteration:
                    break
                try:
                    send_val = yield item
                except GeneratorExit:
                    raise
                except BaseException as exc:
                    pending_exc = exc
        except (GeneratorExit, asyncio.CancelledError):
            raise
        except Exception as exc:
            _record_span_error(span, exc)
            raise
        finally:
            try:
                await _close_async_gen(gen, span)
            finally:
                if span is not None:
                    span.end()

    return agen_wrapper


def _wrap_sync_gen(
    fn: Callable[..., Any],
    span_name: str,
    attrs: dict[str, Any] | None,
    module: str,
    get_tracer: Callable[[], trace.Tracer],
) -> Callable[..., Any]:
    @functools.wraps(fn)
    def gen_wrapper(*args: Any, **kwargs: Any) -> Any:
        if not _module_enabled(module):
            return (yield from fn(*args, **kwargs))
        gen = fn(*args, **kwargs)
        span = get_tracer().start_span(span_name, attributes=attrs)
        pending_exc: BaseException | None = None
        send_val: Any = None
        try:
            while True:
                try:
                    item = _step_sync_gen(gen, span, pending_exc, send_val)
                    pending_exc = None
                except StopIteration as stop:
                    return stop.value
                try:
                    send_val = yield item
                except GeneratorExit:
                    raise
                except BaseException as exc:
                    pending_exc = exc
        except GeneratorExit:
            raise
        except Exception as exc:
            _record_span_error(span, exc)
            raise
        finally:
            try:
                _close_sync_gen(gen, span)
            finally:
                span.end()

    return gen_wrapper


def _wrap_async[**P, R](
    fn: Callable[P, R],
    span_name: str,
    attrs: dict[str, Any] | None,
    module: str,
    get_tracer: Callable[[], trace.Tracer],
) -> Callable[P, R]:
    @functools.wraps(fn)
    async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if not _module_enabled(module):
            return await fn(*args, **kwargs)  # type: ignore[misc, no-any-return]
        with get_tracer().start_as_current_span(span_name, attributes=attrs):
            return await fn(*args, **kwargs)  # type: ignore[misc, no-any-return]

    return async_wrapper  # type: ignore[return-value]


def _wrap_sync[**P, R](
    fn: Callable[P, R],
    span_name: str,
    attrs: dict[str, Any] | None,
    module: str,
    get_tracer: Callable[[], trace.Tracer],
) -> Callable[P, R]:
    @functools.wraps(fn)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if not _module_enabled(module):
            return fn(*args, **kwargs)
        with get_tracer().start_as_current_span(span_name, attributes=attrs):
            return fn(*args, **kwargs)

    return sync_wrapper


@overload
def traced[**P, R](func: Callable[P, R]) -> Callable[P, R]: ...
@overload
def traced[**P, R](
    *, name: str | None = None, attrs: dict[str, Any] | None = None
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def traced[**P, R](
    func: Callable[P, R] | None = None,
    *,
    name: str | None = None,
    attrs: dict[str, Any] | None = None,
) -> Any:
    """Wrap a function in an OpenTelemetry span.

    Usable bare (@traced) or parameterized (@traced(name="...", attrs={...})).
    attrs are static attributes set at span start. Per-module gating is
    controlled by set_trace_modules(). Exceptions are recorded on the span
    and re-raised. Without a configured SDK the proxy tracer makes this a
    near-zero-cost no-op.
    """

    def decorate(fn: Callable[P, R]) -> Callable[P, R]:
        span_name = name or f"{fn.__module__}.{fn.__qualname__}"
        module = fn.__module__
        get_tracer = _make_tracer_getter(module)

        if inspect.isasyncgenfunction(fn):
            return _wrap_async_gen(fn, span_name, attrs, module, get_tracer)
        if inspect.isgeneratorfunction(fn):
            return _wrap_sync_gen(fn, span_name, attrs, module, get_tracer)
        if inspect.iscoroutinefunction(fn):
            return _wrap_async(fn, span_name, attrs, module, get_tracer)
        return _wrap_sync(fn, span_name, attrs, module, get_tracer)

    return decorate(func) if func is not None else decorate
