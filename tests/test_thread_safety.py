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
from unittest.mock import patch

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

    def test_concurrent_get_logger_calls_setup_once(self):
        """Verify that double-checked locking calls setup exactly once across concurrent threads."""
        setup_calls = 0
        original_setup = LoggerFactory.setup

        def wrapped_setup(*args, **kwargs):
            nonlocal setup_calls
            time.sleep(0.01)  # Expand window to expose race if lock missing
            setup_calls += 1
            original_setup(*args, **kwargs)

        LoggerFactory._initialized = False
        try:
            with patch.object(LoggerFactory, "setup", side_effect=wrapped_setup):
                with ThreadPoolExecutor(max_workers=30) as executor:
                    futures = [executor.submit(LoggerFactory.get_logger, f"test_race_{i}") for i in range(60)]
                    for future in as_completed(futures):
                        future.result()
            assert setup_calls == 1, f"setup was called {setup_calls} times instead of 1"
        finally:
            LoggerFactory._initialized = True

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

    def test_concurrent_same_name_json_logger_reconfiguration_and_emission(self):
        from arlogi import cleanup_json_logger, rotate_json_logger

        with tempfile.TemporaryDirectory() as tmpdir:
            errors = []

            def worker(idx: int) -> None:
                try:
                    path = os.path.join(tmpdir, f"shared_{idx % 3}.jsonl")
                    logger = get_json_logger("same_name_race", path)
                    logger.info("concurrent event", worker=idx)
                    rotate_json_logger("same_name_race")
                except Exception as exc:
                    errors.append(exc)

            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(worker, i) for i in range(60)]
                for f in as_completed(futures):
                    f.result()

            assert not errors
            raw_logger = logging.getLogger("arlogi.json.same_name_race")
            assert len(raw_logger.handlers) == 1
            cleanup_json_logger("same_name_race")
            assert len(raw_logger.handlers) == 0

    def test_concurrent_dedicated_reconfiguration_has_no_last_resort_leak(self):
        import sys

        from arlogi import cleanup_json_logger

        class _CountingHandler(logging.Handler):
            def __init__(self) -> None:
                super().__init__()
                self.count = 0
                self.lock = threading.Lock()

            def emit(self, record: logging.LogRecord) -> None:
                with self.lock:
                    self.count += 1

        last_resort_spy = _CountingHandler()
        orig_interval = sys.getswitchinterval()
        sys.setswitchinterval(1e-6)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                path = os.path.join(tmpdir, "audit.jsonl")
                logger = get_json_logger("audit_window", path)
                stop = threading.Event()
                errors: list[Exception] = []

                def emitter() -> None:
                    try:
                        for i in range(200):
                            logger.warning(f"warn-{i}")
                    except Exception as exc:
                        errors.append(exc)

                def reconfigurator() -> None:
                    try:
                        while not stop.is_set():
                            get_json_logger("audit_window", path)
                    except Exception as exc:
                        errors.append(exc)

                with patch.object(logging, "lastResort", last_resort_spy):
                    t_emit = threading.Thread(target=emitter)
                    t_reconf = threading.Thread(target=reconfigurator)
                    t_reconf.start()
                    t_emit.start()
                    t_emit.join()
                    stop.set()
                    t_reconf.join()

                assert not errors
                assert last_resort_spy.count == 0
                cleanup_json_logger("audit_window")
        finally:
            sys.setswitchinterval(orig_interval)

    def test_concurrent_syslog_logger_swap_does_not_reopen_closed_sockets(self):
        import gc
        import sys
        import warnings

        from arlogi import cleanup_syslog_logger, get_syslog_logger

        orig_interval = sys.getswitchinterval()
        sys.setswitchinterval(1e-6)
        try:
            logger = get_syslog_logger("syslog_race", address=("127.0.0.1", 5140))
            stop = threading.Event()
            errors: list[Exception] = []

            def emitter() -> None:
                try:
                    for i in range(150):
                        logger.info(f"msg-{i}")
                except Exception as exc:
                    errors.append(exc)

            def reconfigurator() -> None:
                try:
                    while not stop.is_set():
                        get_syslog_logger("syslog_race", address=("127.0.0.1", 5140))
                except Exception as exc:
                    errors.append(exc)

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ResourceWarning)
                t_emit = threading.Thread(target=emitter)
                t_reconf = threading.Thread(target=reconfigurator)
                t_reconf.start()
                t_emit.start()
                t_emit.join()
                stop.set()
                t_reconf.join()
                cleanup_syslog_logger("syslog_race")
                gc.collect()

            assert not errors
            assert not any(issubclass(w.category, ResourceWarning) for w in caught)
        finally:
            sys.setswitchinterval(orig_interval)

    def test_concurrent_root_swap_delivers_to_all_handlers(self):
        import sys

        root = logging.getLogger()
        orig_root_handlers = root.handlers[:]
        orig_interval = sys.getswitchinterval()
        per_record_hits: list[int] = []
        hits_lock = threading.Lock()

        class _TrackedHandler(logging.Handler):
            def __init__(self) -> None:
                super().__init__()
                self.count = 0

            def emit(self, record: logging.LogRecord) -> None:
                with hits_lock:
                    self.count += 1
                    record._hit_count = getattr(record, "_hit_count", 0) + 1  # type: ignore[attr-defined]

        stop_root = threading.Event()
        root_errors: list[Exception] = []

        def root_emitter() -> None:
            try:
                for i in range(200):
                    rec = root.makeRecord("root.swap", logging.WARNING, __file__, 1, f"m-{i}", (), None)
                    root.handle(rec)
                    per_record_hits.append(getattr(rec, "_hit_count", 0))
            except Exception as exc:
                root_errors.append(exc)

        def root_swapper() -> None:
            try:
                while not stop_root.is_set():
                    LoggerFactory._swap_handlers(root, [_TrackedHandler(), _TrackedHandler(), _TrackedHandler()])
            except Exception as exc:
                root_errors.append(exc)

        sys.setswitchinterval(1e-6)
        try:
            LoggerFactory._swap_handlers(root, [_TrackedHandler(), _TrackedHandler(), _TrackedHandler()])
            last_resort_spy = _TrackedHandler()
            with patch.object(logging, "lastResort", last_resort_spy):
                t1 = threading.Thread(target=root_emitter)
                t2 = threading.Thread(target=root_swapper)
                t2.start()
                t1.start()
                t1.join()
                stop_root.set()
                t2.join()
            assert last_resort_spy.count == 0
            assert not root_errors
            assert per_record_hits and all(h == 3 for h in per_record_hits)
        finally:
            LoggerFactory._swap_handlers(root, orig_root_handlers)
            sys.setswitchinterval(orig_interval)

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
