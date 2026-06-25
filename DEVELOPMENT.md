# DEVELOPMENT.md

Guide for contributors working on Palm **0.13.13** (Provider apps + Wizard Experience + Compositional Power).

## Setup

```bash
git clone https://github.com/JGabrielGruber/palmengine.git && cd palmengine
uv sync --group dev --extra cli   # recommended: includes Rich + REPL
uv pip install -e ".[cli]"       # editable install (PyPI name: palmengine)
just dev                          # optional: sync + pre-commit + format
```

The **cli** extra installs Rich and prompt-toolkit for `palm` and the REPL.

**PyPI vs import:** distribution name is `palmengine`; Python package and CLI remain `palm`. End-user install: `pip install palmengine[cli]`.

## Daily commands

| Task | Command |
|------|---------|
| REPL | `palm` or `palm repl` or `just palm-repl` |
| Diagnostics | `palm doctor` or `just palm-doctor` |
| Version (full) | `palm version --full` or `just palm-version` |
| E2E demo script | `just demo-full` |
| Dashboard | `palm status` or `just palm-status` |
| Detailed dashboard | `palm status --full` or `just palm-status-full` |
| Live refresh | `palm status -r` (REPL/TTY) |
| Tests (full) | `pytest` or `just test-quick` (~8s) |
| Tests (fast) | `pytest --fast` (skips slow integration) |
| Lint | `ruff check src/palm/ tests/` |
| Format | `ruff format src/palm/ tests/` |
| Type check | `mypy src/palm/` |
| Fast gate | `just check` |
| Full gate | `just full-check` |

## Type checking

Mypy runs in **strict** mode on all of `src/palm/` (`pyproject.toml` → `[tool.mypy]`).
`just full-check` includes `mypy`; the tree should stay at **zero errors**.

**Guidelines during beta:**

- Prefer precise types over `Any` in `palm/common/`, `palm/runtimes/`, and `palm/app/`.
- Use `@overload` + `isinstance` branches when a public API accepts both definitions and repository string refs.
- Lazy exports in `palm.common.__getattr__` are allowed; new coordination code should use normal imports.
- Reserve `# type: ignore` for third-party stubs or genuinely dynamic boundaries (e.g. pattern registry hooks) — add a one-line comment when used.
- `palm/core/` stays typed but must never import outer layers (enforced by `just guard-core`).

## Project layout

```
src/palm/
├── app/               # ApplicationHost, PalmApp (infra), settings, host roles
├── core/              # Pure engines — no external palm imports
├── patterns/          # Wizard, DAG, ETL (+ commit registry, validation)
├── providers/         # REST, GraphQL, Postgres
├── storages/          # Memory, Postgres, MongoDB, filesystem
├── definitions/       # FlowDefinition, ProcessDefinition
├── common/            # Shared coordination (executions/, plans/, hooks/, persistence/, managers/, storage/, runtimes/)
│   └── runtimes/      # BaseRuntime, RuntimeHost, wiring, schedulers, runtime hooks
├── instances/         # ProcessInstance, StateSnapshot, status history
├── runtimes/          # Concrete surfaces (thin packages on common.runtimes)
│   ├── embedded/      # EmbeddedRuntime
│   ├── daemon/        # DaemonRuntime
│   ├── server/        # ServerRuntime + HTTP surfaces (REST, Explorer SSR)
│   │   └── surfaces/ssr/explorer/  # Palm Explorer pages, forms, actions
│   └── cli/           # Entry point + commands/ (one-shot) + tui/ (REPL) + shared/
└── utils/

examples/definitions/  # Auto-loaded by CLI (see examples/README.md)
archive/               # Legacy — do not import
tests/
```

Runtime imports: `palm.common.runtimes` for shared infrastructure;
`palm.runtimes.<name>` for concrete surfaces; `palm.runtimes.cli.commands` / `.tui` / `.shared` for CLI layers.

## Working with the CLI

