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
├── app/               # PalmApp, PalmSettings, bootstrap, multi-runtime registry
├── core/              # Pure engines — no external palm imports
├── patterns/          # Wizard, DAG, ETL (+ commit registry, validation)
├── providers/         # REST, GraphQL, Postgres
├── storages/          # Memory, Postgres, MongoDB, filesystem
├── definitions/       # FlowDefinition, ProcessDefinition
├── common/            # Shared coordination (executions/, plans/, hooks/, persistence/)
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

### Shared storage and multi-runtime

Use :class:`~palm.app.PalmApp` to share storage across runtimes and sessions:

```python
from palm.app import PalmApp, PalmSettings

with PalmApp(PalmSettings(storage_backend="memory")) as app:
    cli = app.create_runtime("embedded", name="cli", autostart=True)
    worker = app.create_runtime("daemon", name="worker", autostart=True)
    app.load_definitions()
    # … submit via cli, worker drives queued jobs …
```

Pass an existing ``StorageEngine`` to ``PalmApp(storage=storage)`` when resuming
across separate app lifetimes (the CLI uses this pattern internally).

## Adding a pattern (Django-style app)

1. Create `palm/patterns/<name>/` with:
   - `pattern.py` — `BasePattern` subclass
   - `builder.py` — `build(flow, context, pattern_cls)` for flow options
   - `registry.py` — `pattern_registry.register(...)` + `register_builder(...)`
   - `__init__.py` — import `registry` for side effect
2. Add `"<name>"` to `INSTALLED_PATTERNS` in `patterns/_apps.py`.
3. Add tests in `tests/`.

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