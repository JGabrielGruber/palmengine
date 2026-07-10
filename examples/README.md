# Palm examples

Runnable flow and process definitions for learning and manual testing.  
`ApplicationHost` loads **definition packs** under `definitions/` on startup.

## Layout

```
examples/
├── definitions/
│   ├── coconut/             # Pack: resources first, then npc flow (__init__ order)
│   │   ├── __init__.py
│   │   ├── resources.py
│   │   └── npc.py
│   ├── todos/               # Pack: resources → todo-builder → todo-analytics
│   │   ├── __init__.py
│   │   ├── resources.py
│   │   ├── builder.py
│   │   └── analytics.py
│   ├── onboard.py           # Flat single-file demos (still supported)
│   ├── data_ingestion.py
│   ├── approval_workflow.py
│   ├── transform_*.py
│   └── …
└── full_demo.py
```

**Preferred:** multi-file **packages** with ordered `__init__.py`  
(`resources` before flows that `resource_ref` them). Relative imports only.

**Legacy:** flat `*.py` with `register_definitions(repository)`.

Each pack/module’s `register_definitions` may:

1. Register **commit / compensation** handlers  
2. `repository.save_flow` / `save_process` / `save_resource`

## Running examples

All commands use the host-backed CLI (command bus for writes, query bus for reads):

```bash
palm flow start onboard          # recommended entry
palm status                      # live projection dashboard
palm status --full               # detailed dashboard view
palm status -r                   # live refresh in REPL (2s)
palm instance list               # CQRS projection
palm status <instance_id>        # read model + live job
palm doctor                      # full health report
```

## Onboarding (`onboard`)

Transactional wizard with validation, auto-generated **summary**, and **commit** steps.

- **Validation:** name length, email regex, role choice
- **Commit hook:** `persist_profile` — builds a profile dict from answers

```bash
palm flow start onboard
```

**Compensation (optional):** register an undo handler for `persist_profile` on `default_compensation_registry()` if your commit performs partial external writes. See [MIGRATION-0.10.md](../MIGRATION-0.10.md).

## Data ingestion (`data-ingestion`)

Models registering a dataset before running a pipeline.

- **Validation:** dataset name pattern, non-empty source URI
- **Resource step:** `verify_source` uses the `rest` provider
- **Commit hook:** `register_dataset`
- **Process:** `data-ingestion` includes `ingest-wizard` and `ingest-etl`

```bash
palm flow start ingest-wizard
palm process submit data-ingestion
```

## Approval workflow (`approval-workflow`)

Spend approval with structured validation and commit.

```bash
palm flow start approval
```

## Schema wizard (`schema-onboard`)

Demonstrates **layered state schemas**, **step scopes**, and **schema-aware resume**.

```bash
palm flow start schema-onboard
palm instance list
palm status <instance_id>
palm process resume <instance_id>
```

## Parallel demo (`parallel-demo`)

Two multi-step wizard branches in parallel with isolated scopes and merge validation.

```bash
palm flow start parallel-demo
palm doctor
palm status <instance_id>
```

## Todo builder (`todo-builder`)

Dynamic **todo list wizard** using the `collection` step kind — ideal for Explorer collection UI demos.

```bash
palm flow start todo-builder
palm status <instance_id>
```

**Explorer (0.13):** with `ServerRuntime` running:

```bash
curl -s -X POST http://localhost:8080/v1/wizards \
  -H 'Content-Type: application/json' \
  -d '{"flow_name": "todo-builder"}'
# Open /explorer/instances/<instance_id> — Add New, edit/remove items, continue to summary
```

See [EXPLORER-WIZARD.md](../EXPLORER-WIZARD.md).

## Migrate instance demo (`migrate-instance-demo`)

Demonstrates **definition revision migration** (0.24.1–0.24.3): a source flow at
revisions 1 and 2, a registered migration rule, and an operator wizard that
dry-runs then applies the upgrade.

```bash
# Start a session pinned to revision 1
palm flow start migrate-demo-source
palm instance list   # note instance_id

# Operator wizard: confirm → dry-run → apply
palm flow start migrate-instance-demo
```

