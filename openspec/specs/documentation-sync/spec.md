# documentation-sync Specification

## Purpose
Defines alignment between published Markdown documentation, MkDocs navigation, and the hardened runtime behavior of `arlogi` and `arlogi.otel`.

## Requirements

### Requirement: Accurate security and configuration documentation

Published documentation (`README.md` and `docs/`, including published `docs/C4-Documentation/` pages and `docs/C4-Documentation/apis/arlogi-api.yaml`) SHALL accurately document `sys.modules`-only `is_test_mode()`, `json_file_base_dir` containment, `LoggingConfigBuilder`, `setup_logging(config=...)`, `LoggerFactory.apply_config()`, `rotate_json_logger()`, `JSONFileHandler` rotation and `base_dir` parameters, the `ColoredConsoleHandler` `markup=False` default, valid configuration parameter types/keys, actual JSON envelope fields (including `exception`), `stderr` default for `get_json_logger()`, atomic handler rollback/re-raising, and actual `ColoredConsoleHandler` default colors. Published documentation MUST NOT disclose internal private IP addresses, SSH credentials/key paths, internal server docroots, or local workstation paths, and SHALL exclude or remove C4 pages documenting gitignored directories (`docs/scripts/`, `subdir/`).

#### Scenario: Following documented configuration and security guides without errors

- **WHEN** a user follows the documented `ArlogiSyslogHandler`, `level_styles`, `module_levels`, `caller_depth`, and `json_file_base_dir` examples
- **THEN** every documented parameter name, type, and JSON output key matches the runtime implementation

#### Scenario: Logger method signatures show the real caller_depth default

- **WHEN** a reader consults the documented logger method signatures in `docs/API_REFERENCE.md`
- **THEN** every method, including `fatal`, shows `caller_depth=None` as the default

#### Scenario: Syslog fallback is described per address type

- **WHEN** a reader consults the `ArlogiSyslogHandler` fallback behavior (including `docs/ARCHITECTURE.md` Error Boundaries)
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

#### Scenario: Published C4 documentation matches runtime contracts and omits internal metadata

- **WHEN** `README.md`, `mkdocs.yml`, and published pages under `docs/C4-Documentation/` are inspected
- **THEN** `c4-code-docs-scripts.md` and `c4-code-subdir.md` are absent, zero private IPs (`192.168.168.5`), SSH key paths, `/opt/c/nginx` paths, or local `/opt/Code/...` workstation paths appear, `c4-component-core-logging.md`/`c4-container.md` document real JSON envelope keys and `setup_logging()` without false deprecation, `c4-code-tests-example.md` uses `caller_depth`, `c4-code-src-arlogi.md` reflects `sys.modules`-only `is_test_mode()`, `apis/arlogi-api.yaml` states `stderr` for `get_json_logger`, and `docs/API_REFERENCE.md` lists `exception` in the protected JSON envelope

### Requirement: Complete arlogi.otel documentation and MkDocs reference coverage

`README.md`, `docs/USER_GUIDE.md`, `docs/API_REFERENCE.md`, `docs/ARCHITECTURE.md`, and `mkdocs.yml` SHALL document all 9 public exports of `arlogi.otel` (`setup_tracing`, `shutdown_tracing`, `setup_metrics`, `shutdown_metrics`, `install_log_correlation`, `set_trace_modules`, `traced`, `RotatingJsonlSpanExporter`, `RotatingJsonlMetricExporter`) and its SDK-free lazy import boundary. `mkdocs.yml` SHALL configure anchor link validation at `warn` level so `uv run mkdocs build --strict` fails on broken heading anchors.

#### Scenario: Building MkDocs site with complete arlogi.otel reference

- **WHEN** `uv run mkdocs build --strict` executes
- **THEN** the documentation site builds cleanly with navigation entries for `arlogi.otel`, valid heading anchors (`#jsonhandler-and-jsonformatter` rather than `#jsonhandler`), and zero broken links or anchor warnings

#### Scenario: User guide and architecture document every otel export

- **WHEN** `docs/USER_GUIDE.md` and `docs/ARCHITECTURE.md` are each searched for the 9 `arlogi.otel` export names and the `arlogi[otel]` extra
- **THEN** every name is present in each file, and each file states that bare `import arlogi.otel` does not import `opentelemetry-sdk`

### Requirement: Executable documentation examples

