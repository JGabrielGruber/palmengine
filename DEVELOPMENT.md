# DEVELOPMENT.md

Guide for contributors working on Palm **0.7.0**.

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
├── common/            # Shared coordination (executions/, plans/, hooks/, persistence/, managers/, storage/)
├── instances/         # ProcessInstance, StateSnapshot, status history
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

The CLI is a **thin client of `PalmApp`** — all wiring (storage, `InstanceManager`,
persistence hooks, definitions) happens in :func:`~palm.app.session.create_cli_app`.
No manual runtime assembly in command handlers.

| Mode | How | Persists? |
|------|-----|-----------|
| Default (dev) | `palm` / `palm repl` | No — in-memory; startup warns |
| Durable (local) | `PALM_STORAGE_BACKEND=filesystem` | Yes — under `PALM_DATA_DIR` (default `./data`) |
| Override | `palm --storage-backend filesystem --data-dir ./data` | Yes |

Environment variables load via `PalmSettings` (`PALM_*` prefix). CLI flags override
env **only when explicitly passed** — omit `--storage-backend` to respect
`PALM_STORAGE_BACKEND`.

```bash
export PALM_STORAGE_BACKEND=filesystem
export PALM_DATA_DIR=./data
export PALM_ENABLE_STATE_SNAPSHOT=true   # optional snapshot history

palm doctor          # shows durable vs in-memory notice
palm wizard start onboard
palm instance list   # via InstanceManager summaries
palm status <id>     # same manager; prefix ids from list work
```

All instance commands resolve through `CliContext.instance_manager` (backed by
`PalmApp`). Settings precedence: `PALM_*` env → explicit `settings` arg → CLI flags.

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
from pathlib import Path

from palm.app import PalmApp, PalmSettings

with PalmApp(PalmSettings(storage_backend="filesystem", data_dir=Path("data"))) as app:
    cli = app.create_runtime("embedded", name="cli", autostart=True)
    worker = app.create_runtime("daemon", name="worker", autostart=True)
    app.load_definitions()
    # … submit via cli, worker drives queued jobs …
```

Environment variables (prefix `PALM_`):

```bash
export PALM_STORAGE_BACKEND=filesystem
export PALM_DATA_DIR=./data
```

:class:`~palm.common.storage.StorageFactory` resolves backends lazily and builds
constructor options from :class:`~palm.app.settings.PalmSettings` (notably
``data_dir`` for the filesystem backend). ``BaseRuntime.start()`` and
``runtime_start_options()`` wire this automatically.

Pass an existing ``StorageEngine`` to ``PalmApp(storage=storage)`` when resuming
across separate app lifetimes (the CLI uses this pattern internally).

### InstanceManager

:class:`~palm.common.managers.InstanceManager` coordinates instance lifecycle across
runtimes — LRU cache, active tracking, lightweight summaries, and startup
reconciliation. Access via ``app.instance_manager`` or ``runtime.instance_manager``.

```python
summaries = app.list_instance_summaries()  # fast CLI-style listing
instance = app.instance_manager.acquire("inst-abc")  # load + mark active
snapshots = app.list_instance_snapshots("inst-abc")
```

**Settings** (``PALM_*`` env vars):

| Setting | Default | Purpose |
|---------|---------|---------|
| `max_loaded_instances` | 128 | LRU cache size for loaded `ProcessInstance` objects |
| `max_concurrent_active` | 32 | Cap on concurrently tracked active instances |
| `reconcile_instances_on_startup` | true | Mark stale `RUNNING` records; purge orphan index entries |

## State snapshots

Optional middleware (`StateSnapshotHook`) captures blackboard state at configured job status transitions. Disabled by default—no hook registered, zero overhead.

### Enable for local development

**Environment variables** (loaded by `PalmSettings`, prefix `PALM_`):

```bash
export PALM_ENABLE_STATE_SNAPSHOT=true
# Optional — defaults shown:
export PALM_SNAPSHOT_ON_STATUS='["WAITING_FOR_INPUT","SUCCEEDED","FAILED"]'
export PALM_MAX_SNAPSHOTS_PER_INSTANCE=10
```

**In tests or scripts:**

```python
from palm.app import PalmApp, PalmSettings
from palm.runtimes.embedded import EmbeddedRuntime

