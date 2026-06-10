# Handler Implementation & Resource Management

**Community ID:** 1  
**Cohesion Score:** 0.06  
**Total Nodes:** 58

## Source Files

- [](../../src/arlogi/handlers.py) - 22 nodes
- [](../../tests/test_resource_management.py) - 35 nodes

## Nodes in this Community

### From 

- **.__init__()**
- **ColoredConsoleHandler**
- **._find_project_root()**
- **.get_level_text()**
- **.__init__()**
- **.render()**
- **.render_message()**
- **.__init__()**
- **JSONFormatter**
- **.format()**
- **.__init__()**
- **Override render method to show relative paths from project root. Args:**
- **Get level text as a single character with styling. Args: re**
- **Render message text with level-specific styling. Args: reco**
- **JSON formatter for structured log output. Outputs log records as JSON with**
- **A logging handler that uses rich for colored console output. Features:**
- **Format log record as JSON. Args: record: The log record to**
- **Initialize the JSON stream handler. Args: stream: The strea**
- **Initialize the JSON file handler. Args: filename: Path to t**
- **Initialize the syslog handler. Args: address: Syslog server**
- **Initialize the colored console handler. Args: show_time: Wh**
- **Find the project root by looking for common indicators. Searches upward**

### From 

- **test_resource_management.py**
- **check_psutil()**
- **Resource management tests for arlogi. This module tests that handlers properly**
- **Test JSONFileHandler's file management.**
- **Test that JSONFileHandler creates parent directories.**
- **Test that multiple handler instances don't leak file handles.**
- **Test JSONFormatter's error handling.**
- **Test that JSONFormatter handles objects that can't be serialized.**
- **Test that handlers are properly closed and removed.**
- **Test that JSONFormatter works for normal cases.**
- **Test that multiple configuration changes don't leak resources.**
- **Test that _clear_and_add_handlers closes existing handlers.**
- **Test that multiple setup() calls don't leak handlers.**
- **Test that reconfiguring JSON loggers doesn't leak.**
- **Tests that detect actual resource leaks (requires psutil).**
- **Test that creating/destroying loggers doesn't leak file descriptors.**
- **Test that creating/destroying file loggers doesn't leak file descriptors.**
- **Test that get_json_logger closes previous handlers before adding new ones.**
- **Test that get_syslog_logger closes previous handlers before adding new ones.**
- **TestHandlerCleanup**
- **.test_clear_and_add_handlers_closes_existing()**
- **.test_get_json_logger_closes_previous_handlers()**
- **.test_get_syslog_logger_closes_previous_handlers()**
- **TestJSONFileHandlerResourceManagement**
- **.test_json_file_handler_creates_directories()**
- **.test_json_file_handler_no_duplicate_file_handles()**
- **TestJSONFormatterErrorHandling**
- **.test_json_formatter_handles_normal_cases()**
- **.test_json_formatter_handles_unserializable_objects()**
- **TestMultipleConfigurationChanges**
- **.test_json_logger_reconfiguration()**
- **.test_multiple_setup_calls()**
- **TestResourceLeakDetection**
- **.test_no_file_descriptor_leaks()**
- **.test_no_file_descriptor_leaks_with_files()**

