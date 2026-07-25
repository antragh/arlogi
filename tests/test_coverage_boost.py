"""Additional unit tests to achieve high test coverage across arlogi modules."""

import logging
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from arlogi.config import LoggingConfig
from arlogi.config_builder import LoggingConfigBuilder
from arlogi.factory import (
    LoggerFactory,
    cleanup_syslog_logger,
    get_syslog_logger,
)
from arlogi.handler_factory import HandlerFactory
from arlogi.handlers import (
    ArlogiSyslogHandler,
    ColoredConsoleHandler,
    JSONFileHandler,
)
from arlogi.levels import register_trace_level


class TestHandlerFactoryCoverage:
    """Test all methods in HandlerFactory."""

    def test_create_json_stream(self):
        handler = HandlerFactory.create_json_stream()
        assert handler is not None

    def test_create_json_file_without_name_raises(self):
        config = LoggingConfig()
        with pytest.raises(ValueError, match="json_file_name must be set"):
            HandlerFactory.create_json_file(config)

    def test_create_json_file_with_name(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl") as f:
            config = LoggingConfig(json_file_name=f.name)
            handler = HandlerFactory.create_json_file(config)
            assert isinstance(handler, JSONFileHandler)

    def test_create_json_handler_stream_vs_file(self):
        config_stream = LoggingConfig(json_file_only=True)
        h_stream = HandlerFactory.create_json_handler(config_stream)
        assert not isinstance(h_stream, JSONFileHandler)

        with tempfile.NamedTemporaryFile(suffix=".jsonl") as f:
            config_file = LoggingConfig(json_file_name=f.name)
            h_file = HandlerFactory.create_json_handler(config_file)
            assert isinstance(h_file, JSONFileHandler)

    def test_create_syslog(self):
        config = LoggingConfig(use_syslog=True, syslog_address="/dev/log")
        handler = HandlerFactory.create_syslog(config)
        assert isinstance(handler, ArlogiSyslogHandler)

    def test_create_handlers_all_options(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl") as f:
            config = LoggingConfig(
                json_file_name=f.name,
                use_syslog=True,
                json_file_only=False,
            )
            handlers = HandlerFactory.create_handlers(config)
            assert len(handlers) == 3

    def test_create_handlers_json_stream_fallback(self):
        config = LoggingConfig(
            json_file_only=True,
            json_file_name=None,
        )
        handlers = HandlerFactory.create_handlers(config)
        assert len(handlers) == 1


class TestConfigBuilderCoverage:
    """Test all builder methods in LoggingConfigBuilder."""

    def test_builder_methods(self):
        builder = (
            LoggingConfigBuilder()
            .with_level("DEBUG")
            .with_module_levels({"foo.bar": "TRACE"})
            .with_json_file("app.jsonl", console_also=False)
            .with_syslog(address="/dev/log")
            .with_console_format(show_time=True, show_level=False, show_path=False)
            .with_rotation("month", retention_count=5)
        )
        config = builder.build()
        assert config.level == "DEBUG"
        assert config.module_levels == {"foo.bar": "TRACE"}
        assert config.json_file_name == "app.jsonl"
        assert config.json_file_only is True
        assert config.use_syslog is True
        assert config.syslog_address == "/dev/log"
        assert config.show_time is True
        assert config.show_level is False
        assert config.show_path is False
        assert config.rotate_schedule == "month"
        assert config.rotate_retention_count == 5

    def test_builder_json_console_only(self):
        builder = LoggingConfigBuilder().with_json_console_only()
        config = builder.build()
        assert config.json_file_only is True


class TestLevelsCoverage:
    """Test TRACE level registration and execution covering all 8 branches in levels.py."""

    def test_register_trace_level_fast_path(self):
        with patch("arlogi.levels._trace_registered", True):
            register_trace_level()

    def test_register_trace_level_double_checked_lock_true_branch(self):
        with patch("arlogi.levels._trace_registered", False):
            lock_mock = MagicMock()

            def enter_lock(*args, **kwargs):
                import arlogi.levels

                arlogi.levels._trace_registered = True

            lock_mock.__enter__ = enter_lock
            lock_mock.__exit__ = MagicMock(return_value=False)
            with patch("arlogi.levels._trace_lock", lock_mock):
                register_trace_level()

    def test_register_trace_level_hasattr_true_branch(self):
        with patch("arlogi.levels._trace_registered", False):
            with patch.object(logging, "TRACE", 5, create=True):
                register_trace_level()

    def test_register_trace_level_full_execution_and_trace_method(self):
        with patch("arlogi.levels._trace_registered", False):
            had_trace = hasattr(logging, "TRACE")
            old_trace_val = getattr(logging, "TRACE", None)
            old_logger_trace = getattr(logging.Logger, "trace", None)
            if had_trace:
                delattr(logging, "TRACE")
            try:
                register_trace_level()

                raw_logger = logging.Logger("test_raw_logger_full")

                # 1. Disabled trace call (if isEnabledFor(5) is False)
                with patch.object(raw_logger, "isEnabledFor", return_value=False):
                    logging.Logger.trace(raw_logger, "disabled trace message")  # type: ignore

                # 2. Enabled trace call (if isEnabledFor(5) is True)
                with patch.object(raw_logger, "isEnabledFor", return_value=True):
                    with patch.object(raw_logger, "_log") as mock_log:
                        logging.Logger.trace(raw_logger, "enabled trace message", "arg1", kw="kw1")  # type: ignore
                        mock_log.assert_called_once_with(5, "enabled trace message", ("arg1",), kw="kw1")

            finally:
                if had_trace and old_trace_val is not None:
                    logging.TRACE = old_trace_val  # type: ignore
                if old_logger_trace is not None:
                    logging.Logger.trace = old_logger_trace  # type: ignore


class TestSyslogLoggerAndCleanupCoverage:
    """Test get_syslog_logger and cleanup_syslog_logger."""

    def test_get_and_cleanup_syslog_logger(self):
        logger = get_syslog_logger("test_sec", address="/dev/log")
        assert logger is not None

        # Verify cleanup removes handlers
        cleanup_syslog_logger("test_sec")
        syslog_sys_logger = logging.getLogger("arlogi.syslog.test_sec")
        assert len(syslog_sys_logger.handlers) == 0

    def test_arlogi_syslog_handler_fallback(self):
        # Trigger fallback by passing invalid socket path
        handler = ArlogiSyslogHandler(address="/nonexistent_socket_path_12345")
        assert handler is not None

    def test_arlogi_syslog_handler_raises_on_non_dev_log_error(self):
        with pytest.raises(OSError):
            ArlogiSyslogHandler(address=("invalid_host_that_does_not_exist_9999", 99999))


class TestHandlersCoverageEdgeCases:
    """Test ColoredConsoleHandler and JSONFileHandler edge cases."""

    def test_colored_console_handler_custom_styles(self):
        handler = ColoredConsoleHandler(level_styles={"info": "bold green"})
        assert handler.level_styles["info"] == "bold green"

    def test_colored_console_handler_root_fallback(self):
        with patch.object(ColoredConsoleHandler, "_project_root_cache", None):
            with patch("os.path.exists", return_value=False):
                handler = ColoredConsoleHandler()
                assert handler.project_root == os.getcwd()

    def test_colored_console_handler_render_relpath_error(self):
        handler = ColoredConsoleHandler()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/some/path/file.py",
            lineno=10,
            msg="test msg",
            args=(),
            exc_info=None,
        )
        with patch("os.path.relpath", side_effect=ValueError("Different drives")):
            renderable = handler.render(record=record, traceback=None, message_renderable="test msg")
            assert renderable is not None

    def test_json_file_handler_month_schedule(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl") as f:
            handler = JSONFileHandler(f.name, rotate_schedule="month")
            period_key = handler._compute_period_key(handler._now_local())
            assert len(period_key) == 7  # YYYY-MM

    def test_json_file_handler_invalid_schedule(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl") as f:
            with pytest.raises(ValueError, match="Unsupported rotate_schedule"):
                JSONFileHandler(f.name, rotate_schedule="invalid")  # type: ignore

    def test_json_file_handler_collision_safe_path(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl") as f:
            handler = JSONFileHandler(f.name)
            base_target = f.name + ".rotated"
            base_target_1 = f.name + ".rotated.1.rotated"
            # Create base target and first candidate to test suffix increment loop
            with open(base_target, "w") as f1, open(base_target_1, "w") as f2:
                f1.write("data")
                f2.write("data")
            try:
                candidate = handler._build_collision_safe_path(base_target)
                assert candidate != base_target
                assert ".rotated" in candidate
            finally:
                for p in (base_target, base_target_1):
                    if os.path.exists(p):
                        os.remove(p)

    def test_json_file_handler_prune_os_error(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl") as f:
            handler = JSONFileHandler(f.name, rotate_schedule="day", rotate_retention_count=1)
            with patch("glob.glob", return_value=["dummy-1.jsonl", "dummy-2.jsonl"]):
                with patch("os.remove", side_effect=OSError("Permission denied")):
                    # Should not raise exception
                    handler._prune_rotated_files()

    def test_json_file_handler_emit_error_handling(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl") as f:
            handler = JSONFileHandler(f.name)
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="msg",
                args=(),
                exc_info=None,
            )
            with patch.object(handler, "_rotation_key_for_emit", side_effect=RuntimeError("rotation error")):
                mock_handle_error = MagicMock()
                handler.handleError = mock_handle_error
                handler.emit(record)
                mock_handle_error.assert_called_once_with(record)


class TestConfigValidationCoverage:
    """Test LoggingConfig validation paths."""

    def test_config_invalid_level(self):
        with pytest.raises(ValueError, match="Invalid log level"):
            LoggingConfig(level="INVALID_LEVEL_NAME")

        with pytest.raises(ValueError, match="Log level must be int or str"):
            LoggingConfig(level=12.34)  # type: ignore

    def test_config_invalid_module_name(self):
        with pytest.raises(ValueError, match="Invalid module name"):
            LoggingConfig(module_levels={"": "DEBUG"})

    def test_config_invalid_retention(self):
        with pytest.raises(ValueError, match="rotate_retention_count must be >= 1"):
            LoggingConfig(rotate_schedule="day", rotate_retention_count=0)

    def test_config_to_dict_and_resolve(self):
        config = LoggingConfig(level="INFO", json_file_only=True)
        assert config.has_json_output is True
        d = config.to_dict()
        assert d["level"] == "INFO"
        assert config.resolve_module_level("foo", "TRACE") == 5
        assert config.resolve_module_level("foo", "DEBUG") == logging.DEBUG
        assert config.resolve_module_level("foo", logging.WARNING) == logging.WARNING

    def test_config_from_kwargs(self):
        config = LoggingConfig.from_kwargs(
            level="DEBUG",
            rotate_schedule="day",
            rotate_retention_count=3,
        )
        assert config.level == "DEBUG"
        assert config.rotate_schedule == "day"
        assert config.rotate_retention_count == 3

        with pytest.raises(TypeError, match="unknown keyword argument"):
            LoggingConfig.from_kwargs(unknown_setting=123)


class TestFactoryEdgeCases:
    """Test LoggerFactory helper methods and edge cases."""

    def test_caller_attribution_different_module(self):
        logger = LoggerFactory.get_logger("test_caller")
        with patch.object(logger, "_get_caller_info", side_effect=[("modA", "fnA"), ("modB", "fnB")]):
            msg, kwargs = logger._process_params("hello", {"caller_depth": 1})
            assert "[from modB.fnB()]" in str(msg)

    def test_caller_attribution_invalid_depth(self):
        logger = LoggerFactory.get_logger("test_caller")
        msg, kwargs = logger._process_params("hello", {"caller_depth": "invalid_int"})
        assert msg == "hello"

    def test_extra_non_dict(self):
        logger = LoggerFactory.get_logger("test_caller")
        msg, kwargs = logger._process_params("hello", {"extra": "string_extra", "custom_key": "val"})
        assert kwargs["extra"]["_original_extra"] == "string_extra"
        assert kwargs["extra"]["custom_key"] == "val"

    def test_apply_configuration_non_test_mode(self):
        config = LoggingConfig(level="INFO")
        with patch("arlogi.factory.is_test_mode", return_value=False):
            LoggerFactory._apply_configuration(config)

    def test_trace_logger_exception(self):
        logger = LoggerFactory.get_logger("test_exception_logger")
        try:
            raise ValueError("test exception for coverage")
        except ValueError:
            logger.exception("Caught an exception")

    def test_caller_info_exception(self):
        logger = LoggerFactory.get_logger("test_caller_err")
        with patch("sys._getframe", side_effect=ValueError("Depth overflow")):
            mod, fn = logger._get_caller_info(99999)
            assert mod == "unknown"
            assert fn == "unknown"

    def test_caller_attribution_non_string_msg(self):
        logger = LoggerFactory.get_logger("test_non_str")
        msg, kwargs = logger._process_params(12345, {"caller_depth": 0})
        assert "12345" in str(msg)

    def test_caller_attribution_extra_is_dict(self):
        logger = LoggerFactory.get_logger("test_extra_dict")
        msg, kwargs = logger._process_params("msg", {"extra": {"existing": 1}, "custom": 2})
        assert kwargs["extra"] == {"existing": 1, "custom": 2}

    def test_rotate_json_logger_handler_returns_false(self):
        from arlogi.factory import get_json_logger, rotate_json_logger

        with tempfile.NamedTemporaryFile(suffix=".jsonl") as f:
            get_json_logger("rot_false", json_file_name=f.name)
            # Empty file -> rotate_now() returns False
            rotated = rotate_json_logger("rot_false")
            assert rotated == 0


class TestBranchCoverageExtra:
    """Test specific branch coverage conditions across handlers and factory."""

    def test_create_handlers_json_file_only_with_file_name(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl") as f:
            config = LoggingConfig(json_file_name=f.name, json_file_only=True)
            handlers = HandlerFactory.create_handlers(config)
            assert len(handlers) == 1
            assert isinstance(handlers[0], JSONFileHandler)

    def test_trace_level_double_checked_lock(self):
        with patch("arlogi.levels._trace_registered", False):

            def fake_lock():
                import arlogi.levels

                arlogi.levels._trace_registered = True
                m = MagicMock()
                m.__enter__ = MagicMock(return_value=True)
                m.__exit__ = MagicMock(return_value=False)
                return m

            with patch("arlogi.levels._trace_lock", fake_lock()):
                register_trace_level()

    def test_raw_logger_trace_method(self):
        register_trace_level()
        raw_logger = logging.Logger("raw_logger_test")
        raw_logger.setLevel(5)
        raw_logger.trace("Trace on raw Logger")

    def test_colored_console_handler_with_custom_console(self):
        from rich.console import Console

        custom_console = Console()
        handler = ColoredConsoleHandler(console=custom_console)
        assert handler.console is custom_console

    def test_json_file_handler_period_key_change(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl") as f:
            f.write(b"data\n")
            f.flush()
            handler = JSONFileHandler(f.name, rotate_schedule="hour")
            handler._active_period_key = "2020-01-01-00"
            key = handler._rotation_key_for_emit()
            assert key is not None

    def test_json_file_handler_rotate_no_schedule_no_active_key(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl") as f:
            f.write(b"data\n")
            f.flush()
            handler = JSONFileHandler(f.name, rotate_schedule=None)
            res = handler._rotate_now_locked()
            assert res is True

    def test_json_file_handler_permission_error(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl") as f:
            f.write(b"data\n")
            f.flush()
            handler = JSONFileHandler(f.name, rotate_schedule="hour")
            with patch("os.replace", side_effect=PermissionError("File locked")):
                res = handler._rotate_now_locked("2026-01-01-00")
                assert res is False

    def test_json_file_handler_generic_exception_on_rotate(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl") as f:
            f.write(b"data\n")
            f.flush()
            handler = JSONFileHandler(f.name, rotate_schedule="hour")
            with patch("os.replace", side_effect=RuntimeError("Disk failure")):
                res = handler._rotate_now_locked("2026-01-01-00")
                assert res is False

    def test_arlogi_syslog_handler_all_fallbacks_fail(self):
        with patch("logging.handlers.SysLogHandler.__init__", side_effect=OSError("No syslog")):
            handler = ArlogiSyslogHandler(address="/dev/log")
            assert handler is not None
