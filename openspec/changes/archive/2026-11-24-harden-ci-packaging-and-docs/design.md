# Design

## Context

See `proposal.md` for motivation and scope. All runtime Python changes in `src/arlogi/` were completed and archived in Waves 1 and 2.

## Goals / Non-Goals

**Goals:**

- Enforce lint, format, core-only (`no-otel`), and `[otel]` test checks automatically on PRs/branches and before any PyPI release.
- Eliminate `curl | sh` installer execution, overly broad workflow-level `contents: write`, and `5.84 MB` `graphify-out/` bloat in `sdist` archives.
- Synchronize `README.md`, `docs/`, and `mkdocs.yml` with actual `arlogi` and `arlogi.otel` APIs and security invariants.

**Non-Goals:**

- Modifying `src/arlogi/*.py` or `src/arlogi/otel/*.py` runtime behavior.
- Migrating PyPI authentication from `PYPI_API_TOKEN` to OIDC Trusted Publishing without external PyPI/GitHub Environment setup (note: `publish.yml` keeps `secrets.PYPI_API_TOKEN` while adding strict `refs/tags/v*` and version-match guards; OIDC can be enabled once the PyPI publisher is registered).

## Decisions

### 1. CI Workflows & Release Guards

- **Choice**:
  - Create `.github/workflows/ci.yml` with `permissions: contents: read`, `astral-sh/setup-uv@v5`, `uv sync --frozen --group test` (no-otel check) and `uv sync --frozen --group test --extra otel` (full check + `ruff check` + `ruff format --check`).
  - Update `.github/workflows/publish.yml`: top-level `permissions: contents: read`; `test` job runs `ruff check src/ tests/`, `ruff format --check src/ tests/`, core-only `pytest`, and `[otel]` `pytest`; `publish` job has `if: startsWith(github.ref, 'refs/tags/v')`, checks `github.ref_name == "v$(python -c 'import tomllib; ...')"`, builds with `uv build`, publishes to PyPI, and creates the GitHub Release in a job scoped with `permissions: contents: write`.
  - Update `.github/workflows/deploy-docs.yml`: trigger on `push` (`branches: [master]`, `tags: ['v*']`) and `workflow_dispatch`, scope `permissions: contents: write` to the `deploy` job, install `--group docs`, and allow `peaceiris/actions-gh-pages@v4` on `workflow_dispatch`, `master` push, or `v*` tag push.

### 2. Packaging & Dependency Groups

- **Choice**:
  - In `pyproject.toml`, split `[dependency-groups]` into `test` (`pytest`, `pytest-cov`, `ruff`, `psutil`), `docs` (`mkdocs-material`, `mkdocstrings`, `mkdocstrings-python`, `pymdown-extensions`), `graph` (`graphifyy`, `radon`), and `dev = [{include-group = "test"}, {include-group = "docs"}, {include-group = "graph"}, "commitizen>=4.0.0"]`.
  - Add `[tool.hatch.build.targets.sdist]` with `include = ["/src", "/tests", "/README.md", "/LICENSE", "/pyproject.toml"]`.
  - Update `.ruff.toml` `target-version = "py313"` and add `docs/_audit_/` to `.gitignore`.

### 3. Documentation & MkDocs Sync

- **Choice**:
  - Fix all 7 broken contracts in `docs/CONFIGURATION_GUIDE.md`, `docs/ARCHITECTURE.md`, `docs/USER_GUIDE.md`, and `README.md`.
  - Document `json_file_base_dir` / `base_dir`, `sys.modules`-only `is_test_mode()`, `LoggingConfigBuilder`, `setup_logging(config=...)`, `LoggerFactory.apply_config()`, and `arlogi.otel` (all 9 exports + lazy import boundary) across `README.md`, `docs/USER_GUIDE.md`, `docs/API_REFERENCE.md`, `docs/ARCHITECTURE.md`, and `docs/DEVELOPER_GUIDE.md`.
  - Add `docs/reference/arlogi/otel/*.md` pages (`__init__.md`, `bootstrap.md`, `decorator.md`, `exporters.md`) and register them in `mkdocs.yml` `nav`, verifying with `uv run mkdocs build --strict`.
