# DEVELOPMENT.md

## Setup

```bash
uv sync --group dev
uv pip install -e .
```

## Daily Commands

| Task | Command |
|------|---------|
| CLI (placeholder) | `palm` or `palm status` |
| Tests | `pytest` |
| Lint | `ruff check palm/ tests/` |
| Format | `ruff format palm/ tests/` |
| Type check | `mypy palm/` |

Or use `just` recipes (`just check`, `just test-quick`).

## Project Layout

```
palm/                  # Python package (repo root layout)
├── core/              # Pure engines — no external palm imports
├── patterns/          # Wizard, DAG, ETL
├── providers/         # REST, GraphQL, Postgres
├── storages/          # Memory, Postgres, MongoDB, filesystem
├── definitions/       # Flow and process specs
├── runtimes/          # CLI, embedded, server, daemon
└── utils/             # Shared non-core helpers

archive/               # Legacy code — do not import
tests/                 # Pytest suite
examples/              # Future runnable examples
```

## Adding a Pattern

1. Create `palm/patterns/<name>.py` subclassing `BasePattern`.
2. Call `pattern_registry.register("<name>", YourPattern)` at module bottom.
3. Export from `palm/patterns/__init__.py`.
4. Add tests in `tests/`.

## Adding a Storage Backend

1. Create `palm/storages/<name>.py` subclassing `BaseBackend`.
2. Register with `storage_registry`.
3. Add tests.

## Core Purity Check

```bash
# Must return no matches:
rg 'from palm\.(patterns|providers|storages|runtimes|definitions|utils)' palm/core/
```

## Archive Policy

All code under `archive/` is historical. Never add new features there.

---

Last updated: June 2026 (0.4.0-dev restructure)