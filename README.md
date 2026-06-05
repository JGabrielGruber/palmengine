# Palm Engine

**Palm** is a lightweight orchestration engine for multi-step transactional workflows — interactive wizards, DAG pipelines, and ETL processes.

Version **0.4.0-dev** introduces a clean layered architecture with a **pure core** and registry-based extension.

---

## Quick Start

```bash
uv sync --group dev
uv pip install -e .
palm status
```

---

## Project Structure

```
palm/                      # Python package
├── core/                  # Pure foundational engines (no external palm imports)
│   ├── behavior_tree/     # Pattern execution + blackboard
│   ├── resource/          # Provider coordination
│   ├── storage/           # Backend coordination
│   ├── orchestration/     # Job lifecycle
│   ├── context/           # Scoped metadata
│   ├── event/             # Observability bus
│   └── auth/              # Auth primitives
├── patterns/              # wizard, dag, etl
├── providers/             # rest, graphql, postgres
├── storages/              # memory, postgres, mongodb, filesystem
├── definitions/           # flow, process
├── runtimes/              # cli, embedded, server, daemon
└── utils/

archive/                   # Legacy pre-0.4.0 code (reference only)
tests/
examples/
```

---

## Architecture

| Layer | Purpose |
|-------|---------|
| **Core** | Abstract engines, registries, shared primitives — imports only from `palm.core` |
| **Patterns / Providers / Storages** | Concrete implementations registered at import time |
| **Definitions** | Declarative flow and process specs |
| **Runtimes** | How Palm runs (CLI today; server/daemon planned) |

See [ARCHITECTURE.md](ARCHITECTURE.md) and [AGENTS.md](AGENTS.md) for full rules.

---

## CLI Entry Point

The `palm` command is registered in `pyproject.toml`:

```toml
[project.scripts]
palm = "palm.runtimes.cli:main"
```

Commands (placeholder):

- `palm` / `palm status` — show engine readiness
- `palm version` — print version

---

## Development

```bash
pytest
ruff check palm/ tests/
mypy palm/
just check
```

See [DEVELOPMENT.md](DEVELOPMENT.md).

---

## Migration from 0.3.x

Legacy CLI, wizards, and the old behavior-tree/orchestration implementations are under **`archive/`**. New work targets `palm/core/` and the concrete layers above — not `archive/`.

---

## License

MIT