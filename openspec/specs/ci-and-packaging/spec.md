# ci-and-packaging Specification

## Purpose
Defines CI quality gates, tag-verified package release and documentation deployment workflows, lean source-distribution packaging, and separated developer dependency groups.

## Requirements

### Requirement: Automated pull-request and branch CI quality gates

The repository SHALL provide a CI workflow triggered on `push` to `master` and `pull_request` that enforces `ruff check`, `ruff format --check`, and both core-only (without `[otel]`) and full `[otel]` `pytest` suites using frozen lockfile resolution. CI and release test jobs SHALL install only the explicitly requested dependency group and extras, MUST NOT install the default `dev` group, and MUST NOT re-sync the environment when running tools.

#### Scenario: Verifying core-only and OTEL test matrix on pull requests

- **WHEN** a pull request or push to `master` runs the CI workflow
- **THEN** lint, format check, `no-otel` core tests, and `[otel]` tests all execute without installing the `dev` group, `commitizen`, `radon`, or any `docs` group package

#### Scenario: Core-only job environment excludes the OTEL SDK and dev tooling

- **WHEN** `uv sync --dry-run --frozen --no-dev --group test` is resolved against the committed `uv.lock`
- **THEN** the planned environment contains the project, `rich`, and `test` group packages only, with no `opentelemetry-sdk`, `mkdocs-material`, `commitizen`, or `radon`

#### Scenario: Tool invocations do not re-install the default group

- **WHEN** any CI, release-test, or docs-deploy step runs a tool through `uv run` after the install step
- **THEN** the invocation does not perform a project sync and the environment produced by the install step is left unchanged

### Requirement: Tag-guarded release publication and least-privilege permissions

The release workflow SHALL scope top-level permissions to `contents: read`, SHALL guard PyPI publication and GitHub Release creation to `refs/tags/v*` matching `[project].version` in `pyproject.toml`, and SHALL install `uv` via `astral-sh/setup-uv` rather than piping remote shell scripts into `sh`.

#### Scenario: Preventing untagged workflow_dispatch PyPI publication

- **WHEN** `publish.yml` is dispatched on a non-tag ref or a tag whose name does not match `v<pyproject.toml version>`
- **THEN** the `publish` job MUST NOT run or upload packages to PyPI

### Requirement: Documentation deployment on master, release tags, and manual dispatch

The documentation deployment workflow SHALL build and deploy MkDocs on `master` pushes, `v*` tag pushes, and manual `workflow_dispatch` runs using only the `docs` dependency group.

#### Scenario: Deploying documentation via workflow_dispatch or release tag

- **WHEN** `deploy-docs.yml` is triggered by `workflow_dispatch` or a `v*` tag push
- **THEN** `mkdocs build` runs and the `Deploy to GitHub Pages` step executes

#### Scenario: Docs deployment installs only the docs group

- **WHEN** the `deploy-docs.yml` install step resolves dependencies
- **THEN** only the project and `docs` group packages are installed, and no `test` group, `commitizen`, or `radon` package is present when `mkdocs build --strict` runs

### Requirement: Lean source distribution and split dependency groups

`pyproject.toml` SHALL exclude NotebookLM notes, audit reports (`docs/_audit_/`), and editor dotfiles from `sdist` tarballs, and SHALL separate `test` and `docs` dependency groups, with `dev` composing `test`, `docs`, and developer-only tools. The project SHALL NOT declare any knowledge-graph tooling dependency group or git-sourced developer dependency.

#### Scenario: Building a minimal sdist without graphify-out dumps

- **WHEN** `uv build --sdist` builds the source distribution
- **THEN** the resulting `.tar.gz` contains `/src`, `/tests`, `/README.md`, `/LICENSE`, and `/pyproject.toml` and contains no `docs/`, `openspec/`, or `graphify-out/` entries

#### Scenario: Default developer sync does not install graphify

- **WHEN** `uv sync --dry-run --frozen` resolves the default developer environment from the committed `uv.lock`
- **THEN** no `graphifyy` package is planned, `radon` is planned via the `dev` group, and `uv lock --check` succeeds

#### Scenario: No graph dependency group remains

- **WHEN** `pyproject.toml` `[dependency-groups]` and `[tool.uv.sources]` are inspected
- **THEN** there is no `graph` group, no `graphifyy` entry, and no git-sourced dependency
