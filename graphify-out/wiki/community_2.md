# Thread Safety Tests

**Community ID:** 2  
**Cohesion Score:** 0.08  
**Total Nodes:** 43

## Source Files

- [](../../src/arlogi/factory.py) - 1 nodes
- [](../../tests/test_thread_safety.py) - 42 nodes

## Nodes in this Community

### From 

- **LoggerFactory**

### From 

- **test_thread_safety.py**
- **Thread safety tests for arlogi. This module tests that the library is thread-sa**
- **Test concurrent logger creation.**
- **Test creating many loggers concurrently with different names.**
- **Test concurrent JSON logger creation.**
- **Test concurrent logger creation with different levels.**
- **Test thread safety of TRACE level registration.**
- **Test that concurrent TRACE registration is safe.**
- **Test that multiple TRACE registrations are safe.**
- **Test concurrent logging operations.**
- **Test concurrent logging to the same logger instance.**
- **Test concurrent logging with extra fields.**
- **Test concurrent initialization of the logging system.**
- **Test concurrent logging at different levels.**
- **Test concurrent directory creation in JSON file handlers.**
- **Test that concurrent setup() calls don't duplicate handlers.**
- **Test concurrent JSON file handlers creating the same directory.**
- **Stress tests with high concurrency.**
- **Stress test with high concurrency.**
- **Test rapid initialization and logging cycles.**
- **Test that concurrent get_logger() calls initialize successfully.**
- **Test that concurrent get_global_logger() calls are thread-safe.**
- **TestConcurrentDirectoryCreation**
- **.test_concurrent_json_file_handler_same_directory()**
- **TestConcurrentInitialization**
- **.test_concurrent_get_global_logger()**
- **.test_concurrent_get_logger_initializes_once()**
- **.test_concurrent_setup_does_not_duplicate_handlers()**
- **TestConcurrentLoggerCreation**
- **.test_concurrent_json_logger_creation()**
- **.test_concurrent_logger_creation_with_names()**
- **.test_concurrent_logger_with_levels()**
- **TestConcurrentLogging**
- **.test_concurrent_logging_at_different_levels()**
- **.test_concurrent_logging_to_same_logger()**
- **.test_concurrent_logging_with_extra_fields()**
- **TestStressTest**
- **.test_high_concurrency_stress()**
- **.test_rapid_initialization_and_logging()**
- **TestTraceRegistrationThreadSafety**
- **.test_concurrent_trace_registration()**
- **.test_trace_idempotency()**