The CLI is a **thin client of `ApplicationHost`** — bootstrap via
:func:`~palm.app.session.create_cli_host` (collapsed ``all_in_one`` profile).
Commands route through the host command bus; queries use projections.
No manual runtime assembly in command handlers.

| Mode | How | Persists? |
|------|-----|-----------|
| Default (dev) | `palm` / `palm repl` | No — in-memory; startup warns |
| Durable (local) | `PALM_STORAGE_BACKEND=filesystem` | Yes — under `PALM_DATA_DIR` (default `./data`) |
| Override | `palm --storage-backend filesystem --data-dir ./data` | Yes |

Environment variables load via `PalmSettings` (`PALM_*` prefix). CLI flags override
env **only when explicitly passed** — omit `--storage-backend` to respect
`PALM_STORAGE_BACKEND`.

Settings precedence (highest last): `PALM_*` env → `--config` file → CLI flags.

```bash
export PALM_STORAGE_BACKEND=filesystem
export PALM_DATA_DIR=./data
export PALM_ENABLE_STATE_SNAPSHOT=true   # optional snapshot history

palm doctor                              # persistence mode + active instance summary
palm wizard start onboard
palm instance list                       # active instances (non-terminal) by default
palm instance list --all --format json   # scripting output
palm instance prune --dry-run            # preview terminal cleanup
palm status                              # active instance when one is set
palm status <id>                         # prefix ids from list work
```

Global flags live in `palm/runtimes/cli/shared/args.py` (`-b`, `-d`, `--config`, `-S`,
`--max-loaded-instances`, `--scheduler`, `--format`, …). Parsed into
`CliInvocation` and merged via `settings_from_invocation()`.

Instance **reads** (`list`, `status`, `snapshots`) resolve through the host query
bus and projections. **Writes** (`flow start`, `input`, `resume`) use the command
bus via `CliContext.submit_*` helpers. REPL tab-completion suggests commands,
definitions, and instance ids from the projection-backed list.

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

### Preferred bootstrap (ApplicationHost)

Use :class:`~palm.app.host.ApplicationHost` for services, scripts, and tests that
mirror production wiring (CQRS, projections, outbox, compensation):

```python
from pathlib import Path

from palm.app import ApplicationHost, HostProfile, PalmSettings

settings = PalmSettings(storage_backend="filesystem", data_dir=Path("data"))
with ApplicationHost(settings, profile=HostProfile.all_in_one()) as host:
    job = host.submit_flow("onboard")
    rows = host.list_instance_views(include_terminal=False)
```

CLI equivalent: :func:`~palm.app.session.create_cli_host` (same profile).

Multi-role deployment:

```python
from palm.app import ApplicationHost, HostProfile

# Master + workers in one process (tests)
profile = HostProfile(master=True, worker=True, worker_count=2)
with ApplicationHost(profile=profile) as host:
    job = host.submit_flow("quick")  # routed to a worker runtime
```

Blocking standalone process: ``run_host("master")`` or ``palm host master``.

### Low-level embedding (PalmApp)

Use :class:`~palm.app.PalmApp` directly when testing runtime registry behaviour
without host overhead:

```python
from palm.app import PalmApp, PalmSettings

with PalmApp(PalmSettings(load_example_definitions=False)).bootstrap() as app:
    app.create_runtime("embedded", autostart=True)
    app.load_definitions()
    job = app.submit_flow("onboard")
```

Pass an existing ``StorageEngine`` to ``ApplicationHost(..., storage=storage)``
or ``PalmApp(storage=storage)`` when resuming across separate lifetimes.

Environment variables (prefix `PALM_`):

```bash
export PALM_STORAGE_BACKEND=filesystem
export PALM_DATA_DIR=./data
```

:class:`~palm.common.storage.StorageFactory` and ``runtime_start_options()`` wire
storage automatically on host/runtime start.

### InstanceManager

:class:`~palm.common.managers.InstanceManager` coordinates instance lifecycle across
runtimes — LRU cache, active tracking, lightweight summaries, and startup
reconciliation. Access via ``app.instance_manager`` or ``runtime.instance_manager``.

