# Proposal

## Why

The repository deep audit (`docs/_audit_/2611242139-deep-audit.md`) identified high- and medium-severity CI/CD, packaging, and documentation drift issues: `publish.yml` permits unguarded `workflow_dispatch` PyPI publication with workflow-wide `contents: write` and `curl | sh` `uv` installation; no PR/branch CI workflow enforces `ruff check`, `ruff format --check`, `ty` / type checks, or core-only (`no-otel`) tests; `deploy-docs.yml` silently skips deployment on `workflow_dispatch` and omits `v*` tags; `pyproject.toml` ships `5.84 MB` of `graphify-out/` dumps in the PyPI `sdist` and bundles `graphifyy` (29 transitive dependencies) into `dev`; and `README.md` / `docs/` contain broken API contracts and omit `arlogi.otel` and `json_file_base_dir`. Wave 3 resolves all remaining CI/CD, packaging, and documentation findings.

## What Changes

- **Harden GitHub Actions CI/CD & Release Gates (`DA-005`, `DA-011`, `DA-017`, `DA-019`)**:
  - Add `.github/workflows/ci.yml` triggered on `push` (`master`) and `pull_request` running `ruff check src/ tests/`, `ruff format --check src/ tests/`, and a test matrix covering both core-only (`--group test` without `--extra otel`) and full OTEL (`--group test --extra otel`) suites.
  - Harden `.github/workflows/publish.yml`: scope top-level `permissions` to `contents: read` (granting `contents: write` only to the GitHub Release job), replace `curl ... | sh` with `astral-sh/setup-uv`, gate `publish` on `startsWith(github.ref, 'refs/tags/v')`, verify tag version matches `pyproject.toml` `[project].version`, run `ruff check` + `ruff format --check` + core-only and OTEL `pytest` before building, and use `--frozen` on `uv sync`.
  - Fix `.github/workflows/deploy-docs.yml`: trigger on `push` (`master` and `tags: ['v*']`) plus `workflow_dispatch`, scope `permissions: contents: write` to the `deploy` job only, replace `curl ... | sh` with `astral-sh/setup-uv`, use `uv sync --frozen --group docs`, and enable deployment on `workflow_dispatch` and `v*` tags.
- **Optimize Packaging & Dependency Groups (`DA-020`, `INV-9`)**:
  - Add `[tool.hatch.build.targets.sdist]` in `pyproject.toml` excluding `graphify-out`, `docs/NotebookLM`, `.vscode`, `.envrc`, `CLAUDE.md`, `docs/_audit_`, and `uv.lock` (including `/src`, `/tests`, `/README.md`, `/LICENSE`, `/pyproject.toml`).
  - Split `[dependency-groups]` in `pyproject.toml` into `test`, `docs`, and `graph` (with `dev` composing them via `include-group`), and remove unused `mkdocs-git-revision-date-localized-plugin` and `mkdocs-minify-plugin`.
  - Update `.ruff.toml` `target-version` from `"py312"` to `"py313"` and add `docs/_audit_/` to `.gitignore`.
- **Synchronize Documentation & MkDocs (`DA-018`, `DA-025`..`DA-030`)**:
  - Update `README.md`, `docs/ARCHITECTURE.md`, `docs/CONFIGURATION_GUIDE.md`, `docs/API_REFERENCE.md`, `docs/USER_GUIDE.md`, `docs/DEVELOPER_GUIDE.md`, and `mkdocs.yml` (plus `docs/reference/arlogi/otel/*.md`):
    - Fix `is_test_mode()` docs to state `sys.modules`-only (`PYTEST_CURRENT_TEST` intentionally ignored).
    - Document `json_file_base_dir`, `JSONFileHandler(base_dir=...)`, `LoggingConfigBuilder`, `setup_logging(config=...)`, `LoggerFactory.apply_config()`, and all 9 `arlogi.otel` exports + `INV-7` lazy-import contract.
    - Fix broken examples (`module_levels={"app": "TRACE"}`, valid `setup_logging(...)` syntax, actual JSON envelope keys, `socket.SOCK_DGRAM`, lowercase `level_styles`, `caller_depth` instead of `from_`, and actual `ColoredConsoleHandler` default colors).
- **Non-Goals / Out of Scope**:
  - Modifying runtime Python source code in `src/arlogi/` (completed and archived in Waves 1 and 2).

## Capabilities

### New Capabilities

- `ci-and-packaging`: Automated PR/branch CI quality gates (lint, format, core-only and OTEL test matrix), tag-guarded release pipeline, docs deployment on `master`/`v*`/`workflow_dispatch`, lean `sdist` packaging, and split `test`/`docs`/`graph` dependency groups.
- `documentation-sync`: Accurate, MkDocs-validated user, configuration, architecture, API, and developer documentation matching current `arlogi` and `arlogi.otel` behavior.

### Modified Capabilities

<!-- None -->

## Impact

- **Affected Files**: `.github/workflows/ci.yml` (new), `.github/workflows/publish.yml`, `.github/workflows/deploy-docs.yml`, `pyproject.toml`, `uv.lock`, `.ruff.toml`, `.gitignore`, `mkdocs.yml`, `README.md`, `docs/*.md`, `docs/reference/arlogi/otel/*.md` (new).
- **Dependencies**: Zero new runtime dependencies; `mkdocs-git-revision-date-localized-plugin` and `mkdocs-minify-plugin` removed from dev dependencies.
