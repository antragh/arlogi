# Graph Report - /opt/Code/2026/_Libs/arlogi  (2026-06-10)

## Corpus Check
- 18 files · ~83,298 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 391 nodes · 1239 edges · 24 communities detected
- Extraction: 32% EXTRACTED · 68% INFERRED · 0% AMBIGUOUS · INFERRED: 842 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]

## God Nodes (most connected - your core abstractions)
1. `LoggerFactory` - 128 edges
2. `LoggerProtocol` - 109 edges
3. `JSONFileHandler` - 106 edges
4. `LoggingConfig` - 94 edges
5. `LoggingConfigBuilder` - 82 edges
6. `JSONHandler` - 80 edges
7. `ColoredConsoleHandler` - 51 edges
8. `ArlogiSyslogHandler` - 46 edges
9. `HandlerFactory` - 39 edges
10. `JSONFormatter` - 38 edges

## Surprising Connections (you probably didn't know these)
- `LoggingConfig` --uses--> `Builder pattern for LoggingConfig construction.  This module provides a fluent b`  [INFERRED]
  /opt/Code/2026/_Libs/arlogi/src/arlogi/config.py → src/arlogi/config_builder.py
- `LoggingConfig` --uses--> `Builder for creating LoggingConfig instances with fluent API.      This builder`  [INFERRED]
  /opt/Code/2026/_Libs/arlogi/src/arlogi/config.py → src/arlogi/config_builder.py
- `LoggingConfig` --uses--> `Initialize builder with sensible defaults.`  [INFERRED]
  /opt/Code/2026/_Libs/arlogi/src/arlogi/config.py → src/arlogi/config_builder.py
- `LoggingConfig` --uses--> `Set the global log level.          Args:             level: Log level (e.g., "IN`  [INFERRED]
  /opt/Code/2026/_Libs/arlogi/src/arlogi/config.py → src/arlogi/config_builder.py
- `LoggingConfig` --uses--> `Set per-module level overrides.          Allows fine-grained control over loggin`  [INFERRED]
  /opt/Code/2026/_Libs/arlogi/src/arlogi/config.py → src/arlogi/config_builder.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.09
