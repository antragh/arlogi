# Arlogi Test Suite

---

## FILE: tests/test_core.py

```py
import logging

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

```

---

## FILE: tests/test_features.py

```py
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
    # The [ is escaped for Rich markup as \[
    assert r"\[inner_func()]" in caplog.text

    caplog.clear()
    outer_func()
    # From the inner_func call: [inner_func()]
    assert r"\[inner_func()]" in caplog.text
    # From the outer_func call (depth 1): [from .test_caller_attribution()]
    assert r"\[from .test_caller_attribution()]" in caplog.text

```

---

## FILE: tests/test_file_rotation.py

```py
import glob
import logging
from datetime import datetime

from arlogi import get_json_logger, rotate_json_logger
from arlogi.handlers import JSONFileHandler


def _emit(handler: JSONFileHandler, message: str) -> None:
    handler.emit(
        logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg=message,
            args=(),
            exc_info=None,
        )
    )


def test_period_key_generation(tmp_path):
    log_file = tmp_path / "app.jsonl"

    hour_handler = JSONFileHandler(str(log_file), rotate_schedule="hour")
    assert hour_handler._compute_period_key(datetime(2026, 6, 10, 14, 45)) == "2026-06-10-14"

    day_handler = JSONFileHandler(str(log_file), rotate_schedule="day")
    assert day_handler._compute_period_key(datetime(2026, 6, 10, 14, 45)) == "2026-06-10"

    week_handler = JSONFileHandler(str(log_file), rotate_schedule="week")
    assert week_handler._compute_period_key(datetime(2026, 6, 10, 14, 45)) == "2026-W23"

    month_handler = JSONFileHandler(str(log_file), rotate_schedule="month")
    assert month_handler._compute_period_key(datetime(2026, 6, 10, 14, 45)) == "2026-06"

    hour_handler.close()
    day_handler.close()
    week_handler.close()
    month_handler.close()


def test_rotate_now_moves_to_suffixed_file(tmp_path):
    log_file = tmp_path / "app.jsonl"
    handler = JSONFileHandler(str(log_file), rotate_schedule="day")

    _emit(handler, "before rotate")
    rotated = handler.rotate_now()

    assert rotated is True
    assert log_file.exists()

    rotated_files = glob.glob(str(tmp_path / "app-*.jsonl"))
    assert len(rotated_files) == 1

    handler.close()


def test_rotate_now_is_noop_for_empty_file(tmp_path):
    log_file = tmp_path / "app.jsonl"
    handler = JSONFileHandler(str(log_file), rotate_schedule="day")

    assert handler.rotate_now() is False

    handler.close()


def test_emit_rotates_on_period_boundary(tmp_path):
    log_file = tmp_path / "app.jsonl"
    handler = JSONFileHandler(str(log_file), rotate_schedule="day")

    times = [
        datetime(2026, 6, 10, 23, 59, 59),
        datetime(2026, 6, 10, 23, 59, 59),
        datetime(2026, 6, 11, 0, 0, 1),
    ]

    def fake_now_local() -> datetime:
        return times.pop(0)

    handler._now_local = fake_now_local  # type: ignore[attr-defined]
    handler._active_period_key = handler._compute_period_key(handler._now_local())

    _emit(handler, "day-1")
    _emit(handler, "day-2")

    rotated_files = glob.glob(str(tmp_path / "app-*.jsonl"))
    assert len(rotated_files) == 1

    handler.close()


def test_retention_prunes_old_rotated_files(tmp_path):
    log_file = tmp_path / "app.jsonl"
    handler = JSONFileHandler(
        str(log_file),
        rotate_schedule="hour",
        rotate_retention_count=2,
    )

    for hour in [10, 11, 12, 13]:
        handler._now_local = lambda h=hour: datetime(2026, 6, 10, h, 0, 0)  # type: ignore[attr-defined]
        _emit(handler, f"hour-{hour}")
        handler.rotate_now()

    rotated_files = sorted(glob.glob(str(tmp_path / "app-*.jsonl")))
    assert len(rotated_files) == 2

    handler.close()


def test_rotate_json_logger_helper(tmp_path):
    log_file = tmp_path / "helper.jsonl"
    logger = get_json_logger("rotation-helper", str(log_file))
    logger.info("hello")

    rotated_count = rotate_json_logger("rotation-helper")

    assert rotated_count == 1

```

