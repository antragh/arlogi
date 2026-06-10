# Configuration Management

**Community ID:** 3  
**Cohesion Score:** 0.07  
**Total Nodes:** 43

## Source Files

- [](../../src/arlogi/__init__.py) - 1 nodes
- [](../../src/arlogi/config.py) - 13 nodes
- [](../../src/arlogi/config_builder.py) - 2 nodes
- [](../../src/arlogi/factory.py) - 15 nodes
- [](../../src/arlogi/handler_factory.py) - 7 nodes
- [](../../src/arlogi/levels.py) - 3 nodes
- [](../../src/arlogi/types.py) - 2 nodes

## Nodes in this Community

### From 

- **__init__.py**

### From 

- **config.py**
- **from_kwargs()**
- **get_default_level()**
- **has_json_output()**
- **is_test_mode()**
- **.__post_init__()**
- **Logging configuration dataclass for type-safe setup. This module provides a str**
- **Detect if running under a test runner. Checks for pytest, unittest, or the**
- **Get the default log level based on the current environment. Returns DEBUG i**
- **Validate configuration after initialization.**
- **resolved_level()**
- **show_console()**
- **_validate_level()**

### From 

- **config_builder.py**
- **Builder pattern for LoggingConfig construction. This module provides a fluent b**

### From 

- **factory.py**
- **_apply_configuration()**
- **cleanup_json_logger()**
- **cleanup_syslog_logger()**
- **_clear_and_add_handlers()**
- **_configure_module_levels()**
- **_configure_root_logger()**
- **get_global_logger()**
- **get_json_logger()**
- **get_logger()**
- **get_syslog_logger()**
- **_initialize_trace_level()**
- **is_test_mode()**
- **setup()**
- **setup_logging()**

### From 

- **handler_factory.py**
- **create_console()**
- **create_handlers()**
- **create_json_file()**
- **create_json_handler()**
- **create_json_stream()**
- **create_syslog()**

### From 

- **levels.py**
- **Register the TRACE level with the standard logging module. Thread-safe: Use**
- **register_trace_level()**

### From 

- **types.py**
- **name()**