REST equivalent:

```bash
curl -s 'http://localhost:8080/v1/api/definitions/flows/migrate-demo-source/impact'
curl -s -X POST 'http://localhost:8080/v1/api/definitions/instances/<instance_id>/migrate' \
  -H 'Content-Type: application/json' \
  -H 'X-Palm-Subject: operator' \
  -d '{"target_revision": 2, "dry_run": true}'
```

## Coconut NPC (`coconut-npc`)

**Branching wizard reference** — hub-and-spoke topic menu, transform chain
(`string_format`, `lookup`), and `route_on_answer` / `complete_on` routing.
Dogfood profile for compositional interactive workflows (see [VISION-0.27.md](../docs/VISION-0.27.md));
not a game-NPC product direction.

```bash
palm flow start coconut-npc
```

Example path: name → reputation → topic hub → rumors/trade/about → farewell.

MCP agents can revise via `palm_design_propose_flow(base_flow_id="coconut-npc", …)`.

**KV persistence** (`coconut_resources.py` + `coconut_transforms.py`): after `player_name`, the
flow loads/saves a `player_profile` via `kv` (`backend: auto`) keyed by `player_name`.
Returning travelers get `visit_count > 1` and a "I remember you" greeting line.

## Quick wizard (`quick`)

Two text steps with backtracking — useful for resume demos.

```bash
palm flow start quick
palm instance list
palm process resume <instance_id>
```

## Programmatic demo (ApplicationHost)

[`full_demo.py`](full_demo.py) demonstrates the **recommended library path**:

1. Start `ApplicationHost` with shared `StorageEngine`
2. Register a flow and submit via `host.submit_flow()`
3. Shutdown (simulated session end)
4. Start a new host on the same storage and `host.resume_process()`

```bash
uv run python examples/full_demo.py
# or: just demo-full
```

```python
from palm.app import ApplicationHost, HostProfile, PalmSettings

with ApplicationHost(PalmSettings(), profile=HostProfile.all_in_one()) as host:
    job = host.submit_flow("onboard")
    host.provide_input(job.id, "Ada")
    views = host.list_instance_views()
```

## Writing your own definitions

1. Create `my_flow.py` under `definitions/` (or `--data-dir definitions/`).
2. Define `FlowDefinition` / `ProcessDefinition` from `palm.definitions`.
3. Register commit handlers when using `include_commit: True`.
4. Implement `register_definitions(repository)`.

Wizard flow options commonly used:

| Option | Purpose |
|--------|---------|
| `steps` | Step dicts (slug, prompt, validation, `step_kind`) |
| `include_summary` | Auto summary step before commit |
| `include_commit` | Transactional commit step |
| `commit_hook` | Name on `default_commit_registry()` |
| `allow_backtrack` | Enable `back <instance> <slug>` in CLI |
| `step_kind: collection` | Repeatable item builder |
| `step_kind: transform` | Apply transform rule/chain between steps |
| `params.route_on_answer` | Jump to step slug after choice input (hub menus) |
| `params.complete_on` | Finish wizard when input matches (farewell / exit) |

### Transform examples

| Flow | Pattern | Demonstrates |
|------|---------|--------------|
| `transform-demo` | pipeline | `rename_field`, `filter_items` |
| `transform-shaping` | pipeline | `calculate`, `lookup`, `conditional` |
| `transform-example` | wizard | `string_format` between input steps |
| `transform-formats` | pipeline | `json_load` → reshape → `csv_dump` |

Run `palm doctor` for all **22** built-in transform rules.

Commit handlers receive `CommitContext` with `answers`, `state`, and optional `resource_engine`.

## Verify loading

```bash
palm doctor
palm process list
palm version --full
```

## Further reading

- [README.md](../README.md) — installation and CLI reference
- [ARCHITECTURE.md](../ARCHITECTURE.md) — ApplicationHost, CQRS, reliability
- [MIGRATION-0.10.md](../MIGRATION-0.10.md) — upgrade from older bootstrap paths