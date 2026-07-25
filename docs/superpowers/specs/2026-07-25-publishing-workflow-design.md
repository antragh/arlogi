# Publishing Workflow Design (Commitizen, GitHub Releases, PyPI)

Date: 2026-07-25

Status: Approved

## Overview

This specification details the setup for version management, conventional commit enforcement, automated testing, GitHub release creation, and PyPI package publishing for `arlogi`.

## Goals

1. Standardize version bumping and changelog generation using `commitizen`.
2. Automate testing, package building (`uv build`), GitHub Release creation, and PyPI publishing upon pushing version tags (`v*`).
3. Deploy documentation automatically to GitHub Pages via MkDocs on master push and release tags.
4. Document release commands in `CLAUDE.md`.

## Architecture & Workflows

### 1. Local Tooling & Configuration (`pyproject.toml`)

- **Dev Dependency**: Add `commitizen` to `[dependency-groups.dev]`.
- **Commitizen Configuration**:

  ```toml
  [tool.commitizen]
  name = "cz_conventional_commits"
  tag_format = "v$version"
  version_scheme = "pep440"
  version_provider = "pep621"
  version_files = ["pyproject.toml"]
  update_changelog_on_bump = true
  changelog_file = "CHANGELOG.md"
  ```

### 2. GitHub Actions Release Workflow (`.github/workflows/publish.yml`)

- **Triggers**:
  - Push of tags matching `v*` (e.g., `v0.607.26`).
  - Manual execution via `workflow_dispatch`.

- **Permissions**:
  - `contents: write` (for GitHub Release creation).

- **Job Sequence**:
  1. **Test Job**:
     - Sets up Python 3.13 and `uv`.
     - Installs dependencies (`uv sync --group dev`).
     - Runs test suite (`uv run pytest`).
  2. **Publish Job** (runs after `test` succeeds):
     - Checkouts code.
     - Installs `uv`.
     - Builds package artifacts using `uv build` (`dist/*.tar.gz`, `dist/*.whl`).
     - Publishes to PyPI via `pypa/gh-action-pypi-publish@v1` using `password: ${{ secrets.PYPI_API_TOKEN }}`.
     - Creates GitHub Release via `softprops/action-gh-release@v2` attaching `CHANGELOG.md` notes and built dist files.

### 3. Developer Workflow

1. Use Conventional Commits (`feat: ...`, `fix: ...`, `docs: ...`, or `uv run cz commit`).
2. Run `uv run cz bump` to bump version in `pyproject.toml`, update `CHANGELOG.md`, create git commit and release tag.
3. Push to repository: `git push origin master --tags`.

## Verification Plan

1. Verify `cz bump --dry-run` operates cleanly with `pyproject.toml`.
2. Verify local build via `uv build`.
3. Validate GitHub workflow YAML structure.
