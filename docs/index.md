# `arlogi` library documentation

This documentation provides comprehensive coverage of the arlogi logging library with a special focus on the unique caller attribution feature that allows developers to trace log calls across function boundaries using the `from_` parameters.

## Quick Start

- **Installation and basic usage**: Get started with arlogi quickly
- **Caller Attribution Feature**: Learn about the unique `from_` parameters

## Documentation

### 1. **Main Developer Guide** ([DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md))

- **Quick Start**: Installation and basic usage
- **Caller Attribution Feature**: Comprehensive explanation of `from_=0`, `from_caller=1`, and `**{"from": 2}` parameters
- **Global Configuration**: `setup_logging()` and the modern `LoggingConfig` pattern
- **Logger Types**: Standard, JSON-only, and syslog loggers
- **Advanced Usage**: Structured logging, exception handling, log levels
- **Testing Integration**: Test mode detection and pytest integration
- **Migration Guide**: How to migrate from standard logging
- **Common Patterns**: Real-world usage patterns

### 2. **API Reference** ([API_REFERENCE.md](API_REFERENCE.md))

- **Factory Functions**: Complete parameter documentation for `get_logger()`, `get_json_logger()`, etc.
- **Logger Methods**: All logging methods with caller attribution parameters
- **Caller Attribution Parameters**: Detailed explanation of `from_`, `from_caller`, and `**{"from": depth}` syntax
- **Depth Values**: Complete table explaining what each depth value means
- **Handler Types**: All handler classes and their configuration options
- **Type Safety**: LoggerProtocol and function signatures
- **Performance Considerations**: Optimizations and best practices

### 3. **Caller Attribution Examples** ([CALLER_ATTRIBUTION_EXAMPLES.md](CALLER_ATTRIBUTION_EXAMPLES.md))

- **Basic Examples**: `from_=0` (current function) and `from_=1` (caller function)
- **Parameter Syntaxes**: All three ways to specify caller attribution
- **Parameter Precedence**: How multiple caller parameters interact
- **Cross-Module Attribution**: Same vs different module calling
- **Real-World Examples**: Web API handlers, database operations, background jobs
- **Performance Considerations**: Efficient usage patterns
- **Testing Examples**: Unit tests with caller attribution

### 4. **Configuration Guide** ([CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md))

- **Global Configuration**: `setup_logging()` and `LoggingConfig` architecture
- **Per-Module Configuration**: Module-level log level overrides
- **Handler Configuration**: Console, JSON file, and syslog configuration
- **Application Structure**: Microservice, web app, and CLI configurations
- **Environment-Specific**: Development, testing, staging, production configs
- **Dynamic Configuration**: Runtime adjustments and environment variables
- **Advanced Handlers**: Multiple JSON files, custom formatters, filtering
- **Performance Optimization**: High-performance configurations

### 5. **User Guide** ([USER_GUIDE.md](USER_GUIDE.md))

- **Getting Started**: Basic usage and setup
- **Advanced Features**: Deep dive into arlogi capabilities

### 6. **Architecture** ([ARCHITECTURE.md](ARCHITECTURE.md))

- **System Design**: High-level architecture and design decisions
- **Component Overview**: Detailed breakdown of library components

## API Reference

### Core Components

- **Config**: [reference/arlogi/config.md](reference/arlogi/config.md)
- **Factory**: [reference/arlogi/factory.md](reference/arlogi/factory.md)
- **Handler Factory**: [reference/arlogi/handler_factory.md](reference/arlogi/handler_factory.md)
- **Handlers**: [reference/arlogi/handlers.md](reference/arlogi/handlers.md)
- **Levels**: [reference/arlogi/levels.md](reference/arlogi/levels.md)
- **Types**: [reference/arlogi/types.md](reference/arlogi/types.md)

## Key Features Documented

✅ **`from_=0` Parameter**: Shows current function name in logs
✅ **`from_=1` Parameter**: Shows immediate caller function
✅ **`**{"from": depth}` Syntax**: Alternative syntax with dictionary
✅ **`from_caller` Parameter**: Alternative parameter name
✅ **Parameter Precedence**: How multiple caller parameters are resolved
✅ **Stack Frame Analysis**: Depth values and cross-module attribution
✅ **Performance Considerations**: Minimal overhead patterns
✅ **Real-World Usage\*\*: Practical application examples

## Additional Resources

- **Developer Guide**: [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - For contributors
