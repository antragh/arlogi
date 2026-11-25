# Design

## Context

- `pyproject.toml` defines `test`, `docs`, `graph` (`graphifyy` git source + `radon`), and `dev` (includes all three plus `commitizen`). No `[tool.uv] default-groups` is set, so uv enables `dev` by default for `uv sync` and for the implicit sync performed by `uv run`.
- Verified on disk (uv 0.11.31): `ci.yml`/`publish.yml` matrix `sync-args` are `--frozen --group test [--extra otel]`, `deploy-docs.yml` uses `--frozen --group docs`, and all `uv run` steps lack `--no-sync`. A dry run with `--no-dev` plans removal of `graphifyy`, `radon`, and `commitizen` from the current venv, confirming they are installed by default today.
- `graphify-out/` (44 tracked files) and `.graphifyignore` are only referenced by `CLAUDE.md`, `.gitignore` (`graphify-out/cache/`), `docs/NotebookLM/01-architecture-conventions.md` (embedded snapshots of `CLAUDE.md` and an old `pyproject.toml`), `docs/NotebookLM/05-knowledge-graph.md` (a dump of the graph report), the `ci-and-packaging` spec, `CHANGELOG.md`, archived changes, and audit reports. `docs/NotebookLM/*` is excluded from MkDocs (`exclude_docs`) and from the sdist, and nothing links to `05-knowledge-graph.md`.
- All six audit findings in scope were re-verified against current files (see "Finding verification" below). None were already fixed.
- Sibling changes `fix-core-logging-and-rotation-gaps` and `fix-otel-lifecycle-gaps` may change behavior that these docs describe (logger level parsing, `setup_logging` override validation, `JSONFileHandler` validation, rotation pruning, OTEL lifecycle). This change is applied after both.

## Goals / Non-Goals

**Goals:**

- Remove every live graphify artifact and dependency while keeping `radon` available to developers.
- Make CI/release/docs jobs install exactly the requested group and never re-sync.
- Make hand-authored docs match runtime behavior and cover the public API, with at least the caller-attribution assertions executed by the test suite.

**Non-Goals:**

- No `src/` changes; no doc rewrite beyond the cited findings; no MkDocs nav restructuring; no history rewrites (`CHANGELOG.md`, archive, audit reports).

## Decisions

### D1. CI dependency isolation: explicit CLI flags, not `UV_NO_DEV` / `UV_NO_SYNC` env vars

Add `--no-dev` to each `uv sync` (in the matrix `sync-args` strings and in `deploy-docs.yml`) and `--no-sync` to each subsequent `uv run` (`ruff check`, `ruff format --check`, `pytest`, `mkdocs build --strict`). `publish.yml`'s `uv build` step is unaffected (it does not sync).

Rationale:
- Flags are visible at the exact call site, greppable, and can be copied verbatim into `docs/DEVELOPER_GUIDE.md` and the README so contributors reproduce CI locally with the same commands (required by the new "Contributor commands match CI gates" requirement).
- Job-level `UV_NO_SYNC=1` would also apply to any future `uv sync`-adjacent commands and silently change their semantics; scoping env vars per step is more verbose than flags.
- `--no-dev` is preferred over `--no-default-groups` because `dev` is the only default group and `--no-dev` states the intent; both are equivalent today.

Alternative considered: `[tool.uv] default-groups = []` in `pyproject.toml`. Rejected: it changes the local developer default (`uv sync` would stop installing test/docs tooling), which is a bigger workflow change than this cleanup warrants.

### D2. Keep `radon` by moving it into `dev`

`radon>=6.0.1` becomes a direct `dev` entry; `dev` = `{test}`, `{docs}`, `commitizen`, `radon`. No new group is created for one package. `uv lock` regenerates the lockfile; `uv lock --check` guards it.

### D3. Graphify artifact handling

- Delete `graphify-out/` via `git rm -r` and `.graphifyignore`; delete the `.gitignore` line `graphify-out/cache/` (with its preceding blank line if it leaves a double blank).
- `CLAUDE.md`: replace the `## graphify` section with a short `## Source of truth` section stating that live `src/` and `openspec/specs/` are authoritative and that `docs/` must be kept in sync with them. Keep the existing Release & Publishing section untouched.
- `docs/NotebookLM/05-knowledge-graph.md`: delete (pure graph dump, unlinked, excluded from site and sdist).
- `docs/NotebookLM/01-architecture-conventions.md`: refresh the embedded `## FILE: CLAUDE.md` and `## FILE: pyproject.toml` snapshots from the post-change files so no graphify text remains. Other snapshot sections are left as-is.