rt = EmbeddedRuntime()
rt.start(
    enable_state_snapshot=True,
    snapshot_on_status=["WAITING_FOR_INPUT", "SUCCEEDED"],
    max_snapshots_per_instance=5,
)
```

Or via `PalmApp` (settings flow through `runtime_start_options()` automatically):

```python
app = PalmApp(PalmSettings(enable_state_snapshot=True)).bootstrap()
app.create_runtime("embedded", autostart=True)
```

### Inspect snapshots

**CLI** (REPL or one-shot):

```bash
palm instance snapshots <instance_id>
```

**Python API:**

```python
snapshots = app.list_instance_snapshots(instance_id)
for snap in snapshots:
    print(snap.status, snap.recorded_at, snap.wizard_step_slug)
    print(snap.state_snapshot)  # blackboard dict
```

Snapshots persist with the `ProcessInstance` record in `InstanceRepository` (same storage backend as instances). Use a durable backend (`filesystem`, `postgres`, etc.) if snapshots must survive process restarts.

### How it relates to instance persistence

| Mechanism | Field | Purpose |
|-----------|-------|---------|
| `InstancePersistenceHook` | `state_snapshot` | Latest state — **resume authority** |
| `StateSnapshotHook` | `state_snapshots[]` | Historical ring buffer — **audit/debug** |

`StateSnapshotHook` runs after `InstancePersistenceHook` on `on_job_status_changed`. Snapshot failures are swallowed so jobs never fail because of snapshot I/O.

### Trade-offs

- **Storage cost:** each capture duplicates the blackboard dict; large wizards or high capture frequency increase backend size. Lower `max_snapshots_per_instance` or narrow `snapshot_on_status` to reduce footprint.
- **Performance:** one serialize + repository write per matching transition when enabled. Leave disabled in latency-sensitive paths unless you need the audit trail.
- **Replay:** inspection is supported today; programmatic time-travel replay from `state_snapshots[]` is a future extension.

### Tests

| File | Coverage |
|------|----------|
| `tests/test_state_snapshot_hook.py` | Hook behavior, ring buffer trim, non-blocking errors, embedded integration, `PalmApp` wiring |
| `tests/test_instances.py` | `ProcessInstance` persistence and resume (uses `state_snapshot`, not history) |

Run snapshot tests only:

```bash
pytest tests/test_state_snapshot_hook.py -q
```

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

1. Create `palm/storages/<name>/` with `backend.py` and `registry.py`.
2. Register with `storage_registry.register("<name>", YourBackend)`.
3. Add the name to `INSTALLED_STORAGES` in `storages/_apps.py` (use `OPTIONAL_STORAGES` when the backend needs extra dependencies).
4. Declare a uv extra in `pyproject.toml` when optional drivers are required.
5. Add tests; use `StorageFactory.ensure_registered("<name>")` in tests for optional backends.

## Registry registration and thread safety

Plugin registries (`pattern_registry`, `provider_registry`, `storage_registry`, pattern builders, commit handlers) are **thread-safe** but should be populated **once during bootstrap**, not from job-drive hot paths.

**Do:**

- Register patterns/providers/storages in each app's `registry.py`, imported via `INSTALLED_*` autoload lists.
- Register commit handlers in `register_definitions()` or module import side effects before serving traffic.
- Use `PalmApp.bootstrap()` (or `ensure_plugins()`) before creating runtimes in multi-threaded deployments.

**Avoid:**

- Calling `register()` from orchestration hooks, scheduler workers, or per-request handlers.
- Assuming single-threaded access — `QueuedScheduler`, daemon runtimes, and multi-runtime apps read registries concurrently.

Concurrency tests live in `tests/test_core_registry.py`. Run them after registry changes:

```bash
pytest tests/test_core_registry.py -q
```

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
| State snapshot hook | `tests/test_state_snapshot_hook.py` |
| Registry thread safety | `tests/test_core_registry.py` |
| Embedded API | `tests/test_embedded.py` |
| CLI dispatch | `tests/test_cli.py` |

## Related documents

- [SCOPE.md](SCOPE.md) — vision, scope, and roadmap
- [ARCHITECTURE.md](ARCHITECTURE.md) — layers, BT model, middleware
- [README.md](README.md) — quick start and CLI
- [CHANGELOG.md](CHANGELOG.md) — release history

---

Last updated: June 2026 (0.7.0)