import json
import logging

from arlogi import TRACE, get_json_logger, get_logger, setup_logging


def test_module_specific_levels():
    # Setup specific levels for submodules
    setup_logging(level=logging.INFO, module_levels={"app.db": logging.DEBUG, "app.net": TRACE})

    db_logger = get_logger("app.db")
    net_logger = get_logger("app.net")
    root_logger = get_logger("app.other")

    # Directly verify levels
    assert db_logger.isEnabledFor(logging.DEBUG) is True
    assert net_logger.isEnabledFor(TRACE) is True
    assert root_logger.isEnabledFor(logging.DEBUG) is False
    assert root_logger.isEnabledFor(logging.INFO) is True


def test_json_logger(capsys):
    # Dedicated JSON logger should output to its own handler
    json_logger = get_json_logger("test_json")
    json_logger.info("json message", extra={"key": "value"})

    captured = capsys.readouterr()
    # Since get_json_logger creates a logger with JSONHandler directed to stdout by default (in our implementation it's a StreamHandler)
    # let's verify if we can catch the output.
    # Actually JSONHandler uses sys.stderr by default if stream is None, but let's check.
    # Our implementation: class JSONHandler(logging.StreamHandler): def __init__(self, stream: Any = None): super().__init__(stream)
    # StreamHandler defaults to sys.stderr.

    output = captured.err
    assert "json message" in output
    data = json.loads(output)
    assert data["message"] == "json message"
    assert data["level"] == "INFO"
    assert data["key"] == "value"


def test_trace_stacklevel(caplog):
    caplog.set_level(TRACE)
    logger = get_logger("test_stack")
    logger.trace("trace message")

    record = caplog.records[0]
    # Check if funcName is correct (it should be test_trace_stacklevel, not trace)
    assert record.funcName == "test_trace_stacklevel"


def test_caller_attribution(caplog):
    caplog.set_level(logging.DEBUG)
    logger = get_logger("test.attribution")

    def inner_func():
        logger.info("message", caller_depth=0)

    def outer_func():
        inner_func()
        logger.info("outer message", caller_depth=1)

    inner_func()
    assert "message" in caplog.text
    assert "[inner_func()]" in caplog.text
    assert r"\[inner_func()]" not in caplog.text

    caplog.clear()
    outer_func()
    assert "[inner_func()]" in caplog.text
    assert "[from .test_caller_attribution()]" in caplog.text


def test_colored_console_handler_markup_disabled_by_default():
    from io import StringIO

    from rich.console import Console

    from arlogi.handlers import ColoredConsoleHandler

    buf = StringIO()
    console = Console(file=buf, force_terminal=False, no_color=True, width=120)
    handler = ColoredConsoleHandler(console=console, show_path=False, show_level=False)
    assert handler.markup is False

    record = logging.LogRecord("test", logging.INFO, "test.py", 1, "[bold red]injected[/bold red]", (), None)
    handler.emit(record)
    assert "[bold red]injected[/bold red]" in buf.getvalue()

    buf_opt_in = StringIO()
    console_opt_in = Console(file=buf_opt_in, force_terminal=False, no_color=True, width=120)
    handler_opt_in = ColoredConsoleHandler(console=console_opt_in, markup=True, show_path=False, show_level=False)
    assert handler_opt_in.markup is True
    handler_opt_in.emit(record)
    assert "[bold red]" not in buf_opt_in.getvalue()
    assert "injected" in buf_opt_in.getvalue()


def test_exception_fatal_and_explicit_stacklevel_attribution(caplog):
    caplog.set_level(TRACE)
    logger = get_logger("test.callsite")

    def user_exc_fn():
        try:
            raise ValueError("boom")
        except ValueError:
            logger.exception("caught", caller_depth=0)

    def user_fatal_fn():
        logger.fatal("halting", caller_depth=0)

    def helper_wrapper():
        logger.info("from helper", stacklevel=2)

    def outer_caller():
        helper_wrapper()

    user_exc_fn()
    user_fatal_fn()
    outer_caller()

    exc_rec, fatal_rec, helper_rec = caplog.records
    assert exc_rec.funcName == "user_exc_fn"
    assert "[user_exc_fn()]" in exc_rec.message
    assert r"\[" not in exc_rec.message
    assert fatal_rec.funcName == "user_fatal_fn"
    assert "[user_fatal_fn()]" in fatal_rec.message
    assert helper_rec.funcName == "outer_caller"


def test_extra_dict_not_mutated_and_disabled_level_skips_processing(caplog):
    from types import MappingProxyType

    logger = get_logger("test.extra_immutability")
    logger.setLevel(logging.INFO)

    shared_ctx = {"request_id": "r1"}
    logger.trace("ignored", extra=shared_ctx, caller_depth=1, secret="x")
    assert shared_ctx == {"request_id": "r1"}

    caplog.set_level(logging.INFO, logger="test.extra_immutability")
    logger.info("auth", extra=shared_ctx, user_id=42)
    assert shared_ctx == {"request_id": "r1"}
    assert caplog.records[-1].request_id == "r1"  # type: ignore[attr-defined]
    assert caplog.records[-1].user_id == 42  # type: ignore[attr-defined]

    ro = MappingProxyType({"tenant": "acme"})
    logger.info("ro", extra=ro, action="sync")
    assert caplog.records[-1].tenant == "acme"  # type: ignore[attr-defined]
    assert caplog.records[-1].action == "sync"  # type: ignore[attr-defined]

    logger.info("none_extra", extra=None, k="v")
    assert not hasattr(caplog.records[-1], "_original_extra")
    assert caplog.records[-1].k == "v"  # type: ignore[attr-defined]


def test_caller_attribution_renders_without_backslash_on_console_and_json(tmp_path):
    from io import StringIO

    from rich.console import Console

    from arlogi import cleanup_json_logger
    from arlogi.handlers import ColoredConsoleHandler

    log_file = tmp_path / "attr.jsonl"
    jlog = get_json_logger("attr_json", str(log_file))

    def emit_with_attr():
        jlog.info("hello", caller_depth=0)

    emit_with_attr()
    cleanup_json_logger("attr_json")
    payload = json.loads(log_file.read_text(encoding="utf-8").strip())
    assert payload["message"] == "hello\n[emit_with_attr()]"

    buf = StringIO()
    console = Console(file=buf, force_terminal=False, no_color=True, width=120)
    handler = ColoredConsoleHandler(console=console, markup=True, show_path=False, show_level=False)
    rec = logging.LogRecord("t", logging.INFO, "t.py", 1, "hello\n[emit_with_attr()]", (), None)
    rec._arlogi_attribution = "emit_with_attr()"
    handler.emit(rec)
    assert "[emit_with_attr()]" in buf.getvalue()
    assert r"\[emit_with_attr()]" not in buf.getvalue()
