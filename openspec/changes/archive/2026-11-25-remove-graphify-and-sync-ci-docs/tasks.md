# Tasks

## 1. Ordering gate with sibling changes

- [x] 1.1 Confirm `fix-core-logging-and-rotation-gaps` and `fix-otel-lifecycle-gaps` are applied (or archived) on the working branch; if either is not, stop before group 5. Verify with `openspec list --json` and `git log --oneline` showing their implementation commits.
- [x] 1.2 Record, in a short note at the top of the PR description, every public behavior those changes altered (signatures, accepted parameter values, raised exceptions, validation and pruning rules) by reading their `proposal.md`/specs deltas and the resulting `src/` diff; this list is the reference for groups 5–7. Verify the note lists each sibling change by name.

## 2. Remove graphify dependencies

- [x] 2.1 In `pyproject.toml`, delete the `graph` dependency group and the `{ include-group = "graph" }` line from `dev`, add `"radon>=6.0.1"` directly to `dev`, and delete the `[tool.uv.sources]` table (its only entry is `graphifyy`). Verify `grep -n -i "graphif\|include-group = \"graph\"" pyproject.toml` returns nothing and `grep -n radon pyproject.toml` shows it under `dev`.
- [x] 2.2 Run `uv lock` and verify `uv lock --check` passes and `grep -c -i graphifyy uv.lock` returns `0`.
- [x] 2.3 Verify the default developer environment no longer plans graphify: `UV_PROJECT_ENVIRONMENT="$(mktemp -d)/venv" uv sync --dry-run --frozen` output contains `radon` and `commitizen` and no `graphifyy`.

## 3. Remove graphify artifacts and agent rules

- [x] 3.1 `git rm -r graphify-out .graphifyignore` and remove the `graphify-out/cache/` line from `.gitignore`. Verify `git ls-files graphify-out .graphifyignore` prints nothing and `grep -n graphify .gitignore` returns nothing.
- [x] 3.2 Replace the `## graphify` section in `CLAUDE.md` with a `## Source of truth` section stating that live `src/` and `openspec/specs/` are authoritative and `docs/` must be kept in sync with them; leave the Release & Publishing section unchanged. Verify `grep -n -i graphif CLAUDE.md` returns nothing (resolves DA-024).
- [x] 3.3 Delete `docs/NotebookLM/05-knowledge-graph.md` and refresh the `## FILE: CLAUDE.md` and `## FILE: pyproject.toml` snapshot sections in `docs/NotebookLM/01-architecture-conventions.md` from the updated files. Verify `grep -rn -i graphif docs/NotebookLM` returns nothing.

## 4. CI dependency isolation (DA-003)

- [x] 4.1 In `.github/workflows/ci.yml` and `.github/workflows/publish.yml`, change matrix `sync-args` to `--frozen --no-dev --group test` and `--frozen --no-dev --group test --extra otel`, and add `--no-sync` to every `uv run` (`ruff check`, `ruff format --check`, `pytest`). Verify `grep -n "uv run" .github/workflows/*.yml | grep -v -- --no-sync` returns nothing and every `sync-args` contains `--no-dev`.
- [x] 4.2 In `.github/workflows/deploy-docs.yml`, use `uv sync --frozen --no-dev --group docs` and `uv run --no-sync mkdocs build --strict`. Verify `UV_PROJECT_ENVIRONMENT="$(mktemp -d)/venv" uv sync --dry-run --frozen --no-dev --group docs` plans no `pytest`, `commitizen`, or `radon`.
- [x] 4.3 Verify the core-only CI environment: `UV_PROJECT_ENVIRONMENT="$(mktemp -d)/venv" uv sync --dry-run --frozen --no-dev --group test` plans no `graphifyy`, `opentelemetry-sdk`, `mkdocs-material`, `commitizen`, or `radon`.
- [x] 4.4 Update the GitHub Actions snippet in `docs/DEVELOPER_GUIDE.md` (Continuous Integration section) to use the same `--no-dev` / `--no-sync` flags. Verify by diffing the snippet's `uv` lines against `ci.yml`.

## 5. Fix runtime-incorrect documentation (DA-014)

- [x] 5.1 In `docs/CALLER_ATTRIBUTION_EXAMPLES.md`, fix the "Unit Test Examples" assertions to expect `[from .test_function_call_attribution()]` and `[from .top_function()]` (or the post-sibling equivalent from 1.2), and correct the console output snippets (around the `caller_depth=0/1/2` sections) to the actual `message\n[attribution]` layout produced by the runtime. Verify by running the extracted block through task 5.2.
- [x] 5.2 Add `tests/test_docs_examples.py` that extracts the fenced `python` block under the "Unit Test Examples" heading of `docs/CALLER_ATTRIBUTION_EXAMPLES.md`, execs it, and invokes each `test_*` function with `caplog`; it MUST fail with a clear message if the block is missing. Verify `uv run --no-sync pytest tests/test_docs_examples.py` passes in both a no-otel and an otel environment.
- [x] 5.3 In `docs/USER_GUIDE.md`, replace both `logger.debug(lambda: ...)` examples with `logger.isEnabledFor(logging.DEBUG)` guards and `%s`-style deferred formatting. Verify `grep -n "lambda" docs/USER_GUIDE.md` shows no logging call with a callable message.
- [x] 5.4 In `docs/API_REFERENCE.md`, change all logger method signatures to `caller_depth=None` and add `fatal`; rewrite the `ArlogiSyslogHandler` fallback list so silent degradation applies only to the default `/dev/log` address and custom addresses raise initialization errors. Verify `grep -n "caller_depth=0" docs/API_REFERENCE.md` returns nothing.
- [x] 5.5 In `docs/CONFIGURATION_GUIDE.md`, move `**module_levels` before the explicit production overrides. Verify by evaluating the snippet's production dict (e.g. a one-off Python check) yields `auth=ERROR`, `api=WARNING`.
- [x] 5.6 In `docs/DEVELOPER_GUIDE.md`, remove the `SIM` row from the ruff rule table (keep rows only for rules selected in `.ruff.toml`). Verify `grep -n "| SIM" docs/DEVELOPER_GUIDE.md` returns nothing.