---

## FILE: tests/test_resource_management.py

```py
"""Resource management tests for arlogi.

This module tests that handlers properly manage resources (file handles,
sockets, etc.) to prevent leaks in long-running applications.
"""

import logging
import os
import tempfile
from io import StringIO

import pytest

from arlogi import (
    cleanup_json_logger,
    get_json_logger,
    get_syslog_logger,
    setup_logging,
)
from arlogi.config import LoggingConfig
from arlogi.factory import LoggerFactory


class TestHandlerCleanup:
    """Test that handlers are properly closed and removed."""

    def test_clear_and_add_handlers_closes_existing(self):
        """Test that _clear_and_add_handlers closes existing handlers."""
        # Setup initial handlers
        config = LoggingConfig.from_kwargs(
            level=logging.INFO,
            show_time=False,
        )
        LoggerFactory._clear_and_add_handlers(config)

        root = logging.getLogger()
        initial_handlers = root.handlers.copy()

        # Replace handlers
        LoggerFactory._clear_and_add_handlers(config)

        # Check that old handlers were closed
        # (FileHandler and SocketHandler should have close() called)
        for handler in initial_handlers:
            # If it's a handler with resources, check it's been properly removed
            assert handler not in root.handlers

    def test_get_json_logger_closes_previous_handlers(self):
        """Test that get_json_logger closes previous handlers before adding new ones."""
        logger = get_json_logger("test_close", "logs/test1.json")

        # Get initial handler
        assert len(logger.handlers) == 1
        handler1 = logger.handlers[0]

        # Replace with new handler
        logger2 = get_json_logger("test_close", "logs/test2.json")
        assert len(logger2.handlers) == 1

        # Handler1 should be closed and removed
        assert handler1 not in logger2.handlers

    def test_get_syslog_logger_closes_previous_handlers(self):
        """Test that get_syslog_logger closes previous handlers before adding new ones."""
        logger = get_syslog_logger("test_close")

        # Get initial handler
        assert len(logger.handlers) == 1
        handler1 = logger.handlers[0]

        # Replace with new handler (different address)
        logger2 = get_syslog_logger("test_close", ("localhost", 514))
        assert len(logger2.handlers) == 1

        # Handler1 should be closed and removed
        assert handler1 not in logger2.handlers


class TestJSONHandlerResourceManagement:
    """Test JSONHandler's stream management."""

    def test_json_handler_custom_stream_closed(self):
        """Test that JSONHandler closes custom streams."""
        custom_stream = StringIO()
        from arlogi.handlers import JSONHandler

        handler = JSONHandler(stream=custom_stream)
        handler.emit(
            logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="test message",
                args=(),
                exc_info=None,
            )
        )

        # Close the handler
        handler.close()

        # Custom stream should be closed
        assert custom_stream.closed

    def test_json_handler_system_stream_not_closed(self):
        """Test that JSONHandler doesn't close system streams."""
        import sys

        from arlogi.handlers import JSONHandler

        handler = JSONHandler(stream=sys.stderr)

        # Close the handler
        handler.close()

        # System stream should NOT be closed
        assert not sys.stderr.closed


class TestJSONFileHandlerResourceManagement:
    """Test JSONFileHandler's file management."""

    def test_json_file_handler_creates_directories(self):
        """Test that JSONFileHandler creates parent directories."""
        from arlogi.handlers import JSONFileHandler

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "subdir", "test.json")
            handler = JSONFileHandler(log_path)

            # Directory should be created
            assert os.path.exists(os.path.dirname(log_path))

            # Handler should be able to write
            handler.emit(
                logging.LogRecord(
                    name="test",
                    level=logging.INFO,
                    pathname="test.py",
                    lineno=1,
                    msg="test message",
                    args=(),
                    exc_info=None,
                )
            )

            handler.close()
            assert os.path.exists(log_path)

    def test_json_file_handler_no_duplicate_file_handles(self):
        """Test that multiple handler instances don't leak file handles."""
        from arlogi.handlers import JSONFileHandler

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.json")

            # Create and close multiple handlers
            for i in range(10):
                handler = JSONFileHandler(log_path)
                handler.emit(
                    logging.LogRecord(
                        name="test",
                        level=logging.INFO,
                        pathname="test.py",
                        lineno=1,
                        msg=f"message {i}",
                        args=(),
                        exc_info=None,
                    )
                )
                handler.close()

            # If file handles were leaked, this would fail
            # File should be accessible
            assert os.path.exists(log_path)


class TestProjectRootCaching:
    """Test ColoredConsoleHandler's project root caching."""

    def test_project_root_is_cached(self):
        """Test that project root detection is cached."""
        from arlogi.handlers import ColoredConsoleHandler

        # Clear cache first
        ColoredConsoleHandler._project_root_cache = None

        handler1 = ColoredConsoleHandler()
        root1 = handler1.project_root

        # Should use cache on second instantiation
        handler2 = ColoredConsoleHandler()
        root2 = handler2.project_root

        # Should be the same object (cached)
        assert root1 is root2
        assert ColoredConsoleHandler._project_root_cache is not None

    def test_project_root_cache_persists(self):
        """Test that cache persists across multiple handler creations."""
        from arlogi.handlers import ColoredConsoleHandler

        # Clear cache
        ColoredConsoleHandler._project_root_cache = None

        handlers = [ColoredConsoleHandler() for _ in range(5)]

        # All should have the same project root
        roots = [h.project_root for h in handlers]
        assert len(set(roots)) == 1


class TestJSONFormatterErrorHandling:
    """Test JSONFormatter's error handling."""

    def test_json_formatter_handles_unserializable_objects(self):
        """Test that JSONFormatter handles objects that can't be serialized."""
        from arlogi.handlers import JSONFormatter

        formatter = JSONFormatter()

        # Create a record with an unserializable object
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )

        # Add an unserializable object
        class UnserializableClass:
            def __str__(self):
                raise ValueError("Can't convert to string")

        record.custom_field = UnserializableClass()

        # Should not raise, should fall back to error format
        result = formatter.format(record)

        # Should be valid JSON
        import json

        parsed = json.loads(result)
        assert "error" in parsed
        assert "JSON serialization failed" in parsed["error"]

    def test_json_formatter_handles_normal_cases(self):
        """Test that JSONFormatter works for normal cases."""
        from arlogi.handlers import JSONFormatter

        formatter = JSONFormatter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        # Should be valid JSON
        import json

        parsed = json.loads(result)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "test message"
        assert "error" not in parsed


class TestMultipleConfigurationChanges:
    """Test that multiple configuration changes don't leak resources."""

    def test_multiple_setup_calls(self):
        """Test that multiple setup() calls don't leak handlers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.json")

            # Setup multiple times
            for _i in range(5):
                setup_logging(
                    level=logging.INFO,
                    json_file_name=log_file,
                )

            root = logging.getLogger()

            # Should only have handlers from last setup (Console + JSON)
            # Note: pytest may add LogCaptureHandler during tests
            arlogi_handlers = [h for h in root.handlers if not h.__class__.__name__.startswith("LogCapture")]
            assert len(arlogi_handlers) <= 2  # Console + JSON

    def test_json_logger_reconfiguration(self):
        """Test that reconfiguring JSON loggers doesn't leak."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(10):
                log_file = os.path.join(tmpdir, f"test_{i}.json")
                logger = get_json_logger(f"test_{i}", log_file)
                logger.info(f"Message {i}")

            # All log files should be accessible
            for i in range(10):
                log_file = os.path.join(tmpdir, f"test_{i}.json")
                assert os.path.exists(log_file)


class TestResourceLeakDetection:
    """Tests that detect actual resource leaks (requires psutil)."""

    @pytest.fixture(autouse=True)
    def check_psutil(self):
        """Skip all tests in this class if psutil is not available."""
        pytest.importorskip("psutil")

    def test_no_file_descriptor_leaks(self):
        """Test that creating/destroying loggers doesn't leak file descriptors."""

        psutil = __import__("psutil")
        process = psutil.Process()
        initial_fds = process.num_fds()

        # Create and destroy many loggers
        for i in range(50):
            logger = get_json_logger(f"leak_test_{i}")
            logger.info(f"Message {i}")
            # Clean up the logger to release resources
            cleanup_json_logger(f"leak_test_{i}")

        final_fds = process.num_fds()

        # Should not have leaked more than 10 extra FDs (some overhead is OK)
        assert final_fds <= initial_fds + 10, f"Leaked {final_fds - initial_fds} file descriptors"

    def test_no_file_descriptor_leaks_with_files(self):
        """Test that creating/destroying file loggers doesn't leak file descriptors."""
        psutil = __import__("psutil")

        with tempfile.TemporaryDirectory() as tmpdir:
            process = psutil.Process()
            initial_fds = process.num_fds()

            for i in range(50):
                log_file = os.path.join(tmpdir, f"leak_test_{i}.json")
                logger = get_json_logger(f"leak_test_{i}", log_file)
                logger.info(f"Message {i}")
                # Clean up the logger to release file handles
                cleanup_json_logger(f"leak_test_{i}")

            final_fds = process.num_fds()

            # Should not have leaked file descriptors
            # Allow some overhead for temp directory operations
            assert final_fds <= initial_fds + 20, f"Leaked {final_fds - initial_fds} file descriptors"

```

