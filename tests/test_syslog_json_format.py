"""Unit tests for syslog_format configuration, SyslogJSONFormatter, and syslog handler lifecycle."""

import json
import logging
import logging.handlers
import os
import sys
from unittest.mock import patch

import pytest

from arlogi import (
    HandlerFactory,
    LoggerFactory,
    LoggingConfig,
    LoggingConfigBuilder,
    cleanup_syslog_logger,
    get_syslog_logger,
    setup_logging,
)
from arlogi.config import VALID_SYSLOG_FORMATS, validate_syslog_format
from arlogi.handlers import ArlogiSyslogHandler, SyslogJSONFormatter


def _fake_syslog_init(self, address="/dev/log", facility=logging.handlers.SysLogHandler.LOG_USER, socktype=None):
    logging.Handler.__init__(self)
    self.address = address
    self.facility = facility
    self.socktype = socktype
    self.socket = None


def _make_record(
    name: str = "app.security",
    level: int = logging.INFO,
    msg: str = "user login",
    exc_info: tuple | None = None,
) -> logging.LogRecord:
    return logging.LogRecord(
        name=name,
        level=level,
        pathname="auth.py",
        lineno=42,
        msg=msg,
        args=(),
        exc_info=exc_info,
    )


class TestSyslogFormatConfig:
    """Tests for LoggingConfig, LoggingConfigBuilder, and setup_logging syslog_format."""

    def test_default_syslog_format_parity(self):
        cfg = LoggingConfig()
        built = LoggingConfigBuilder().build()

        assert cfg.syslog_format == "text"
        assert built.syslog_format == "text"
        assert built == cfg
        assert VALID_SYSLOG_FORMATS == frozenset({"text", "json"})

    def test_builder_and_setup_configure_json_syslog(self):
        built = LoggingConfigBuilder().with_syslog(address=("syslog.example.com", 514), syslog_format="json").build()
        assert built.use_syslog is True
        assert built.syslog_address == ("syslog.example.com", 514)
        assert built.syslog_format == "json"

        captured: list[LoggingConfig] = []
        with patch.object(LoggerFactory, "_apply_configuration", side_effect=lambda c: captured.append(c)):
            setup_logging(use_syslog=True, syslog_format="json")

        assert len(captured) == 1
        assert captured[0].use_syslog is True
        assert captured[0].syslog_format == "json"

    @pytest.mark.parametrize(
        "invalid_format",
        ["jsonl", "JSON", "Text", "", None, True, False, 123, ["json"], {"format": "json"}],
    )
    @pytest.mark.parametrize("use_syslog", [False, True])
    def test_invalid_syslog_format_rejected_eagerly(self, invalid_format, use_syslog):
        with pytest.raises(ValueError, match="Invalid syslog_format"):
            LoggingConfig(use_syslog=use_syslog, syslog_format=invalid_format)

        with pytest.raises(ValueError, match="Invalid syslog_format"):
            validate_syslog_format(invalid_format)

    @pytest.mark.parametrize("syslog_format", ["text", "json"])
    def test_setup_rejects_simultaneous_config_and_syslog_format(self, syslog_format):
        cfg = LoggingConfigBuilder().with_syslog(syslog_format="json").build()

        with pytest.raises(ValueError, match="syslog_format"):
            setup_logging(config=cfg, syslog_format=syslog_format)

        with pytest.raises(ValueError, match="syslog_format"):
            LoggerFactory.setup(config=cfg, syslog_format=syslog_format)


class TestSyslogJSONFormatter:
    """Tests for SyslogJSONFormatter wire formatting and JSONFormatter inheritance."""

    def test_formats_text_and_json_modes(self):
        with patch("logging.handlers.SysLogHandler.__init__", new=_fake_syslog_init):
            text_handler = ArlogiSyslogHandler(address=("localhost", 514), syslog_format="text")
            json_handler = ArlogiSyslogHandler(address=("localhost", 514), syslog_format="json")

        try:
            assert text_handler.syslog_format == "text"
            assert json_handler.syslog_format == "json"
            assert isinstance(json_handler.formatter, SyslogJSONFormatter)

            record = _make_record(msg="authenticated")
            record.user_id = 42
            record.level = "FAKE"
            record.trace_id = "0123456789abcdef0123456789abcdef"
            record.span_id = "0123456789abcdef"

            text_out = text_handler.format(record)
            assert text_out == f"app.security[{os.getpid()}]: INFO: authenticated"

            json_out = json_handler.format(record)
            prefix = f"app.security[{os.getpid()}]: "
            assert json_out.startswith(prefix)
            assert "\n" not in json_out

            payload = json.loads(json_out[len(prefix) :])
            assert payload["level"] == "INFO"
            assert payload["logger_name"] == "app.security"
            assert payload["message"] == "authenticated"
            assert payload["user_id"] == 42
            assert payload["trace_id"] == "0123456789abcdef0123456789abcdef"
            assert payload["span_id"] == "0123456789abcdef"
            assert payload["extra"] == {"level": "FAKE"}
        finally:
            text_handler.close()
            json_handler.close()

    def test_escapes_multiline_messages_and_tracebacks_to_single_line(self):
        formatter = SyslogJSONFormatter()
        try:
            raise RuntimeError("line1\nline2")
        except RuntimeError:
            exc_info = sys.exc_info()

        record = _make_record(msg="first line\nsecond line", exc_info=exc_info)
        formatted = formatter.format(record)

        assert "\n" not in formatted
        assert "\r" not in formatted

        prefix = f"app.security[{os.getpid()}]: "
        assert formatted.startswith(prefix)
        payload = json.loads(formatted[len(prefix) :])
        assert payload["message"] == "first line\nsecond line"
        assert "RuntimeError: line1\nline2" in payload["exception"]

    def test_resilient_fallback_json_when_str_raises(self):
        formatter = SyslogJSONFormatter()

        class BadRepr:
            def __str__(self) -> str:
                raise ValueError("cannot stringify")

        record = _make_record(msg="resilient test")
        record.bad_attr = BadRepr()

        formatted = formatter.format(record)
        prefix = f"app.security[{os.getpid()}]: "
        assert formatted.startswith(prefix)
        payload = json.loads(formatted[len(prefix) :])
        assert payload["level"] == "INFO"
        assert payload["logger_name"] == "app.security"
        assert payload["message"] == "resilient test"
        assert "JSON serialization failed" in payload["error"]


