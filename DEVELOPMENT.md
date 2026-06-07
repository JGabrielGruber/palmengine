# DEVELOPMENT.md

Guide for contributors working on Palm **0.6.0**.

## Setup

```bash
uv sync --group dev --extra cli   # recommended: includes Rich + REPL
uv pip install -e .
just dev          # optional: sync + pre-commit + format
```

The **cli** extra installs Rich and prompt-toolkit for `palm` and the REPL.

## Daily commands

| Task | Command |
|------|---------|
| REPL | `palm` or `palm repl` or `just palm-repl` |
| Diagnostics | `palm doctor` or `just palm-doctor` |
| Version (full) | `palm version --full` or `just palm-version` |
| E2E demo script | `just demo-full` |
| Short status | `palm status` |
| Full status | `palm status --full` |
| Tests | `pytest` or `just test-quick` |
| Lint | `ruff check src/palm/ tests/` |
| Format | `ruff format src/palm/ tests/` |
| Type check | `mypy src/palm/` |
| Fast gate | `just check` |
| Full gate | `just full-check` |

## Project layout

```
src/palm/
├── core/              # Pure engines — no external palm imports
├── patterns/          # Wizard, DAG, ETL (+ commit registry, validation)
├── providers/         # REST, GraphQL, Postgres
├── storages/          # Memory, Postgres, MongoDB, filesystem
├── definitions/       # FlowDefinition, ProcessDefinition
├── executions/        # Executor, repositories, builder, instance sync
├── instances/         # ProcessInstance, status history
├── runtimes/
│   ├── embedded.py    # EmbeddedRuntime
│   ├── cli.py         # Entry point
│   └── cli_pkg/       # REPL, doctor, commands
└── utils/

examples/definitions/  # Auto-loaded by CLI (see examples/README.md)
archive/               # Legacy — do not import
tests/
```

## Working with the CLI

Example definitions register on every CLI start:

```bash
palm doctor
palm process list
palm wizard start onboard
```

Drive wizards in the REPL or one-shot:

```bash
palm input <instance_id> <value>
palm back <instance_id> <step_slug>
palm process resume <instance_id>
```

### Shared storage for resume demos

In-memory storage is per `EmbeddedRuntime` unless you pass a shared `StorageEngine`:

```python
from palm.core import StorageEngine
from palm.runtimes.cli_pkg.bootstrap import bootstrap_runtime, shutdown_context

storage = StorageEngine()
storage.initialize(backend="memory")
ctx = bootstrap_runtime(storage=storage)
# … submit, persist …
shutdown_context(ctx)
# New context with same storage object can resume instances
```

## Adding a pattern

1. Create `palm/patterns/<name>.py` subclassing `BasePattern`.
2. Call `pattern_registry.register("<name>", YourPattern)` at module bottom.
3. Export from `palm/patterns/__init__.py`.
4. Extend `executions/builder.py` if the pattern has flow options.
5. Add tests in `tests/`.

## Adding example definitions

1. Add `examples/definitions/<name>.py`.
2. Implement `register_definitions(repository)`.
3. Register commit handlers on `default_commit_registry()` when using `commit_hook`.
4. Run `palm doctor` to confirm catalog counts.

## Adding a storage backend

1. Create `palm/storages/<name>.py` subclassing `BaseBackend`.
2. Register with `storage_registry`.
3. Add tests.

## Core purity check

```bash
just guard-core
# or:
rg 'from palm\.(patterns|providers|storages|runtimes|definitions|utils)' src/palm/core/
```

Must return no matches.

## Archive policy

All code under `archive/` is historical. Never add new features there.

## Testing focus areas

| Area | Tests |
|------|-------|
| Core orchestration | `tests/test_orchestration.py` |
| Wizard pattern | `tests/test_wizard.py` |
| Executions / builder | `tests/test_executions.py` |
| Instances / resume | `tests/test_instances.py` |
| Embedded API | `tests/test_embedded.py` |
| CLI dispatch | `tests/test_cli.py` |

## Related documents

- [SCOPE.md](SCOPE.md) — vision, scope, and roadmap
- [ARCHITECTURE.md](ARCHITECTURE.md) — layers, BT model, middleware
- [README.md](README.md) — quick start and CLI
- [CHANGELOG.md](CHANGELOG.md) — release history

---

Last updated: June 2026 (0.6.0)