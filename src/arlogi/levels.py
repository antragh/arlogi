import logging
import threading
from typing import Any

TRACE_LEVEL_NUM = 5
TRACE_LEVEL_NAME = "TRACE"

# Module-level lock and flag for thread-safe TRACE level registration
_trace_lock = threading.Lock()
_trace_registered = False


def register_trace_level() -> None:
    """Register the TRACE level with the standard logging module.

    Thread-safe: Uses double-checked locking to ensure TRACE level is
    registered only once even when called from multiple threads.

    This function is idempotent - multiple calls are safe and will
    only register the TRACE level once.
    """
    global _trace_registered

    # Fast path - already registered
    if _trace_registered:
        return

    # Thread-safe registration with double-checked locking
    with _trace_lock:
        # Check again inside the lock
        if _trace_registered:
            return

        # Register each TRACE piece independently so partial third-party definitions are repaired.
        if logging.getLevelName(TRACE_LEVEL_NUM) != TRACE_LEVEL_NAME:
            logging.addLevelName(TRACE_LEVEL_NUM, TRACE_LEVEL_NAME)

        if not hasattr(logging, TRACE_LEVEL_NAME):
            setattr(logging, TRACE_LEVEL_NAME, TRACE_LEVEL_NUM)

        if not hasattr(logging.Logger, "trace"):

            def trace(self: logging.Logger, msg: Any, *args: Any, **kws: Any) -> None:
                """Log a message with TRACE level."""
                if self.isEnabledFor(TRACE_LEVEL_NUM):
                    raw_sl = kws.get("stacklevel", 1)
                    kws["stacklevel"] = (raw_sl + 1) if isinstance(raw_sl, int) and not isinstance(raw_sl, bool) else 2
                    self._log(TRACE_LEVEL_NUM, msg, args, **kws)

            logging.Logger.trace = trace  # type: ignore

        _trace_registered = True
