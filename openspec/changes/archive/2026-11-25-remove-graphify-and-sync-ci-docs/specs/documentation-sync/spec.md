# Spec Delta: documentation-sync

## MODIFIED Requirements

### Requirement: Accurate security and configuration documentation

Published documentation (`README.md` and `docs/`) SHALL accurately document `sys.modules`-only `is_test_mode()`, `json_file_base_dir` containment, `LoggingConfigBuilder`, `setup_logging(config=...)`, `LoggerFactory.apply_config()`, `rotate_json_logger()`, `JSONFileHandler` rotation and `base_dir` parameters, the `ColoredConsoleHandler` `markup=False` default, valid configuration parameter types/keys, actual JSON envelope fields, and actual `ColoredConsoleHandler` default colors.

#### Scenario: Following documented configuration and security guides without errors

- **WHEN** a user follows the documented `ArlogiSyslogHandler`, `level_styles`, `module_levels`, `caller_depth`, and `json_file_base_dir` examples
- **THEN** every documented parameter name, type, and JSON output key matches the runtime implementation

#### Scenario: Logger method signatures show the real caller_depth default

- **WHEN** a reader consults the documented logger method signatures in `docs/API_REFERENCE.md`
- **THEN** every method, including `fatal`, shows `caller_depth=None` as the default

#### Scenario: Syslog fallback is described per address type

- **WHEN** a reader consults the `ArlogiSyslogHandler` fallback behavior
- **THEN** the documentation states that silent degradation applies only to the default `/dev/log` address and that initialization errors for custom addresses are raised to the caller

#### Scenario: Module-level overrides in examples take effect

- **WHEN** the multi-environment `module_levels` example in `docs/CONFIGURATION_GUIDE.md` is evaluated for the production environment
- **THEN** the explicit production overrides (for example `<app>.auth` = `ERROR`, `<app>.api` = `WARNING`) are the values passed to `setup_logging()`

#### Scenario: Documented lint rules match the ruff configuration

- **WHEN** a reader compares the rule table in `docs/DEVELOPER_GUIDE.md` with `.ruff.toml`
- **THEN** every listed rule or rule family is selected in `.ruff.toml`

#### Scenario: Public configuration API has runnable examples

- **WHEN** a reader searches the hand-authored guides for `LoggingConfigBuilder`, `LoggerFactory.apply_config()`, `rotate_json_logger()`, and `json_file_base_dir`/`base_dir`
- **THEN** each has at least one runnable example whose parameter names match the runtime signatures

### Requirement: Complete arlogi.otel documentation and MkDocs reference coverage

`README.md`, `docs/USER_GUIDE.md`, `docs/API_REFERENCE.md`, `docs/ARCHITECTURE.md`, and `mkdocs.yml` SHALL document all 9 public exports of `arlogi.otel` (`setup_tracing`, `shutdown_tracing`, `setup_metrics`, `shutdown_metrics`, `install_log_correlation`, `set_trace_modules`, `traced`, `RotatingJsonlSpanExporter`, `RotatingJsonlMetricExporter`) and its SDK-free lazy import boundary.

#### Scenario: Building MkDocs site with complete arlogi.otel reference

- **WHEN** `uv run mkdocs build --strict` executes
- **THEN** the documentation site builds cleanly with navigation entries for `arlogi.otel` and zero broken links

#### Scenario: User guide and architecture document every otel export

- **WHEN** `docs/USER_GUIDE.md` and `docs/ARCHITECTURE.md` are each searched for the 9 `arlogi.otel` export names and the `arlogi[otel]` extra
- **THEN** every name is present in each file, and each file states that bare `import arlogi.otel` does not import `opentelemetry-sdk`

## ADDED Requirements

### Requirement: Executable documentation examples

Code examples in published documentation that contain assertions or claim specific runtime output SHALL produce that output when run against the current package, and examples SHALL NOT recommend logging patterns the runtime does not support.

#### Scenario: Caller attribution test examples pass

- **WHEN** the caller-attribution unit-test examples from `docs/CALLER_ATTRIBUTION_EXAMPLES.md` are executed by the project test suite
- **THEN** every assertion passes

#### Scenario: No unsupported lazy-logging pattern

- **WHEN** `docs/USER_GUIDE.md` is searched for logging calls that pass a callable as the message
- **THEN** none are present, and lazy logging is shown with `isEnabledFor()` guards or `%s`-style deferred formatting

### Requirement: Published documentation uses only public API

Published documentation pages included in MkDocs navigation SHALL NOT instruct users to call private (underscore-prefixed) `arlogi` functions or methods and SHALL use current keyword argument names.

#### Scenario: No private configuration entry point recommended

- **WHEN** published pages under `docs/C4-Documentation/` and `docs/ARCHITECTURE.md` user-facing examples are searched for `_apply_configuration(`
- **THEN** no user code example or API listing recommends it, and `LoggerFactory.apply_config()` or `setup_logging()` is shown instead

### Requirement: Contributor commands match CI gates

`README.md` and `docs/DEVELOPER_GUIDE.md` SHALL document the same lint, format-check, test, and strict documentation-build commands and dependency-isolation flags that the CI workflows enforce.

#### Scenario: README development section mirrors CI

- **WHEN** a contributor reads the `README.md` Development section
- **THEN** it lists `uv run ruff check src/ tests/`, `uv run ruff format --check src/ tests/`, `uv run pytest`, and `uv run mkdocs build --strict`

#### Scenario: Developer guide CI snippet mirrors the workflow

- **WHEN** the GitHub Actions snippet in `docs/DEVELOPER_GUIDE.md` is compared with `.github/workflows/ci.yml`
- **THEN** both use the same dependency-isolation flags on `uv sync` and `uv run`
