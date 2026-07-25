## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:

- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- After modifying code files in this session, run `uv run python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"` to keep the graph current
- Always treat AST-based structure in graph.json as the source of truth if it conflicts with documentation in docs/

## Release & Publishing

- Use Conventional Commits (`feat: ...`, `fix: ...`, `docs: ...`, or `uv run cz commit`)
- To release a new version:
  1. Run `uv run cz bump` (bumps `pyproject.toml`, updates `CHANGELOG.md`, creates release commit & `vX.Y.Z` tag)
  2. Run `git push origin master --tags` (triggers GitHub Actions to run tests, publish to PyPI, create GitHub Release, and deploy docs)
