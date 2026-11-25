# Tasks

## 1. CI/CD Workflows & Packaging (`ci-and-packaging`)

- [x] 1.1 Update `pyproject.toml` to split `[dependency-groups]` (`test`, `docs`, `graph`, `dev`), remove unused `mkdocs-git-revision-date-localized-plugin` and `mkdocs-minify-plugin`, add `[tool.hatch.build.targets.sdist]` `include`, update `.ruff.toml` `target-version = "py313"`, add `docs/_audit_/` to `.gitignore`, refresh `uv.lock` via `uv lock`, and verify `uv build --sdist` excludes `graphify-out/`.
- [x] 1.2 Create `.github/workflows/ci.yml` (lint, format check, core-only and OTEL test matrix) and update `.github/workflows/publish.yml` and `.github/workflows/deploy-docs.yml` (replace `curl | sh` with `astral-sh/setup-uv`, least-privilege permissions, tag/version guard on `publish`, `workflow_dispatch`/`v*` support on `deploy-docs`, `--frozen` sync), verifying valid YAML syntax.

## 2. Documentation & MkDocs Sync (`documentation-sync`)

- [x] 2.1 Update `README.md`, `docs/ARCHITECTURE.md`, `docs/API_REFERENCE.md`, `docs/CONFIGURATION_GUIDE.md`, `docs/USER_GUIDE.md`, and `docs/DEVELOPER_GUIDE.md` to fix broken examples (`module_levels`, `socktype`, `level_styles`, `caller_depth`, JSON fields, console color scheme), document `is_test_mode()` (`sys.modules`-only), `json_file_base_dir`, `LoggingConfigBuilder`, `setup_logging(config=...)`, `LoggerFactory.apply_config()`, CI workflow, and all 9 `arlogi.otel` exports + lazy import boundary.
- [x] 2.2 Add `docs/reference/arlogi/otel/` (`index.md`, `bootstrap.md`, `decorator.md`, `exporters.md`) and register them in `mkdocs.yml`, verifying `uv run mkdocs build --strict` succeeds with zero errors.

## 3. Final Verification

- [x] 3.1 Run `uv run pytest`, `uv run ruff check src/ tests/`, `uv run ruff format --check src/ tests/`, `uv run mkdocs build --strict`, `npx --yes markdownlint-cli "README.md" "docs/*.md" "docs/reference/arlogi/otel/*.md"`, and `openspec validate "harden-ci-packaging-and-docs" --strict`.