### D4. Verifying documentation examples

Add `tests/test_docs_examples.py` that reads `docs/CALLER_ATTRIBUTION_EXAMPLES.md`, extracts the fenced `python` block under the "Unit Test Examples" heading, `exec`s it into a namespace, and calls each `test_*` function with the pytest `caplog` fixture. This keeps the documented code as the single source (no duplicated copy that can drift). It uses only the core package, so it runs in both the no-otel and otel CI jobs.

Other DA-014 fixes (syslog fallback text, `caller_depth=None` signatures, `SIM` removal, lambda removal, `module_levels` ordering) are verified by targeted `grep` checks in tasks plus the `mkdocs build --strict` gate, because they are prose/signature corrections rather than runnable assertions. Adding a general doc-snippet runner (e.g. `pytest --doctest-glob`) is deferred: most guide snippets require files, syslog sockets, or OTEL exporters and would need extensive fixtures.

### D5. Ordering with sibling changes

The implementation starts with a task that reads the applied/archived state of `fix-core-logging-and-rotation-gaps` and `fix-otel-lifecycle-gaps` and records any behavior they changed (signatures, accepted values, raised exceptions, validation rules). Documentation edits in later groups use the post-sibling runtime as the reference. If a sibling change is not yet applied, implementation of the docs groups pauses rather than documenting soon-to-change behavior.

### D6. Concurrency, error recovery, and no-otel boundary

- Concurrency/locking: not affected; no runtime code changes. CI matrix jobs run in isolated runners.
- Error recovery: unchanged runtime fail-open semantics. Documentation now states them accurately (syslog silent degradation only for the default `/dev/log`; custom addresses fail fast at construction). CI becomes fail-fast on lockfile drift via `--frozen` (already present) plus `uv lock --check` in verification.
- no-otel boundary: unaffected. The core-only CI job still syncs `--group test` without `--extra otel`; `--no-dev` strengthens isolation by guaranteeing no transitive package from `dev` leaks into that environment. The new docs-example test imports only `arlogi` core. Docs additions describe the existing lazy `__getattr__` boundary; they do not alter it.

## Finding verification

| Finding | Status on disk | Included |
| --- | --- | --- |
| DA-003 | `uv sync` lacks `--no-dev`, `uv run` lacks `--no-sync` in all 3 workflows and the `DEVELOPER_GUIDE.md` snippet | Yes |
| DA-014 | All 6 items present: wrong assertions/snippets, `lambda` at `USER_GUIDE.md:723,753`, `caller_depth=0` and unconditional silent-fallback claim in `API_REFERENCE.md`, `**module_levels` last in production dict, `SIM` row while `.ruff.toml` does not select `SIM` | Yes |
| DA-015 | `USER_GUIDE.md` has no `arlogi.otel` content; `ARCHITECTURE.md` file tree/component table omit `otel/` | Yes |
| DA-016 | No `LoggingConfigBuilder`, `rotate_json_logger`, `markup=False` in hand-authored docs; 16 `_apply_configuration` hits in C4 pages | Yes |
| DA-023 | README shows `ruff check .` labelled as formatting check and `mkdocs build` without `--strict` | Yes |
| DA-024 | `CLAUDE.md` graphify rules present | Yes (resolved by removal) |

No in-scope finding was excluded.

## Risks / Trade-offs

- [Sibling changes alter documented behavior after docs are written] → D5 ordering gate plus a final alignment task.
- [`--no-sync` hides a missing dependency in CI] → `uv sync --frozen` immediately precedes every `uv run`; a missing tool fails loudly with "command not found", which is the desired fail-fast signal.
- [Docs-example test couples tests to markdown structure] → extraction keyed on a stable heading; test fails with a clear message if the block is missing.
- [Developers relying on graphify lose it] → user confirmed nobody uses it; `CLAUDE.md` now points to live sources.

## Migration Plan

Single PR. Rollback is `git revert`; `uv.lock` is reverted with it. Local developers run `uv sync` once to drop graphify packages from their venv.