```python
# Via host (preferred — uses projections)
rows = host.list_instance_views(include_terminal=True)
snapshots = host.list_instance_snapshots("inst-abc")

# Via PalmApp infra (authoritative store)
summaries = app.list_instance_summaries()
instance = app.instance_manager.acquire("inst-abc")
```

**Settings** (``PALM_*`` env vars):

| Setting | Default | Purpose |
|---------|---------|---------|
| `max_loaded_instances` | 128 | LRU cache size for loaded `ProcessInstance` objects |
| `max_concurrent_active` | 32 | Cap on concurrently tracked active instances |
| `reconcile_instances_on_startup` | true | Mark stale `RUNNING` records; purge orphan index entries |

## State schemas & scoping

Palm 0.8 adds optional **schemas** and **named scopes** to execution state. Core stays pure — validation logic lives in `palm.core.context.state_schema`; wizard integration lives in `palm.patterns.wizard`.

### Quick reference

| Layer | Configure | Validates |
|-------|-----------|-----------|
| Flow | `FlowDefinition.state_schema` | Full answers at summary/commit |
| Step | `state_schema` on step dict | Each input before advancing |
| Scope | `bind_scope_schema(slug, schema)` | Values while scope is active |

### Example flow

```bash
palm wizard start schema-onboard
# name → age (integer) → role → summary → commit
palm status <instance_id>   # scope + validation context when waiting
```

### Snapshot metadata

`snapshot_state()` adds `__palm:meta` with `scope_stack`, `scope_schemas`, and `effective_schema`. Resume via `state_from_snapshot()` restores scopes — required for schema-aware wizard resume.

### Observability

```python
from palm.common.state import observe_state, StateObserverConfig
from palm.core.event import EventEngine

events = EventEngine()
observe_state(state, events, config=StateObserverConfig(emit_value_events=False))
```

Scope and schema events emit by default. Value events are off to avoid noise during wizard ticks.

### Tests

| File | Coverage |
|------|----------|
| `tests/core/test_state_scoping.py` | Scope stack, scoped values, schema binding |
| `tests/test_state_phase3.py` | Snapshot resume, context engine, wizard integration |
| `tests/test_state_snapshots.py` | `__palm:meta` round-trip |
| `tests/test_state_observability.py` | EventEngine observer |
| `tests/test_wizard_schema.py` | Flow schema on wizard steps |
| `tests/test_wizard_schemas_layered.py` | Layered validation + CLI coercion |

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
from palm.app import ApplicationHost, HostProfile, PalmSettings

settings = PalmSettings(
    enable_state_snapshot=True,
    snapshot_on_status=["WAITING_FOR_INPUT", "SUCCEEDED"],
    max_snapshots_per_instance=5,
)
with ApplicationHost(settings, profile=HostProfile.all_in_one()) as host:
    job = host.submit_flow("onboard")
```

Settings flow through ``runtime_start_options()`` into ``BaseRuntime.start()`` automatically.

### Inspect snapshots

**CLI** (REPL or one-shot):

```bash
palm instance snapshots <instance_id>
```

**Python API:**

```python
snapshots = host.list_instance_snapshots(instance_id)
for snap in snapshots:
    print(snap.status, snap.recorded_at, snap.current_step_slug)
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

See **[docs/PATTERN-APPS.md](docs/PATTERN-APPS.md)** for the full guide. Summary:

1. Create `palm/patterns/<name>/` with:
   - `pattern.py` — `BasePattern` subclass
   - `app.py` — `PatternApp` manifest (`palm_layers`, `registry_hooks`, optional `ready()`)
   - `bindings/definitions/builder.py` — `build(flow, context, pattern_cls)` for flow options
   - `registry.py` — `pattern_registry.register(...)` + `register_builder(...)` + `<name>_app.register()`
   - `__init__.py` — import `registry` for side effect
2. Add `"<name>"` to `INSTALLED_PATTERNS` in `patterns/_apps.py`.
3. Keep pattern-specific logic in `palm/patterns/<name>/` — **not** in `palm.common`. Run `just guard-common`.
4. Add tests in `tests/`.

