# Publishing Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Configure `commitizen` for local version bumping and conventional commit enforcement, create `.github/workflows/publish.yml` for PyPI publishing and GitHub releases on tag push, and update documentation.

**Architecture:** `commitizen` reads/updates `pyproject.toml` version via PEP 621, generates `CHANGELOG.md`, and creates git release tags. Pushing `v*` tags triggers GitHub Actions to run pytest, build wheel/sdist via `uv build`, publish to PyPI using secrets.PYPI_API_TOKEN, and create a GitHub Release.

**Tech Stack:** `commitizen`, `uv`, `hatchling`, GitHub Actions (`pypa/gh-action-pypi-publish@v1`, `softprops/action-gh-release@v2`, `peaceiris/actions-gh-pages@v4`).

## Global Constraints

- Python version floor: 3.13
- Build tool: `uv` and `hatchling`
- Commit standard: Conventional Commits (`cz_conventional_commits`)
- Tag format: `v$version`

---

### Task 1: Configure Commitizen in pyproject.toml

**Files:**

- Modify: [pyproject.toml](file:///Users/antonr/Code/2026/arlogi/pyproject.toml)

- [ ] **Step 1: Add commitizen to dev dependencies and configure tool.commitizen**

Edit `pyproject.toml` to add `"commitizen>=4.0.0"` under `[dependency-groups.dev]` and add the `[tool.commitizen]` block:

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

- [ ] **Step 2: Install dependencies**

Run: `uv sync --group dev`
Expected: Success, commitizen installed into `.venv`.

- [ ] **Step 3: Verify commitizen configuration**

Run: `uv run cz version`
Expected: Returns commitizen version (e.g. `4.x.x`).

- [ ] **Step 4: Commit changes**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: configure commitizen in pyproject.toml"
```

---

### Task 2: Create GitHub Actions Publishing Workflow

**Files:**

- Create: `.github/workflows/publish.yml`

- [ ] **Step 1: Write `.github/workflows/publish.yml`**

Create `.github/workflows/publish.yml`:

```yaml
name: Publish Package & Create Release

on:
  push:
    tags:
      - "v*"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync --group dev

      - name: Run pytest
        run: uv run pytest

  publish:
    name: Publish to PyPI & GitHub Release
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Build package
        run: uv build

      - name: Publish package to PyPI
        uses: pypa/gh-action-pypi-publish@v1.12.3
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: dist/*
          generate_release_notes: true
```

- [ ] **Step 2: Commit workflow file**

```bash
git add .github/workflows/publish.yml
git commit -m "ci: add GitHub Actions workflow for PyPI and GitHub releases"
```

---

### Task 3: Update Project Documentation

**Files:**

- Modify: [CLAUDE.md](file:///Users/antonr/Code/2026/arlogi/CLAUDE.md)

- [ ] **Step 1: Add release commands to CLAUDE.md**

Append the following instructions to `CLAUDE.md`:

```markdown
## Release & Publishing

- Use Conventional Commits (`feat: ...`, `fix: ...`, `docs: ...`, or `uv run cz commit`)
- To create a new release:
  1. `uv run cz bump` (bumping version in pyproject.toml and updating CHANGELOG.md)
  2. `git push origin master --tags`
```

- [ ] **Step 2: Commit documentation update**

```bash
git add CLAUDE.md
git commit -m "docs: add release instructions to CLAUDE.md"
```

---

### Task 4: Local Verification of Build and Bump Dry-Run

- [ ] **Step 1: Verify `cz bump --dry-run`**

Run: `uv run cz bump --dry-run`
Expected: `commitizen` previews the bump version and changelog updates cleanly.

- [ ] **Step 2: Verify `uv build`**

Run: `uv build`
Expected: `dist/arlogi-0.607.25-py3-none-any.whl` and `dist/arlogi-0.607.25.tar.gz` created in `dist/`.
