# Graph Report - .  (2026-06-10)

## Corpus Check
- 20 files · ~85,954 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 432 nodes · 1137 edges · 33 communities detected
- Extraction: 40% EXTRACTED · 60% INFERRED · 0% AMBIGUOUS · INFERRED: 681 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `LoggerFactory` - 128 edges
2. `JSONFileHandler` - 114 edges
3. `LoggerProtocol` - 110 edges
4. `LoggingConfig` - 90 edges
5. `JSONHandler` - 77 edges
6. `LoggingConfigBuilder` - 74 edges
7. `ColoredConsoleHandler` - 48 edges
8. `ArlogiSyslogHandler` - 45 edges
9. `HandlerFactory` - 40 edges
10. `JSONFormatter` - 36 edges

## Surprising Connections (you probably didn't know these)
- `TestHandlerCleanup` --uses--> `LoggerFactory`  [INFERRED]
  tests/test_resource_management.py → src/arlogi/factory.py
- `TestJSONHandlerResourceManagement` --uses--> `LoggerFactory`  [INFERRED]
  tests/test_resource_management.py → src/arlogi/factory.py
- `TestJSONFileHandlerResourceManagement` --uses--> `LoggerFactory`  [INFERRED]
  tests/test_resource_management.py → src/arlogi/factory.py
- `TestProjectRootCaching` --uses--> `LoggerFactory`  [INFERRED]
  tests/test_resource_management.py → src/arlogi/factory.py
- `TestJSONFormatterErrorHandling` --uses--> `LoggerFactory`  [INFERRED]
  tests/test_resource_management.py → src/arlogi/factory.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.08
