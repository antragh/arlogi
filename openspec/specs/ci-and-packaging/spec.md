# ci-and-packaging Specification

## Purpose
Defines CI quality gates, tag-verified package release and documentation deployment workflows, lean source-distribution packaging, and separated developer dependency groups.

## Requirements

### Requirement: Automated pull-request and branch CI quality gates

The repository SHALL provide a CI workflow triggered on `push` to `master` and `pull_request` that enforces `ruff check`, `ruff format --check`, and both core-only (without `[otel]`) and full `[otel]` `pytest` suites using frozen lockfile resolution.

#### Scenario: Verifying core-only and OTEL test matrix on pull requests

- **WHEN** a pull request or push to `master` runs the CI workflow
- **THEN** lint, format check, `no-otel` core tests, and `[otel]` tests all execute without installing `graphifyy`

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

### Requirement: Lean source distribution and split dependency groups

`pyproject.toml` SHALL exclude repository-internal knowledge-graph dumps (`graphify-out/`), NotebookLM notes, audit reports (`docs/_audit_/`), and editor dotfiles from `sdist` tarballs, and SHALL separate `test`, `docs`, and `graph` dependency groups.

#### Scenario: Building a minimal sdist without graphify-out dumps

- **WHEN** `uv build --sdist` builds the source distribution
- **THEN** the resulting `.tar.gz` contains `/src`, `/tests`, `/README.md`, `/LICENSE`, and `/pyproject.toml` without `graphify-out/`