Code examples in published documentation that contain assertions or claim specific runtime output SHALL produce that output when run against the current package, and examples SHALL NOT recommend logging patterns the runtime does not support.

#### Scenario: Caller attribution test examples pass

- **WHEN** the caller-attribution unit-test examples from `docs/CALLER_ATTRIBUTION_EXAMPLES.md` are executed by the project test suite and the `UserService` depth examples are inspected or run
- **THEN** every assertion passes and the `caller_depth` inline comments match the emitted `[from ...()]` function name

#### Scenario: No unsupported lazy-logging pattern

- **WHEN** `docs/USER_GUIDE.md` is searched for logging calls that pass a callable as the message
- **THEN** none are present, and lazy logging is shown with `isEnabledFor()` guards or `%s`-style deferred formatting

#### Scenario: Configuration and API examples filter logs and avoid double-nested paths

- **WHEN** a reader runs the `Filtering Logs` snippet in `docs/CONFIGURATION_GUIDE.md` or the `json_file_base_dir` snippet in `docs/API_REFERENCE.md`
- **THEN** `get_logger` is imported, `logger.addFilter(...)` filters the targeted records, and `json_file_name="app.jsonl"` with `json_file_base_dir="logs"` writes to `logs/app.jsonl` instead of `logs/logs/app.jsonl`

### Requirement: Published documentation uses only public API

Published documentation pages included in MkDocs navigation SHALL NOT instruct users to call private (underscore-prefixed) `arlogi` functions or methods and SHALL use current keyword argument names.

#### Scenario: No private configuration entry point recommended

- **WHEN** published pages under `docs/C4-Documentation/` and `docs/ARCHITECTURE.md` user-facing examples are searched for `_apply_configuration(`
- **THEN** no user code example or API listing recommends it, and `LoggerFactory.apply_config()` or `setup_logging()` is shown instead

### Requirement: Contributor commands match CI gates

`README.md` and `docs/DEVELOPER_GUIDE.md` SHALL document the same lint, format-check, test, and strict documentation-build commands and dependency-isolation flags that the CI workflows enforce, and `docs/DEVELOPER_GUIDE.md` release instructions SHALL match Commitizen + tag-triggered release automation.

#### Scenario: README development section mirrors CI

- **WHEN** a contributor reads the `README.md` Development section
- **THEN** it lists `uv run ruff check src/ tests/`, `uv run ruff format --check src/ tests/`, `uv run pytest`, and `uv run mkdocs build --strict`

#### Scenario: Developer guide CI snippet mirrors the workflow

- **WHEN** the GitHub Actions snippet in `docs/DEVELOPER_GUIDE.md` is compared with `.github/workflows/ci.yml`
- **THEN** both use the same `permissions: contents: read`, `no-otel`/`otel` matrix legs, and dependency-isolation flags (`--frozen --no-dev`, `--no-sync`) on `uv sync` and `uv run`

#### Scenario: Developer guide commands and release checklist match CI and CLAUDE.md

- **WHEN** `docs/DEVELOPER_GUIDE.md` contributor commands and release checklist are compared against `.github/workflows/ci.yml`, `.github/workflows/publish.yml`, and `CLAUDE.md`
- **THEN** contributor commands use `src/ tests/`, include `uv run ruff format --check src/ tests/` and `uv run mkdocs build --strict`, and the release checklist prescribes `uv run cz bump` + tag push rather than manual edits and local `uv publish`

### Requirement: Syslog format documentation

Published documentation (`README.md`, `docs/API_REFERENCE.md`, `docs/CONFIGURATION_GUIDE.md`, `docs/USER_GUIDE.md`, and `docs/ARCHITECTURE.md`) SHALL document `syslog_format` (`"text"` default and `"json"` `<name>[<pid>]: {...}` output) and `SyslogJSONFormatter`, including TCP/Unix socket guidance for large payloads.

#### Scenario: Guides and API reference document syslog_format accurately

- **WHEN** a reader consults `README.md`, `docs/API_REFERENCE.md`, `docs/CONFIGURATION_GUIDE.md`, `docs/USER_GUIDE.md`, and `docs/ARCHITECTURE.md` for syslog JSON configuration
- **THEN** every file explicitly names `SyslogJSONFormatter`, documents valid `syslog_format` literals (`"text"` / `"json"`), shows the `<name>[<pid>]: {...}` wire format and TCP/Unix guidance in prose, and `uv run mkdocs build --strict` exits 0
