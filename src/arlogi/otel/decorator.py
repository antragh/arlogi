"""@traced decorator for sync and async functions."""

import functools
import inspect
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, overload

from opentelemetry import trace

P = ParamSpec("P")
R = TypeVar("R")


@overload
def traced[**P, R](func: Callable[P, R]) -> Callable[P, R]: ...
@overload
def traced(*, name: str | None = None) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def traced[**P, R](func: Callable[P, R] | None = None, *, name: str | None = None) -> Any:
    """Wrap a function in an OpenTelemetry span.

    Usable bare (@traced) or with a custom span name (@traced(name="...")).
    Exceptions are recorded on the span and re-raised. Without a configured
    SDK the proxy tracer makes this a near-zero-cost no-op.
    """

    def decorate(fn: Callable[P, R]) -> Callable[P, R]:
        span_name = name or f"{fn.__module__}.{fn.__qualname__}"
        tracer = trace.get_tracer(fn.__module__)

        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                with tracer.start_as_current_span(span_name):
                    return await fn(*args, **kwargs)  # type: ignore[no-any-return]

            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(fn)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with tracer.start_as_current_span(span_name):
                return fn(*args, **kwargs)

        return sync_wrapper

    return decorate(func) if func is not None else decorate
