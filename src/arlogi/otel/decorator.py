"""@traced decorator for sync and async functions."""

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
        tracer = trace.get_tracer(fn.__module__)
        module = fn.__module__

        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                if not _module_enabled(module):
                    return await fn(*args, **kwargs)  # type: ignore[no-any-return]
                with tracer.start_as_current_span(span_name, attributes=attrs):
                    return await fn(*args, **kwargs)  # type: ignore[no-any-return]

            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(fn)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if not _module_enabled(module):
                return fn(*args, **kwargs)
            with tracer.start_as_current_span(span_name, attributes=attrs):
                return fn(*args, **kwargs)

        return sync_wrapper

    return decorate(func) if func is not None else decorate
