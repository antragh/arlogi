import logging
import os
import subprocess
import sys

import pytest

from arlogi import TRACE, LoggerProtocol, get_logger


def test_trace_level_registered():
    logger = get_logger("test_trace")
    assert hasattr(logger, "trace")
    assert logging.getLevelName(TRACE) == "TRACE"


def test_protocol_compliance():
    logger = get_logger("test_protocol")
    assert isinstance(logger, LoggerProtocol)


def test_test_mode_detection():
    from arlogi.factory import LoggerFactory

    assert LoggerFactory.is_test_mode() is True


def test_test_mode_ignores_spoofed_pytest_current_test_in_fresh_process():
    env = dict(os.environ)
    env["PYTEST_CURRENT_TEST"] = "spoofed_test::test_fn"
    code = (
        "import sys; "
        "assert 'pytest' not in sys.modules and 'unittest' not in sys.modules; "
        "from arlogi import is_test_mode, setup_logging; "
        "import logging; "
        "assert is_test_mode() is False; "
        "setup_logging(level='INFO'); "
        "assert len(logging.getLogger().handlers) >= 1"
    )
    proc = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr


def test_public_exports_and_apply_config():
    import pytest

    import arlogi
    from arlogi import LoggerFactory, LoggingConfigBuilder, setup_logging

    assert "LoggingConfigBuilder" in arlogi.__all__
    cfg = LoggingConfigBuilder().with_level("WARNING").build()
    setup_logging(config=cfg)
    assert logging.getLogger().level == logging.WARNING

    cfg2 = LoggingConfigBuilder().with_level("ERROR").build()
    LoggerFactory.apply_config(cfg2)
    assert logging.getLogger().level == logging.ERROR

    with pytest.raises(ValueError, match="Cannot combine 'config'"):
        setup_logging(config=cfg, level="DEBUG")

    with pytest.raises(ValueError, match="Cannot combine 'config'"):
        LoggerFactory.setup(config=cfg, use_syslog=True)


def test_setup_logging_preserves_positional_args_and_rejects_base_dir_without_file(tmp_path):
    from arlogi import get_json_logger, setup_logging

    log_path = tmp_path / "pos.jsonl"
    setup_logging("INFO", None, str(log_path), True)

    with pytest.raises(ValueError, match="base_dir cannot be specified"):
        get_json_logger("no_file", base_dir=str(tmp_path))


def test_logging_calls(caplog):
    caplog.set_level(TRACE)
    logger = get_logger("test_calls")
    logger.trace("trace message")
    logger.debug("debug message")
    logger.info("info message")

    messages = [record.message for record in caplog.records]
    assert "trace message" in messages
    assert "debug message" in messages
    assert "info message" in messages


def test_preexisting_logging_trace_still_completes_registration_and_supports_msg_kwarg():
    code = (
        "import logging; "
        "logging.TRACE = 5; "
        "pre_existing = logging.getLogger('app.worker'); "
        "from arlogi import LoggerProtocol, get_logger; "
        "logger = get_logger('app.worker'); "
        "assert logging.getLevelName(5) == 'TRACE'; "
        "assert hasattr(logger, 'trace'); "
        "assert isinstance(logger, LoggerProtocol); "
        "assert hasattr(pre_existing, 'trace')"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr

    kw_code = (
        "import io, logging; "
        "pre_existing = logging.getLogger('app.kwarg_worker'); "
        "from arlogi import TRACE; "
        "from arlogi.levels import register_trace_level; "
        "register_trace_level(); "
        "buf = io.StringIO(); "
        "h = logging.StreamHandler(buf); "
        "pre_existing.addHandler(h); "
        "pre_existing.setLevel(TRACE); "
        "pre_existing.propagate = False; "
        "pre_existing.trace(msg='kwarg'); "
        "assert 'kwarg' in buf.getvalue()"
    )
    proc2 = subprocess.run([sys.executable, "-c", kw_code], capture_output=True, text=True, check=False)
    assert proc2.returncode == 0, proc2.stderr


@pytest.mark.parametrize(
    "override_kwargs",
    [
        {"level": logging.INFO},
        {"use_syslog": False},
        {"json_file_name": None},
        {"json_file_only": False},
        {"show_time": False},
        {"show_level": True},
        {"show_path": True},
        {"syslog_address": "/dev/log"},
        {"syslog_format": "text"},
        {"rotate_schedule": None},
        {"rotate_retention_count": None},
        {"module_levels": None},
        {"json_file_base_dir": None},
    ],
)
def test_setup_rejects_default_equal_explicit_overrides_with_config(override_kwargs):
    from arlogi import LoggerFactory, LoggingConfigBuilder, setup_logging

    cfg = (
        LoggingConfigBuilder().with_level("DEBUG").with_syslog().with_json_file("app.jsonl", console_also=False).build()
    )
    setup_logging(config=cfg)
    assert logging.getLogger().level == logging.DEBUG

    key = next(iter(override_kwargs))
    with pytest.raises(ValueError, match=key):
        setup_logging(config=cfg, **override_kwargs)
    assert logging.getLogger().level == logging.DEBUG

    with pytest.raises(ValueError, match=key):
        LoggerFactory.setup(config=cfg, **override_kwargs)
    assert logging.getLogger().level == logging.DEBUG

    # Keyword-only defaults without config still apply default INFO level
    setup_logging()
    assert logging.getLogger().level == logging.INFO


def test_get_logger_resolves_case_insensitive_levels_and_rejects_booleans():
    logger_trace = get_logger("test.get_logger_trace", level="trace")
    assert logging.getLogger("test.get_logger_trace").level == TRACE
    assert logger_trace is logging.getLogger("test.get_logger_trace")

    get_logger("test.get_logger_debug", level="debug")
    assert logging.getLogger("test.get_logger_debug").level == logging.DEBUG

    get_logger("test.get_logger_notset_str", level="NOTSET")
    assert logging.getLogger("test.get_logger_notset_str").level == logging.NOTSET

    get_logger("test.get_logger_notset_int", level=logging.NOTSET)
    assert logging.getLogger("test.get_logger_notset_int").level == logging.NOTSET

    target = get_logger("test.get_logger_bool_reject", level="WARNING")
    for bad in (True, False):
        with pytest.raises(ValueError):
            get_logger("test.get_logger_bool_reject", level=bad)
        assert logging.getLogger("test.get_logger_bool_reject").level == logging.WARNING
    assert target is logging.getLogger("test.get_logger_bool_reject")