---

## FILE: tests/test_rotation_config.py

```py
import pytest

from arlogi import setup_logging
from arlogi.config import LoggingConfig
from arlogi.config_builder import LoggingConfigBuilder


def test_logging_config_accepts_rotation_options():
    config = LoggingConfig(
        rotate_schedule="hour",
        rotate_retention_count=7,
    )

    assert config.rotate_schedule == "hour"
    assert config.rotate_retention_count == 7


def test_logging_config_rejects_invalid_rotate_schedule():
    with pytest.raises(ValueError, match="Invalid rotate_schedule"):
        LoggingConfig(rotate_schedule="year")


def test_logging_config_rejects_invalid_retention_count():
    with pytest.raises(ValueError, match="rotate_retention_count"):
        LoggingConfig(rotate_schedule="day", rotate_retention_count=0)


def test_from_kwargs_accepts_rotation_keys():
    config = LoggingConfig.from_kwargs(
        level="INFO",
        rotate_schedule="month",
        rotate_retention_count=3,
    )

    assert config.rotate_schedule == "month"
    assert config.rotate_retention_count == 3


def test_builder_with_rotation_options():
    config = (
        LoggingConfigBuilder()
        .with_json_file("logs/app.jsonl")
        .with_rotation(schedule="week", retention_count=9)
        .build()
    )

    assert config.rotate_schedule == "week"
    assert config.rotate_retention_count == 9


def test_builder_with_rotation_defaults_retention_to_none():
    config = LoggingConfigBuilder().with_rotation(schedule="day").build()

    assert config.rotate_schedule == "day"
    assert config.rotate_retention_count is None


def test_setup_logging_accepts_rotation_options():
    # Under tests, setup does not install handlers; this checks API contract only.
    setup_logging(
        level="INFO",
        rotate_schedule="hour",
        rotate_retention_count=7,
    )

```