Nodes (85): LoggingConfig, Immutable configuration for arlogi logging setup.      Attributes:         level, Factory for creating logger instances with caller attribution support.  This mod, Log a message with TRACE level (below DEBUG).          Args:             msg: Th, Log a warning message., Log an error message., Log a critical message., Log an exception with traceback. (+77 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (32): Test module-level logging overrides., Builder pattern for LoggingConfig construction.  This module provides a fluent b, from_kwargs(), get_default_level(), is_test_mode(), Logging configuration dataclass for type-safe setup.  This module provides a str, Resolve a module level to an integer.          Args:             name: Module na, Detect if running under a test runner.      Checks for pytest, unittest, or the (+24 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (23): Tests for backward compatibility with old API., Test that old from_caller parameter still works., Test that old from_ parameter still works., Test that old 'from' in dict still works., Test that legacy setup_logging() function still works., TestBackwardCompatibility, main(), get_logger() (+15 more)

### Community 3 - "Community 3"
Cohesion: 0.13
Nodes (20): Tests for LoggingConfigBuilder pattern., Test basic builder usage., Test method chaining in builder., Test builder with json_file_only via console_also parameter., Test builder with both JSON file and console., Test builder with JSON console output only., Test builder with module level overrides., Test builder with custom syslog address. (+12 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (22): Thread safety tests for arlogi.  This module tests that the library is thread-sa, Test concurrent logger creation., Test creating many loggers concurrently with different names., Test concurrent JSON logger creation., Test concurrent logger creation with different levels., Test thread safety of TRACE level registration., Test that concurrent TRACE registration is safe., Test that multiple TRACE registrations are safe. (+14 more)

### Community 5 - "Community 5"
Cohesion: 0.15
Nodes (14): Comprehensive tests for refactored arlogi code.  Tests cover all critical fixes,, Tests for type safety improvements., Test that logger complies with LoggerProtocol., Test that all protocol methods are implemented., Test that name property exists and returns string., Integration tests for real-world usage scenarios., Tests for from_kwargs() validation improvements., Test that unknown parameters raise TypeError. (+6 more)

### Community 6 - "Community 6"
Cohesion: 0.19
Nodes (8): Tests for critical bug fixes., Test that fatal() method exists on logger., Test that fatal() method can be called without error., Test that fatal() logs at CRITICAL level., TestCriticalFixes, Protocol, LoggerProtocol, Protocol defining the interface for the arlogi logger.

### Community 7 - "Community 7"
Cohesion: 0.15
Nodes (8): Tests for consistent logger naming patterns., Test that logger names get arlogi. prefix., Test that existing prefix is not duplicated., Test that global logger uses consistent naming., Test that JSON loggers have consistent prefix., Test that syslog loggers have consistent prefix., TestLoggerNamingConsistency, get_global_logger()

### Community 8 - "Community 8"
Cohesion: 0.17
Nodes (7): Tests for caller_depth parameter and deprecation warnings., Test that new caller_depth parameter works., Test that from_caller parameter triggers deprecation warning., Test that from_ parameter triggers deprecation warning., Test that 'from' in dict triggers deprecation warning., Test that caller_depth doesn't trigger warning., TestCallerDepthDeprecation

### Community 9 - "Community 9"
Cohesion: 0.35
Nodes (1): TraceLogger

### Community 10 - "Community 10"
Cohesion: 0.2
Nodes (6): Tests for TRACE level string validation fix., Test that TRACE level string is accepted., Test that lowercase 'trace' is accepted., Test that TRACE is mentioned in validation error., Test that standard logging levels still work., TestTRACEValidation

### Community 11 - "Community 11"
Cohesion: 0.2
Nodes (6): Tests for SRP compliance in refactored code., Test that _extract_caller_depth can be tested independently., Test that _format_caller_attribution can be tested independently., Test that _add_attribution_to_message can be tested independently., Test that _process_extra_kwargs can be tested independently., TestSingleResponsibilityPrinciple

### Community 12 - "Community 12"
Cohesion: 0.2
Nodes (5): Initialize the JSON stream handler.          Args:             stream: The strea, Initialize the JSON file handler.          Args:             filename: Path to t, Initialize the syslog handler.          Args:             address: Syslog server, Initialize the colored console handler.          Args:             show_time: Wh, Find the project root by looking for common indicators.          Searches upward

### Community 13 - "Community 13"
Cohesion: 0.31
Nodes (8): create_markdown(), create_nav_menu_yaml(), extract_classes_and_functions(), main(), Extracts class and function names from a given Python file., Creates a Markdown file containing the API reference for the given Python module, Prints a YAML-friendly navigation structure., Main function to generate reference documentation.

### Community 14 - "Community 14"
Cohesion: 0.5
Nodes (2): Override render method to show relative paths from project root.          Args:, Get level text as a single character with styling.          Args:             re

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (1): Render message text with level-specific styling.          Args:             reco

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (1): Convert configuration to a dictionary.          Returns:             Dictionary

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (1): Initialize builder with sensible defaults.

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (0): 

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (1): Validate a log level value.          Args:             level: Log level as int o

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (1): Get the global level as an integer.          Returns:             The resolved l

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (1): Determine if console output should be shown.          Returns:             True

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (1): Determine if JSON output is configured.          Returns:             True if JS

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (1): Create LoggingConfig from keyword arguments.          This factory method provid

## Knowledge Gaps
- **34 isolated node(s):** `Extracts class and function names from a given Python file.`, `Creates a Markdown file containing the API reference for the given Python module`, `Prints a YAML-friendly navigation structure.`, `Main function to generate reference documentation.`, `Logging handlers for arlogi.  This module provides custom logging handlers inclu` (+29 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 15`** (2 nodes): `.render_message()`, `Render message text with level-specific styling.          Args:             reco`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (2 nodes): `.to_dict()`, `Convert configuration to a dictionary.          Returns:             Dictionary`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (2 nodes): `.__init__()`, `Initialize builder with sensible defaults.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (1 nodes): `Validate a log level value.          Args:             level: Log level as int o`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (1 nodes): `Get the global level as an integer.          Returns:             The resolved l`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (1 nodes): `Determine if console output should be shown.          Returns:             True`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (1 nodes): `Determine if JSON output is configured.          Returns:             True if JS`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (1 nodes): `Create LoggingConfig from keyword arguments.          This factory method provid`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LoggerFactory` connect `Community 5` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 6`, `Community 7`, `Community 8`, `Community 10`, `Community 11`?**
  _High betweenness centrality (0.299) - this node is a cross-community bridge._
- **Why does `LoggingConfig` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 5`, `Community 9`, `Community 10`, `Community 16`, `Community 17`?**
  _High betweenness centrality (0.170) - this node is a cross-community bridge._
- **Why does `LoggerProtocol` connect `Community 6` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 5`, `Community 7`, `Community 8`, `Community 9`, `Community 10`, `Community 11`?**
  _High betweenness centrality (0.151) - this node is a cross-community bridge._
- **Are the 126 inferred relationships involving `LoggerFactory` (e.g. with `TestHandlerCleanup` and `TestJSONHandlerResourceManagement`) actually correct?**
  _`LoggerFactory` has 126 INFERRED edges - model-reasoned connections that need verification._
- **Are the 94 inferred relationships involving `LoggerProtocol` (e.g. with `TestCriticalFixes` and `TestTRACEValidation`) actually correct?**
  _`LoggerProtocol` has 94 INFERRED edges - model-reasoned connections that need verification._
- **Are the 103 inferred relationships involving `JSONFileHandler` (e.g. with `TestHandlerCleanup` and `TestJSONHandlerResourceManagement`) actually correct?**
  _`JSONFileHandler` has 103 INFERRED edges - model-reasoned connections that need verification._
- **Are the 89 inferred relationships involving `LoggingConfig` (e.g. with `TestHandlerCleanup` and `TestJSONHandlerResourceManagement`) actually correct?**
  _`LoggingConfig` has 89 INFERRED edges - model-reasoned connections that need verification._