import logging
from typing import Any

TRACE_LEVEL_NUM = 5
TRACE_LEVEL_NAME = "TRACE"

def register_trace_level() -> None:
    """Register the TRACE level with the standard logging module."""
    if hasattr(logging, TRACE_LEVEL_NAME):
        return

    logging.addLevelName(TRACE_LEVEL_NUM, TRACE_LEVEL_NAME)
    setattr(logging, TRACE_LEVEL_NAME, TRACE_LEVEL_NUM)

    def trace(self: logging.Logger, message: str, *args: Any, **kws: Any) -> None:
        """Log a message with TRACE level."""
        if self.isEnabledFor(TRACE_LEVEL_NUM):
            self._log(TRACE_LEVEL_NUM, message, args, **kws)

    logging.Logger.trace = trace  # type: ignore