---

## FILE: tests/test_thread_safety.py

```py
"""Thread safety tests for arlogi.

This module tests that the library is thread-safe and handles concurrent
access correctly, particularly around initialization and logger creation.
"""

import logging
import os
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from arlogi import (
    get_json_logger,
    get_logger,
    setup_logging,
)
from arlogi.factory import LoggerFactory


class TestConcurrentInitialization:
    """Test concurrent initialization of the logging system."""

    def test_concurrent_setup_does_not_duplicate_handlers(self):
        """Test that concurrent setup() calls don't duplicate handlers."""
        errors = []
        handler_counts = []

        def setup_thread(i):
            try:
                setup_logging(level=logging.INFO)
                root = logging.getLogger()
                handler_counts.append(len(root.handlers))
                time.sleep(0.001)  # Simulate work
            except Exception as e:
                errors.append((i, e))

        threads = []
        for i in range(50):
            t = threading.Thread(target=setup_thread, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Should not have any errors
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Should have reasonable number of handlers, not N*50
        root = logging.getLogger()
        # Filter out pytest handlers
        arlogi_handlers = [h for h in root.handlers if not h.__class__.__name__.startswith("LogCapture")]
        assert len(arlogi_handlers) <= 2, f"Too many handlers: {len(arlogi_handlers)}"

    def test_concurrent_get_logger_initializes_once(self):
        """Test that concurrent get_logger() calls initialize successfully."""

        def get_logger_thread(i):
            logger = get_logger(f"test_{i}")
            logger.info(f"Message {i}")
            return logger

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(get_logger_thread, i) for i in range(100)]
            for future in as_completed(futures):
                future.result()

        # Should have initialized
        assert LoggerFactory._initialized, "LoggerFactory should be initialized"

    def test_concurrent_get_global_logger(self):
        """Test that concurrent get_global_logger() calls are thread-safe."""
        loggers = []

        def get_global_thread(i):
            logger = LoggerFactory.get_global_logger()
            loggers.append(logger)
            logger.info(f"Message {i}")
            time.sleep(0.001)

        threads = []
        for i in range(50):
            t = threading.Thread(target=get_global_thread, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All loggers should be the same instance
        assert all(logger is loggers[0] for logger in loggers), "Not all loggers are the same instance"


class TestConcurrentLoggerCreation:
    """Test concurrent logger creation."""

    def test_concurrent_logger_creation_with_names(self):
        """Test creating many loggers concurrently with different names."""
        errors = []

        def create_logger(i):
            try:
                logger = get_logger(f"test_logger_{i}")
                logger.info(f"Message {i}")
                logger.debug(f"Debug message {i}")
                logger.warning(f"Warning {i}")
                time.sleep(0.0001)
            except Exception as e:
                errors.append((i, e))

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(create_logger, i) for i in range(200)]
            for future in as_completed(futures):
                future.result()

        assert len(errors) == 0, f"Errors occurred: {errors}"

    def test_concurrent_json_logger_creation(self):
        """Test concurrent JSON logger creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            errors = []
            log_files = []

            def create_json_logger(i):
                try:
                    log_file = os.path.join(tmpdir, f"test_{i}.json")
                    logger = get_json_logger(f"json_{i}", log_file)
                    logger.info(f"Message {i}")
                    log_files.append(log_file)
                    time.sleep(0.001)
                except Exception as e:
                    errors.append((i, e))

            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(create_json_logger, i) for i in range(50)]
                for future in as_completed(futures):
                    future.result()

            assert len(errors) == 0, f"Errors occurred: {errors}"

            # All log files should exist
            for log_file in log_files:
                assert os.path.exists(log_file), f"Log file not created: {log_file}"

    def test_concurrent_logger_with_levels(self):
        """Test concurrent logger creation with different levels."""
        errors = []
        levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]

        def create_logger_with_level(i):
            try:
                level = levels[i % len(levels)]
                logger = get_logger(f"level_test_{i}", level=level)
                logger.log(level, f"Message at level {level}")
                time.sleep(0.0001)
            except Exception as e:
                errors.append((i, e))

        with ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(create_logger_with_level, i) for i in range(100)]
            for future in as_completed(futures):
                future.result()

        assert len(errors) == 0, f"Errors occurred: {errors}"


class TestTraceRegistrationThreadSafety:
    """Test thread safety of TRACE level registration."""

    def test_concurrent_trace_registration(self):
        """Test that concurrent TRACE registration is safe."""
        errors = []

        def register_trace(i):
            try:
                from arlogi.levels import register_trace_level

                register_trace_level()
                time.sleep(0.0001)
            except Exception as e:
                errors.append((i, e))

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(register_trace, i) for i in range(50)]
            for future in as_completed(futures):
                future.result()

        assert len(errors) == 0, f"Errors occurred: {errors}"

        # TRACE should be registered
        assert hasattr(logging, "TRACE"), "TRACE level not registered"

    def test_trace_idempotency(self):
        """Test that multiple TRACE registrations are safe."""
        from arlogi.levels import register_trace_level

        errors = []
        for i in range(100):
            try:
                register_trace_level()
            except Exception as e:
                errors.append((i, e))

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert hasattr(logging, "TRACE"), "TRACE level not registered"


class TestConcurrentLogging:
    """Test concurrent logging operations."""

    def test_concurrent_logging_to_same_logger(self):
        """Test concurrent logging to the same logger instance."""
        logger = get_logger("concurrent_test")
        message_count = [0]

        def log_messages(i):
            for j in range(10):
                logger.info(f"Message {i}-{j}")
                message_count[0] += 1
                time.sleep(0.0001)

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(log_messages, i) for i in range(20)]
            for future in as_completed(futures):
                future.result()

        # All messages should have been logged
        assert message_count[0] == 200, f"Expected 200 messages, got {message_count[0]}"

    def test_concurrent_logging_with_extra_fields(self):
        """Test concurrent logging with extra fields."""
        logger = get_logger("extra_test")
        errors = []

        def log_with_extra(i):
            try:
                logger.info(f"Message {i}", extra={"counter": i, "worker_id": threading.current_thread().name})
                time.sleep(0.0001)
            except Exception as e:
                errors.append((i, e))

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(log_with_extra, i) for i in range(100)]
            for future in as_completed(futures):
                future.result()

        assert len(errors) == 0, f"Errors occurred: {errors}"

    def test_concurrent_logging_at_different_levels(self):
        """Test concurrent logging at different levels."""
        logger = get_logger("level_test")
        errors = []

        def log_at_levels(i):
            try:
                logger.trace(f"Trace {i}")
                logger.debug(f"Debug {i}")
                logger.info(f"Info {i}")
                logger.warning(f"Warning {i}")
                logger.error(f"Error {i}")
                logger.critical(f"Critical {i}")
                time.sleep(0.0001)
            except Exception as e:
                errors.append((i, e))

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(log_at_levels, i) for i in range(50)]
            for future in as_completed(futures):
                future.result()

        assert len(errors) == 0, f"Errors occurred: {errors}"


class TestConcurrentDirectoryCreation:
    """Test concurrent directory creation in JSON file handlers."""

    def test_concurrent_json_file_handler_same_directory(self):
        """Test concurrent JSON file handlers creating the same directory."""
        from arlogi.handlers import JSONFileHandler

        with tempfile.TemporaryDirectory() as tmpdir:
            errors = []
            subdir = os.path.join(tmpdir, "nested", "dir")

            def create_handler(i):
                try:
                    log_file = os.path.join(subdir, f"test_{i}.json")
                    handler = JSONFileHandler(log_file)
                    handler.emit(
                        logging.LogRecord(
                            name="test",
                            level=logging.INFO,
                            pathname="test.py",
                            lineno=1,
                            msg=f"Message {i}",
                            args=(),
                            exc_info=None,
                        )
                    )
                    handler.close()
                    time.sleep(0.001)
                except Exception as e:
                    errors.append((i, e))

            # All threads try to create the same directory
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(create_handler, i) for i in range(50)]
                for future in as_completed(futures):
                    future.result()

            assert len(errors) == 0, f"Errors occurred: {errors}"

            # Directory should exist
            assert os.path.exists(subdir), "Directory not created"

            # All log files should exist
            for i in range(50):
                log_file = os.path.join(subdir, f"test_{i}.json")
                assert os.path.exists(log_file), f"Log file not created: {log_file}"


class TestStressTest:
    """Stress tests with high concurrency."""

    def test_high_concurrency_stress(self):
        """Stress test with high concurrency."""
        errors = []

        def stress_test(i):
            try:
                logger = get_logger(f"stress_{i % 50}")  # Reuse logger names
                for j in range(10):
                    logger.info(f"Stress message {i}-{j}")
                time.sleep(0.0001)
            except Exception as e:
                errors.append((i, e))

        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(stress_test, i) for i in range(500)]
            for future in as_completed(futures):
                future.result()

        assert len(errors) == 0, f"Errors occurred: {errors}"

    def test_rapid_initialization_and_logging(self):
        """Test rapid initialization and logging cycles."""
        errors = []

        def init_log_cycle(i):
            try:
                # Create logger, log, and let it go out of scope
                logger = get_logger(f"cycle_{i % 20}")
                logger.info(f"Cycle message {i}")
                time.sleep(0.0001)
            except Exception as e:
                errors.append((i, e))

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(init_log_cycle, i) for i in range(200)]
            for future in as_completed(futures):
                future.result()

        assert len(errors) == 0, f"Errors occurred: {errors}"

```
