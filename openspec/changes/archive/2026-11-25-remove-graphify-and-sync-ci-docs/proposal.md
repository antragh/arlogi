# Proposal

## Why

The repository still carries the `graphify` knowledge-graph tooling (`graphifyy` git dependency, `graph` dependency group, 44 tracked files / ~9.5 MB under `graphify-out/` last regenerated on Jul 21, `.graphifyignore`, and agent rules in `CLAUDE.md`) even though nobody uses it. Because `dev` is uv's default-on group and includes `graph`, every CI, release-test, and docs-deploy job installs `graphifyy` (DA-003), and `CLAUDE.md` tells agents to trust the stale graph over live sources (DA-024). The verified deep audit (`docs/_audit_/2611250738-deep-audit.json`) also confirmed that hand-authored documentation contains runtime-failing examples and misses public API surface (DA-014, DA-015, DA-016, DA-023). Fixing both together lets the CI-and-packaging and documentation-sync specs describe reality again.

## What Changes

- **Remove graphify entirely**:
  - Drop the `graph` dependency group and `graphifyy` from `pyproject.toml` `[dependency-groups]` and the `[tool.uv.sources]` table; move `radon>=6.0.1` directly into the `dev` group (it is still documented in `docs/DEVELOPER_GUIDE.md` for complexity checks); refresh `uv.lock` with `uv lock`.
  - Delete the tracked `graphify-out/` directory and `.graphifyignore`; remove the `graphify-out/cache/` line from `.gitignore`.
  - Replace the `## graphify` section in `CLAUDE.md` with a short statement that live `src/` and `openspec/specs/` are the source of truth (resolves DA-024).
  - Delete `docs/NotebookLM/05-knowledge-graph.md` (a dump of `graphify-out/GRAPH_REPORT.md`) and refresh the embedded `CLAUDE.md` and `pyproject.toml` snapshots in `docs/NotebookLM/01-architecture-conventions.md` so they no longer mention graphify.
  - `CHANGELOG.md` history is NOT rewritten.
- **CI dependency isolation (DA-003)**: add `--no-dev` to every `uv sync` and `--no-sync` to every subsequent `uv run` in `.github/workflows/ci.yml`, `publish.yml`, and `deploy-docs.yml`; mirror the change in the CI snippet in `docs/DEVELOPER_GUIDE.md`. Still required after graphify removal because `dev` keeps pulling `docs`, `test`, `commitizen`, and `radon`.
- **Fix runtime-incorrect documentation (DA-014)**: caller-attribution test assertions and output snippets in `docs/CALLER_ATTRIBUTION_EXAMPLES.md`; unsupported `lambda` lazy logging in `docs/USER_GUIDE.md`; `caller_depth=0` default and unconditional syslog silent-fallback claim in `docs/API_REFERENCE.md`; shadowed `**module_levels` in `docs/CONFIGURATION_GUIDE.md`; nonexistent `SIM` rule in `docs/DEVELOPER_GUIDE.md`.
- **Document `arlogi.otel` in the remaining guides (DA-015)**: add the 9 public exports and the SDK-free lazy import boundary to `docs/USER_GUIDE.md` and `docs/ARCHITECTURE.md`.
- **Document missing public API (DA-016)**: `LoggingConfigBuilder`, `LoggerFactory.apply_config()`, `setup_logging(config=..., json_file_base_dir=...)`, `rotate_json_logger()`, `get_json_logger(base_dir=...)`, `JSONFileHandler` rotation/containment params, `ColoredConsoleHandler` `markup=False` default, and `JSONFormatter` protected-key nesting; replace private `_apply_configuration()` recommendations in published `docs/C4-Documentation/` pages and `docs/ARCHITECTURE.md` user-facing text.
- **README development commands (DA-023)**: document `uv run ruff check src/ tests/`, `uv run ruff format --check src/ tests/`, and `uv run mkdocs build --strict`.
- Add a pytest-based docs-example check so the caller-attribution assertions are executed in CI.

**Ordering**: sibling changes `fix-core-logging-and-rotation-gaps` and `fix-otel-lifecycle-gaps` are drafted in parallel and may change documented runtime behavior. This change SHALL be applied LAST and includes a task to align documentation with whatever behavior those changes land.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `ci-and-packaging`: CI quality gate, docs deployment, and lean-sdist/dependency-group requirements change — the `graph` group and `graphify-out/` references are removed, and CI jobs MUST NOT install the default `dev` group.
- `documentation-sync`: accuracy requirement is extended to cover executable examples (caller attribution, lazy logging, `module_levels` merging, syslog fallback, `caller_depth` defaults, ruff rules), the full public API surface, no private API recommendations, and README contributor commands matching CI.

## Impact

- **Files**: `pyproject.toml`, `uv.lock`, `.gitignore`, `.graphifyignore` (deleted), `graphify-out/` (deleted), `CLAUDE.md`, `.github/workflows/{ci,publish,deploy-docs}.yml`, `README.md`, `docs/{USER_GUIDE,API_REFERENCE,ARCHITECTURE,CONFIGURATION_GUIDE,DEVELOPER_GUIDE,CALLER_ATTRIBUTION_EXAMPLES}.md`, `docs/C4-Documentation/*.md`, `docs/NotebookLM/01-architecture-conventions.md`, `docs/NotebookLM/05-knowledge-graph.md` (deleted), new `tests/test_docs_examples.py`.
- **Public API / runtime behavior**: none. No `src/` code changes; the `arlogi` wheel and the `arlogi[otel]` extra are unaffected.
- **Developer workflow**: `uv sync` no longer installs `graphifyy` and its ~20 tree-sitter/numpy/networkx transitive packages; `radon` remains available through `dev`. Anyone invoking the graphify rebuild command from `CLAUDE.md` loses it (intended).
- **CI**: jobs install only the requested group (`test` or `docs`) plus the project; `uv run` no longer re-syncs.

## Non-goals

- Any change to `src/arlogi/` code or runtime behavior (owned by the sibling changes).
- Rewriting `CHANGELOG.md` history, archived OpenSpec changes, or `docs/_audit_/` reports that mention graphify.
- Changing `ruff` rule selection (the docs are corrected to match `.ruff.toml`, not vice versa).
- Restructuring MkDocs navigation or the C4 documentation set beyond replacing private-API usage and stale call signatures.
- Audit findings other than DA-003, DA-014, DA-015, DA-016, DA-023, DA-024.
