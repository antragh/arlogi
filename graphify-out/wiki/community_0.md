# Core Factory & Handler Infrastructure

**Community ID:** 0  
**Cohesion Score:** 0.10  
**Total Nodes:** 68

## Source Files

- [](../../src/arlogi/config.py) - 6 nodes
- [](../../src/arlogi/factory.py) - 30 nodes
- [](../../src/arlogi/handler_factory.py) - 9 nodes
- [](../../src/arlogi/handlers.py) - 10 nodes
- [](../../tests/test_resource_management.py) - 13 nodes

## Nodes in this Community

### From 

- **LoggingConfig**
- **.resolve_module_level()**
- **.to_dict()**
- **Resolve a module level to an integer. Args: name: Module na**
- **Convert configuration to a dictionary. Returns: Dictionary**
- **Immutable configuration for arlogi logging setup. Attributes: level**

### From 

- **Factory for creating logger instances with caller attribution support. This mod**
- **Log a message with TRACE level (below DEBUG). Args: msg: Th**
- **Log a warning message.**
- **Log an error message.**
- **Log a critical message.**
- **Log an exception with traceback.**
- **Log a message at the specified level.**
- **Factory for creating and configuring logger instances. This factory manages**
- **Custom logger class with trace() and caller attribution support. This logge**
- **Centralized logging setup for arlogi. This method configures the root l**
- **Apply a LoggingConfig to the root logger. Args: config: The**
- **Register the custom TRACE level with Python's logging module.**
- **Configure the root logger level. Args: config: The logging**
- **Clear existing handlers and add configured ones. Args: conf**
- **Apply module-specific log level overrides. Args: config: Th**
- **Find the name of the module and function at the specified depth. Args:**
- **Detect if running under a test runner. Returns: True if pyt**
- **Get a logger instance conforming to LoggerProtocol. Auto-initializes wi**
- **Get a logger that only outputs to JSON, bypassing root handlers. Args:**
- **Get a logger that only outputs to Syslog, bypassing root handlers. Args**
- **Clean up handlers for a JSON logger to free resources. This method clos**
- **Clean up handlers for a syslog logger to free resources. Args:**
- **Get or initialize the global logger instance. Returns: The**
- **Set up arlogi logging with the specified configuration. This is a convenien**
- **Get a logger instance with caller attribution support. Args: name:**
- **Get a dedicated JSON-only logger. Args: name: Logger name suffix**
- **Get a dedicated syslog-only logger. Args: name: Logger name suffix**
- **Clean up handlers for a JSON logger to free resources. This function closes**
- **Clean up handlers for a syslog logger to free resources. Args: name**
- **Process caller attribution and move arbitrary kwargs to 'extra'. Args:**

### From 

- **HandlerFactory**
- **Handler factory for creating logging handlers. This module provides a centraliz**
- **Create a syslog handler. Args: config: Logging configuratio**
- **Create all handlers based on configuration. This is the main factory me**
- **Factory for creating logging handlers. This class encapsulates the creation**
- **Create a colored console handler. Args: config: Logging con**
- **Create a JSON stream handler (outputs to stderr). Returns:**
- **Create a JSON file handler. Args: config: Logging configura**
- **Create the appropriate JSON handler based on configuration. Creates eit**

### From 

- **handlers.py**
- **ArlogiSyslogHandler**
- **JSONFileHandler**
- **JSONHandler**
- **.close()**
- **Logging handlers for arlogi. This module provides custom logging handlers inclu**
- **A logging handler that outputs log records as JSON to a stream. Defaults to**
- **Close the handler and the stream if we own it. Only closes custom strea**
- **A logging handler that outputs log records as JSON to a file. Automatically**
- **A robust syslog handler with standard formatting and automatic fallback. Fe**

### From 

- **Test that JSONHandler doesn't close system streams.**
- **Test ColoredConsoleHandler's project root caching.**
- **Test that project root detection is cached.**
- **Test that cache persists across multiple handler creations.**
- **Skip all tests in this class if psutil is not available.**
- **Test JSONHandler's stream management.**
- **Test that JSONHandler closes custom streams.**
- **TestJSONHandlerResourceManagement**
- **.test_json_handler_custom_stream_closed()**
- **.test_json_handler_system_stream_not_closed()**
- **TestProjectRootCaching**
- **.test_project_root_cache_persists()**
- **.test_project_root_is_cached()**

