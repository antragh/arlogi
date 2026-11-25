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