Nodes (85): LoggingConfig, Immutable configuration for arlogi logging setup.      Attributes:         level, Factory for creating logger instances with caller attribution support.  This mod, Log a message with TRACE level (below DEBUG).          Args:             msg: Th, Log a warning message., Log an error message., Log a critical message., Log an exception with traceback. (+77 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (31): Builder pattern for LoggingConfig construction.  This module provides a fluent b, get_default_level(), is_test_mode(), Logging configuration dataclass for type-safe setup.  This module provides a str, Detect if running under a test runner.      Checks for pytest, unittest, or the, Get the default log level based on the current environment.      Returns DEBUG i, Validate configuration after initialization., _validate_level() (+23 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (28): LoggerFactory, Thread safety tests for arlogi.  This module tests that the library is thread-sa, Test creating many loggers concurrently with different names., Test concurrent JSON logger creation., Test concurrent logger creation with different levels., Test thread safety of TRACE level registration., Test that concurrent TRACE registration is safe., Test that multiple TRACE registrations are safe. (+20 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (17): Initialize the JSON stream handler.          Args:             stream: The strea, Close the handler and the stream if we own it.          Only closes custom strea, Initialize the JSON file handler.          Args:             filename: Path to t, Get current local datetime.          This indirection keeps schedule checks test, Compute the period key for the configured schedule., Build target path for a rotated file., Return a unique rotated path by appending numeric suffixes when needed., Prune old rotated files based on retention count. (+9 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (7): Integration tests for real-world usage scenarios., Test complete logging workflow from setup to usage., Test module-level logging overrides., TestIntegrationScenarios, Protocol, LoggerProtocol, Protocol defining the interface for the arlogi logger.

### Community 5 - "Community 5"
Cohesion: 0.1
Nodes (11): LoggingConfigBuilder, Enable syslog output.          Args:             address: Syslog server address, Builder for creating LoggingConfig instances with fluent API.      This builder, Configure console output format.          Args:             show_time: Show time, Configure optional time-window file rotation.          Args:             schedul, Build the LoggingConfig instance.          Returns:             A validated Logg, Initialize builder with sensible defaults., Set the global log level.          Args:             level: Log level (e.g., "IN (+3 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (10): Tests for LoggingConfigBuilder pattern., Test basic builder usage., Test method chaining in builder., Test builder with json_file_only via console_also parameter., Test builder with both JSON file and console., Test builder with JSON console output only., Test builder with module level overrides., Test builder with custom syslog address. (+2 more)

### Community 7 - "Community 7"
Cohesion: 0.17
Nodes (7): Tests for consistent logger naming patterns., Test that logger names get arlogi. prefix., Test that existing prefix is not duplicated., Test that global logger uses consistent naming., Test that JSON loggers have consistent prefix., Test that syslog loggers have consistent prefix., TestLoggerNamingConsistency

### Community 8 - "Community 8"
Cohesion: 0.17
Nodes (7): Tests for caller_depth parameter and deprecation warnings., Test that new caller_depth parameter works., Test that from_caller parameter triggers deprecation warning., Test that from_ parameter triggers deprecation warning., Test that 'from' in dict triggers deprecation warning., Test that caller_depth doesn't trigger warning., TestCallerDepthDeprecation

### Community 9 - "Community 9"
Cohesion: 0.35
Nodes (1): TraceLogger

### Community 10 - "Community 10"
Cohesion: 0.2
Nodes (6): Comprehensive tests for refactored arlogi code.  Tests cover all critical fixes,, Tests for from_kwargs() validation improvements., Test that unknown parameters raise TypeError., Test that error message includes valid parameter names., Test that all valid parameters work correctly., TestFromKwargsValidation

### Community 11 - "Community 11"
Cohesion: 0.2
Nodes (6): Tests for backward compatibility with old API., Test that old from_caller parameter still works., Test that old from_ parameter still works., Test that old 'from' in dict still works., Test that legacy setup_logging() function still works., TestBackwardCompatibility

### Community 12 - "Community 12"
Cohesion: 0.2
Nodes (6): Tests for SRP compliance in refactored code., Test that _extract_caller_depth can be tested independently., Test that _format_caller_attribution can be tested independently., Test that _add_attribution_to_message can be tested independently., Test that _process_extra_kwargs can be tested independently., TestSingleResponsibilityPrinciple

### Community 13 - "Community 13"
Cohesion: 0.2
Nodes (6): Tests for TRACE level string validation fix., Test that TRACE level string is accepted., Test that lowercase 'trace' is accepted., Test that TRACE is mentioned in validation error., Test that standard logging levels still work., TestTRACEValidation

### Community 14 - "Community 14"
Cohesion: 0.31
Nodes (8): create_markdown(), create_nav_menu_yaml(), extract_classes_and_functions(), main(), Extracts class and function names from a given Python file., Creates a Markdown file containing the API reference for the given Python module, Prints a YAML-friendly navigation structure., Main function to generate reference documentation.

### Community 15 - "Community 15"
Cohesion: 0.25
Nodes (0): 

### Community 16 - "Community 16"
Cohesion: 0.36
Nodes (4): _emit(), test_emit_rotates_on_period_boundary(), test_retention_prunes_old_rotated_files(), test_rotate_now_moves_to_suffixed_file()

### Community 17 - "Community 17"
Cohesion: 0.25
Nodes (5): Tests for type safety improvements., Test that logger complies with LoggerProtocol., Test that all protocol methods are implemented., Test that name property exists and returns string., TestTypeSafety

### Community 18 - "Community 18"
Cohesion: 0.25
Nodes (5): Tests for critical bug fixes., Test that fatal() method exists on logger., Test that fatal() method can be called without error., Test that fatal() logs at CRITICAL level., TestCriticalFixes

### Community 19 - "Community 19"
Cohesion: 0.4
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 0.4
Nodes (0): 

### Community 21 - "Community 21"
Cohesion: 0.5
Nodes (0): 

### Community 22 - "Community 22"
Cohesion: 0.5
Nodes (2): Override render method to show relative paths from project root.          Args:, Get level text as a single character with styling.          Args:             re

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (1): Format log record as JSON.          Args:             record: The log record to

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (1): Render message text with level-specific styling.          Args:             reco

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (1): Resolve a module level to an integer.          Args:             name: Module na

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (1): Convert configuration to a dictionary.          Returns:             Dictionary

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (1): Validate a log level value.          Args:             level: Log level as int o

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (1): Get the global level as an integer.          Returns:             The resolved l

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (1): Determine if console output should be shown.          Returns:             True

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (1): Determine if JSON output is configured.          Returns:             True if JS

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (1): Create LoggingConfig from keyword arguments.          This factory method provid

## Knowledge Gaps
- **45 isolated node(s):** `Extracts class and function names from a given Python file.`, `Creates a Markdown file containing the API reference for the given Python module`, `Prints a YAML-friendly navigation structure.`, `Main function to generate reference documentation.`, `Logging handlers for arlogi.  This module provides custom logging handlers inclu` (+40 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 23`** (2 nodes): `test_relative_path.py`, `nested_function()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (2 nodes): `.format()`, `Format log record as JSON.          Args:             record: The log record to`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (2 nodes): `.render_message()`, `Render message text with level-specific styling.          Args:             reco`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (2 nodes): `.resolve_module_level()`, `Resolve a module level to an integer.          Args:             name: Module na`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (2 nodes): `.to_dict()`, `Convert configuration to a dictionary.          Returns:             Dictionary`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (1 nodes): `Validate a log level value.          Args:             level: Log level as int o`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (1 nodes): `Get the global level as an integer.          Returns:             The resolved l`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (1 nodes): `Determine if console output should be shown.          Returns:             True`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `Determine if JSON output is configured.          Returns:             True if JS`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (1 nodes): `Create LoggingConfig from keyword arguments.          This factory method provid`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LoggerFactory` connect `Community 2` to `Community 0`, `Community 1`, `Community 4`, `Community 6`, `Community 7`, `Community 8`, `Community 10`, `Community 11`, `Community 12`, `Community 13`, `Community 17`, `Community 18`?**
  _High betweenness centrality (0.315) - this node is a cross-community bridge._
- **Why does `JSONFileHandler` connect `Community 0` to `Community 9`, `Community 2`, `Community 3`?**
  _High betweenness centrality (0.163) - this node is a cross-community bridge._
- **Why does `LoggingConfig` connect `Community 0` to `Community 1`, `Community 2`, `Community 5`, `Community 9`, `Community 26`, `Community 27`?**
  _High betweenness centrality (0.134) - this node is a cross-community bridge._
- **Are the 126 inferred relationships involving `LoggerFactory` (e.g. with `TestHandlerCleanup` and `TestJSONHandlerResourceManagement`) actually correct?**
  _`LoggerFactory` has 126 INFERRED edges - model-reasoned connections that need verification._
- **Are the 100 inferred relationships involving `JSONFileHandler` (e.g. with `TestHandlerCleanup` and `TestJSONHandlerResourceManagement`) actually correct?**
  _`JSONFileHandler` has 100 INFERRED edges - model-reasoned connections that need verification._
- **Are the 95 inferred relationships involving `LoggerProtocol` (e.g. with `TestCriticalFixes` and `TestTRACEValidation`) actually correct?**
  _`LoggerProtocol` has 95 INFERRED edges - model-reasoned connections that need verification._
- **Are the 85 inferred relationships involving `LoggingConfig` (e.g. with `TestHandlerCleanup` and `TestJSONHandlerResourceManagement`) actually correct?**
  _`LoggingConfig` has 85 INFERRED edges - model-reasoned connections that need verification._