# Palm examples

Runnable flow and process definitions for learning and manual testing. The CLI loads every `*.py` file in `definitions/` on startup (except modules prefixed with `_`).

## Layout

```
examples/
└── definitions/
    ├── onboard.py           # Onboarding wizard
    ├── data_ingestion.py    # Dataset registration + ETL stub
    ├── approval_workflow.py # Spend approval
    └── quick_wizard.py      # Minimal two-step demo
```

Each module exposes `register_definitions(repository)` which:

1. Optionally registers **commit handlers** on `default_commit_registry()`
2. Persists flows and processes via `repository.save_flow` / `save_process`

## Onboarding (`onboard`)

Transactional wizard with validation, auto-generated **summary**, and **commit** steps.

- **Validation:** name length, email regex, role choice
- **Commit hook:** `persist_profile` — builds a profile dict from answers

```bash
palm wizard start onboard
```

## Data ingestion (`data-ingestion`)

Models registering a dataset before running a pipeline.

- **Validation:** dataset name pattern, non-empty source URI
- **Resource step:** `verify_source` uses the `rest` provider (`resource_provider` / `resource_id`)
- **Commit hook:** `register_dataset`
- **Process:** `data-ingestion` includes `ingest-wizard` (wizard) and `ingest-etl` (ETL placeholder)

```bash
palm wizard start ingest-wizard
palm process submit data-ingestion   # submits both flows
```

## Approval workflow (`approval-workflow`)

Spend approval with structured validation and commit.

- **Validation:** title length, numeric amount, justification length
- **Commit hook:** `record_approval` — returns a pending approval ticket

```bash
palm wizard start approval
```

## Quick wizard (`quick`)

Two text steps (`alpha`, `beta`) with backtracking enabled — useful for resume demos.

```bash
palm wizard start quick
palm instance list
palm process resume <instance_id>
```

## Writing your own definitions

1. Create `my_flow.py` under `definitions/` (or `--data-dir definitions/`).
2. Define `FlowDefinition` / `ProcessDefinition` from `palm.definitions`.
3. Register commit handlers by name when using `include_commit: True`.
4. Implement `register_definitions(repository)` and call `save_flow` / `save_process`.

Wizard flow options commonly used in examples:

| Option | Purpose |
|--------|---------|
| `steps` | List of step dicts (slug, prompt, validation, `step_kind`) |
| `include_summary` | Auto summary step before commit |
| `include_commit` | Transactional commit step |
| `commit_hook` | Name registered on `default_commit_registry()` |
| `allow_backtrack` | Enable `back <instance> <slug>` in the CLI |

Commit handlers receive a `CommitContext` with `answers`, `state`, and optional `resource_engine` for `fetch_resource()`.

## Verify loading

```bash
palm doctor
palm process list
```