## Collection step kind (wizard)

Use `step_kind: collection` for repeatable structured items (todo lists, line items, etc.).

| Option | Purpose |
|--------|---------|
| `collection_key` | Answer key for the assembled list (defaults to step `slug`) |
| `item_fields` | Per-item field defs — same shape as wizard step dicts |
| `min_items` | Minimum count before "continue" succeeds |
| `label_field` | Field slug used for item labels and partial search (auto-detected if omitted) |

Implementation lives in `palm/patterns/wizard/flow/collection/`:

- `config.py` — field config parsing
- `state.py` — phases, draft, scopes
- `selection.py` — compact edit/remove item lookup
- `phases/` — behavior-tree collection subtree (menu, select, fields, remove)

Tests: `tests/test_wizard_collection.py`, `tests/test_collection_selection.py`.

**Best practices:**

- Align `item_fields` schemas with flow `state_schema` `items` definition
- Use `label_field` when the display field is not `title`/`name`
- Omit optional empty fields from drafts (handled automatically)
- Test choice fields with numeric input (`1`, `2`) and partial strings

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
- Use `ApplicationHost.start()` or `PalmApp.bootstrap()` before serving traffic in multi-threaded deployments.

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
| Wizard pattern | `tests/test_wizard.py`, `tests/test_wizard_schema.py` |
| Collection steps | `tests/test_wizard_collection.py`, `tests/test_collection_selection.py` |
| Choice resolution | `tests/test_wizard_choice_resolution.py` |
| Parallel pattern | `tests/test_parallel_pattern.py`, `tests/core/test_parallel_node.py` |
| State schemas / scoping | `tests/core/test_state_scoping.py`, `tests/test_state_phase3.py` |
| Executions / builder | `tests/test_executions.py` |
| Instances / resume | `tests/test_instances.py` |
| State snapshot hook | `tests/test_state_snapshot_hook.py` |
| Registry thread safety | `tests/test_core_registry.py` |
| Embedded API | `tests/test_embedded.py` |
| CLI dispatch | `tests/test_cli.py`, `tests/test_cli_host_integration.py` |
| ApplicationHost / CQRS | `tests/test_application_host.py`, `tests/test_application_host_cqrs.py`, `tests/test_cqrs*.py` |

## Release & publishing

PyPI distribution: **`palmengine`** · import: **`palm`** · CLI: **`palm`**

```bash
just release-prep     # full-check + build + checklist
just publish-test     # TestPyPI (set TEST_PYPI_TOKEN)
just publish          # production PyPI (set PYPI_TOKEN)
```

Before publishing:

1. Bump `version` in `pyproject.toml` and `src/palm/__init__.py`
2. Update `CHANGELOG.md`
3. Run `just release-prep`
4. Tag `vX.Y.Z` and push; CI can publish via `.github/workflows/publish.yml`

Test install from TestPyPI:

```bash
pip install -i https://test.pypi.org/simple/ palmengine[cli]
```

## Extending CQRS

1. Add command/query dataclasses in `palm/common/cqrs/command.py` or `query.py`.
2. Handle in `PalmCommandHandlers` / `HostQueryHandlers` (`palm/app/host/cqrs_wiring.py`).
3. For new read models: subclass `Projection` in `palm/common/cqrs/projections/`, register in `ApplicationHost._wire_cqrs()`.

Host tests: `tests/test_application_host_cqrs.py`, `tests/test_cqrs_phase4.py`, `tests/test_cqrs_phase5.py`.

## Related documents

- [SCOPE.md](SCOPE.md) — vision, scope, and roadmap
- [ARCHITECTURE.md](ARCHITECTURE.md) — ApplicationHost, CQRS, reliability
- [MIGRATION-0.10.md](MIGRATION-0.10.md) — upgrade from 0.9.x bootstrap paths
- [README.md](README.md) — quick start and CLI
- [CHANGELOG.md](CHANGELOG.md) — release history

---

Last updated: June 2026 (0.13.13)