class TestArlogiSyslogHandlerAndLifecycle:
    """Tests for pre-socket validation, fallback formatting, HandlerFactory, and get_syslog_logger."""

    @pytest.mark.parametrize(
        ("address", "bad_format"),
        [
            ("/dev/log", "jsonl"),
            (("localhost", 514), "JSON"),
            ("/dev/log", None),
            (("localhost", 514), True),
        ],
    )
    def test_invalid_syslog_format_fails_before_socket_creation(self, address, bad_format):
        with (
            patch("os.path.exists") as mock_exists,
            patch("logging.handlers.SysLogHandler.__init__") as mock_syslog_init,
        ):
            with pytest.raises(ValueError, match="Invalid syslog_format"):
                ArlogiSyslogHandler(address=address, syslog_format=bad_format)

        mock_exists.assert_not_called()
        mock_syslog_init.assert_not_called()

    def test_preserves_syslog_json_formatter_on_dev_log_missing_fallback(self):
        with (
            patch("os.path.exists", return_value=False),
            patch("logging.handlers.SysLogHandler.__init__", autospec=True, side_effect=_fake_syslog_init) as mock_init,
        ):
            handler = ArlogiSyslogHandler(address="/dev/log", syslog_format="json")

        try:
            mock_init.assert_called_once_with(
                handler,
                address=("localhost", 514),
                facility=logging.handlers.SysLogHandler.LOG_USER,
                socktype=None,
            )
            assert handler._failed is False
            assert handler.syslog_format == "json"
            assert isinstance(handler.formatter, SyslogJSONFormatter)
        finally:
            handler.close()

    def test_preserves_syslog_json_formatter_on_dev_log_connect_error_fallback(self):
        def _fail_first(self, address="/dev/log", facility=logging.handlers.SysLogHandler.LOG_USER, socktype=None):
            if address == "/dev/log":
                raise OSError("refused")
            _fake_syslog_init(self, address=address, facility=facility, socktype=socktype)

        with (
            patch("os.path.exists", return_value=True),
            patch("logging.handlers.SysLogHandler.__init__", autospec=True, side_effect=_fail_first) as mock_init,
        ):
            handler = ArlogiSyslogHandler(address="/dev/log", syslog_format="json")

        try:
            assert mock_init.call_count == 2
            assert handler._failed is False
            assert handler.syslog_format == "json"
            assert isinstance(handler.formatter, SyslogJSONFormatter)
        finally:
            handler.close()

    def test_preserves_syslog_json_formatter_when_all_fallbacks_fail(self):
        with (
            patch("os.path.exists", return_value=False),
            patch("logging.handlers.SysLogHandler.__init__", side_effect=OSError("no syslog")),
        ):
            handler = ArlogiSyslogHandler(address="/dev/log", syslog_format="json")

        try:
            assert handler._failed is True
            assert handler.socket is None
            assert handler.syslog_format == "json"
            assert isinstance(handler.formatter, SyslogJSONFormatter)
        finally:
            handler.close()

    def test_handler_factory_forwards_syslog_format(self):
        cfg = LoggingConfig(use_syslog=True, syslog_address=("localhost", 514), syslog_format="json")
        with patch("logging.handlers.SysLogHandler.__init__", new=_fake_syslog_init):
            handler = HandlerFactory.create_syslog(cfg)

        try:
            assert handler.syslog_format == "json"
            assert isinstance(handler.formatter, SyslogJSONFormatter)
        finally:
            handler.close()

    def test_get_syslog_logger_json_end_to_end_and_caller_depth(self):
        name = "security_json_e2e"
        emitted: list[str] = []

        def _capture_emit(self, record):
            emitted.append(self.format(record))

        try:
            with (
                patch("logging.handlers.SysLogHandler.__init__", new=_fake_syslog_init),
                patch.object(logging.handlers.SysLogHandler, "emit", _capture_emit),
            ):
                logger = get_syslog_logger(name, syslog_format="json")

                def _helper_log():
                    logger.warning("Failed login", user_id=42, caller_depth=1)

                _helper_log()

            assert len(emitted) == 1
            assert "\n" not in emitted[0]
            prefix = f"arlogi.syslog.{name}[{os.getpid()}]: "
            assert emitted[0].startswith(prefix)
            payload = json.loads(emitted[0][len(prefix) :])
            assert payload["level"] == "WARNING"
            assert payload["logger_name"] == f"arlogi.syslog.{name}"
            assert payload["message"].startswith("Failed login")
            assert "test_get_syslog_logger_json_end_to_end_and_caller_depth" in payload["message"]
            assert payload["user_id"] == 42
        finally:
            cleanup_syslog_logger(name)

    def test_get_syslog_logger_preserves_existing_handler_on_invalid_format(self):
        name = "security_atomic"
        try:
            with patch("logging.handlers.SysLogHandler.__init__", new=_fake_syslog_init):
                logger = get_syslog_logger(name, syslog_format="text")

            raw_logger = logging.getLogger(f"arlogi.syslog.{name}")
            assert len(raw_logger.handlers) == 1
            original_handler = raw_logger.handlers[0]
            assert isinstance(original_handler, ArlogiSyslogHandler)
            assert original_handler.syslog_format == "text"

            with patch.object(original_handler, "close", wraps=original_handler.close) as mock_close:
                with pytest.raises(ValueError, match="Invalid syslog_format"):
                    LoggerFactory.get_syslog_logger(name, syslog_format="invalid")

            mock_close.assert_not_called()
            assert raw_logger.handlers == [original_handler]
            assert original_handler.syslog_format == "text"
            assert logger is raw_logger
        finally:
            cleanup_syslog_logger(name)

    def test_trace_level_maps_to_syslog_debug_priority(self):
        from arlogi import TRACE

        with patch("logging.handlers.SysLogHandler.__init__", new=_fake_syslog_init):
            text_handler = ArlogiSyslogHandler(address=("localhost", 514), syslog_format="text")
            json_handler = ArlogiSyslogHandler(address=("localhost", 514), syslog_format="json")

        try:
            assert text_handler.mapPriority("TRACE") == "debug"
            assert json_handler.mapPriority("TRACE") == "debug"
            assert text_handler.encodePriority(text_handler.facility, text_handler.mapPriority("TRACE")) == (
                logging.handlers.SysLogHandler.LOG_USER * 8 + 7
            )
            record = _make_record(level=TRACE, msg="trace detail")
            record.levelname = "TRACE"
            assert text_handler.format(record).endswith("TRACE: trace detail")
            assert '"level": "TRACE"' in json_handler.format(record)
        finally:
            text_handler.close()
            json_handler.close()

    def test_stale_dev_log_socket_falls_back_to_udp_and_transport_oserror_degrades_cleanly(self, capsys):
        import socket as stdlib_socket
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory(dir="/tmp", prefix="arl_") as short_tmp:
            stale_sock_path = Path(short_tmp) / "dev_log.sock"
            srv = stdlib_socket.socket(stdlib_socket.AF_UNIX, stdlib_socket.SOCK_DGRAM)
            srv.bind(str(stale_sock_path))
            srv.close()

            # Custom stale Unix socket path fails fast with OSError
            with pytest.raises(OSError):
                ArlogiSyslogHandler(address=str(stale_sock_path))

            # Stale /dev/log path falls back cleanly to ("localhost", 514)
            real_exists = os.path.exists

            def _exists_dev_log(path):
                if path == "/dev/log":
                    return True
                return real_exists(path)

            real_connect_unix = logging.handlers.SysLogHandler._connect_unixsocket

            def _connect_stale(self, address):
                if address == "/dev/log":
                    return real_connect_unix(self, str(stale_sock_path))
                return real_connect_unix(self, address)

            with (
                patch("os.path.exists", side_effect=_exists_dev_log),
                patch.object(logging.handlers.SysLogHandler, "_connect_unixsocket", _connect_stale),
            ):
                handler = ArlogiSyslogHandler(address="/dev/log", syslog_format="json")

        try:
            assert handler.address == ("localhost", 514)
            assert handler._failed is False
            assert handler.socket is not None
            real_sock = handler.socket

            class _FailingUdpSock:
                def sendto(self, *args, **kwargs):
                    raise OSError("Network is unreachable")

                def fileno(self):
                    return real_sock.fileno()

                def close(self):
                    real_sock.close()

            handler.socket = _FailingUdpSock()  # type: ignore[assignment]
            record = _make_record(msg="udp unreachable")
            handler.emit(record)
            handler.emit(record)

            assert handler._failed is True
            assert handler.socket is None
            assert real_sock.fileno() == -1
            assert capsys.readouterr().err == ""
        finally:
            handler.close()
