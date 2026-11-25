## Source of truth

- Live source code under `src/` and OpenSpec specifications under `openspec/specs/` are the authoritative sources of truth for behavior, architecture, and invariants.
- Keep documentation under `docs/` and `README.md` synchronized with `src/` and `openspec/specs/`.

## Release & Publishing

- Use Conventional Commits (`feat: ...`, `fix: ...`, `docs: ...`, or `uv run cz commit`)
- To release a new version:
  1. Run `uv run cz bump` (bumps `pyproject.toml`, updates `CHANGELOG.md`, creates release commit & `vX.Y.Z` tag)
  2. Run `git push origin master --tags` (triggers GitHub Actions to run tests, publish to PyPI, create GitHub Release, and deploy docs)
