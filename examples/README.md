# Palm examples

Runnable flow and process definitions for learning and manual testing. The CLI loads every `*.py` file in `definitions/` on startup via `ApplicationHost` (collapsed `all_in_one` profile).

## Layout

```
examples/
├── definitions/
│   ├── onboard.py           # Onboarding wizard
│   ├── data_ingestion.py    # Dataset registration + ETL stub
│   ├── approval_workflow.py # Spend approval
│   ├── quick_wizard.py      # Minimal two-step demo
│   ├── schema_wizard.py     # Flow + per-step state schemas
│   ├── parallel_demo.py     # Parallel branches + sub-workflows
│   ├── todo_builder.py      # Collection step + todo list schemas
│   └── transform_*.py       # Transform rule demos
└── full_demo.py             # ApplicationHost end-to-end script
```

Each definition module exposes `register_definitions(repository)` which:

1. Optionally registers **commit handlers** on `default_commit_registry()`
2. Optionally registers **compensation handlers** on `default_compensation_registry()` (undo on commit failure)
3. Persists flows and processes via `repository.save_flow` / `save_process`

## Running examples

All commands use the host-backed CLI (command bus for writes, query bus for reads):

```bash
palm flow start onboard          # recommended entry
palm instance list               # CQRS projection
palm status <instance_id>        # read model + live job
palm doctor                      # host roles, plugins, instances
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

Dynamic **todo list wizard** using the `collection` step kind.

```bash
palm flow start todo-builder
palm status <instance_id>
```

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