## 6. Document arlogi.otel in remaining guides (DA-015)

- [x] 6.1 Add an OpenTelemetry (`arlogi[otel]`) section to `docs/USER_GUIDE.md` covering installation of the extra, all 9 public exports with short examples, and the SDK-free lazy import boundary (incorporating any lifecycle behavior recorded in 1.2). Verify each of the 9 names appears via `grep`.
- [x] 6.2 Update `docs/ARCHITECTURE.md`: add `src/arlogi/otel/` (`__init__.py`, `bootstrap.py`, `decorator.py`, `exporters.py`, `_files.py`, `_encode.py`) to the File Structure and Component Reference, add `config_builder.py` without the "(if present)" qualifier, describe the `__getattr__` lazy-loading boundary, and list all 9 exports. Verify each of the 9 names appears via `grep`.

## 7. Document missing public API and remove private-API guidance (DA-016)

- [x] 7.1 In `docs/API_REFERENCE.md`, document `setup_logging()` (including `config=` and `json_file_base_dir=`), `rotate_json_logger()`, `get_json_logger(..., base_dir=...)`, `LoggerFactory.apply_config()`, `LoggingConfigBuilder` (including `with_json_base_dir()`), `JSONFileHandler` `rotate_schedule`/`rotate_retention_count`/`base_dir`, `ColoredConsoleHandler` `markup=False` default, and `JSONFormatter` protected-key nesting, matching current signatures and any changes recorded in 1.2. Verify every name appears via `grep` and parameter names match `src/arlogi/` signatures.
- [x] 7.2 Add runnable `LoggingConfigBuilder`, `LoggerFactory.apply_config()`, and `json_file_base_dir`/`base_dir` examples to `docs/CONFIGURATION_GUIDE.md` and a brief builder/`apply_config()` example to `README.md`. Verify each example runs in a scratch script against a temporary directory.
- [x] 7.3 Update `docs/ARCHITECTURE.md` builder-pattern and factory sections to mention `LoggingConfigBuilder` and public `apply_config()`; internal-flow diagrams MAY keep `_apply_configuration` only where explicitly labelled internal. Verify no user-facing example in the file calls `_apply_configuration(`.
- [x] 7.4 In published `docs/C4-Documentation/` pages, replace user-facing `LoggerFactory._apply_configuration(config)` calls and "(Recommended)" listings with `LoggerFactory.apply_config(config)` / `setup_logging(config=...)`, and replace stale `from_` / `from_caller` / `**{"from": ...}` kwargs with `caller_depth`. Verify `grep -rn "_apply_configuration(\|from_=\|from_caller" docs/C4-Documentation` returns no user-facing hits.

## 8. README contributor commands (DA-023)

- [x] 8.1 Update the `README.md` Development section to list `uv run pytest`, `uv run ruff check src/ tests/`, `uv run ruff format --check src/ tests/`, and `uv run mkdocs build --strict`, with accurate labels. Verify by reading the section and running each command successfully.

## 9. Final alignment and integration verification

- [x] 9.1 Re-check every doc page touched in groups 5–8 against the behavior list from 1.2 and fix any remaining drift. Verify the PR note marks each listed behavior as documented or not user-visible.
- [x] 9.2 Run `uv lock --check` and verify it passes.
- [x] 9.3 Run `UV_PROJECT_ENVIRONMENT="$(mktemp -d)/venv" uv sync --dry-run --frozen --no-dev --group test` and verify the output contains no `graphifyy`.
- [x] 9.4 Run `uv build --sdist` and verify with `tar tzf dist/arlogi-*.tar.gz` that it contains only `src/`, `tests/`, `README.md`, `LICENSE`, `pyproject.toml` (plus `PKG-INFO`) and no `graphify-out/`, `docs/`, or `openspec/` entries.
- [x] 9.5 Run `uv run mkdocs build --strict` and verify it exits 0.
- [x] 9.6 Run `uv run pytest` and verify all tests pass, including `tests/test_docs_examples.py`.
- [x] 9.7 Run `uv run ruff check src/ tests/` and verify it exits 0.
- [x] 9.8 Run `uv run ruff format --check src/ tests/` and verify it exits 0.
- [x] 9.9 Run `git grep -i -l graphif -- ':!uv.lock'` and verify the only hits are `CHANGELOG.md`, `openspec/changes/archive/**`, `docs/_audit_/**`, and this change directory (until archived).
- [x] 9.10 Run `openspec validate remove-graphify-and-sync-ci-docs --strict` and verify it passes.

## Workflow follow-up

- Archive the change after review; on archive, the `ci-and-packaging` and `documentation-sync` main specs receive the deltas.
