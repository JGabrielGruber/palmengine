# Palm examples

Runnable flow and process definitions for learning and manual testing. The CLI loads every `*.py` file in `definitions/` on startup (except modules prefixed with `_`).

## Layout

```
examples/
└── definitions/
    ├── onboard.py           # Onboarding wizard
    ├── data_ingestion.py    # Dataset registration + ETL stub
    ├── approval_workflow.py # Spend approval
    ├── quick_wizard.py      # Minimal two-step demo
    ├── schema_wizard.py     # Flow + per-step state schemas
    ├── parallel_demo.py     # Parallel branches + sub-workflows
    └── todo_builder.py      # Collection step + todo list schemas
```

Each module exposes `register_definitions(repository)` which:

1. Optionally registers **commit handlers** on `default_commit_registry()`
2. Persists flows and processes via `repository.save_flow` / `save_process`

## Onboarding (`onboard`)

Transactional wizard with validation, auto-generated **summary**, and **commit** steps.

- **Validation:** name length, email regex, role choice
- **Commit hook:** `persist_profile` — builds a profile dict from answers

```bash
palm flow start onboard
# wizard start onboard still works as a shortcut
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

## Schema wizard (`schema-onboard`)

Demonstrates **layered state schemas**, **step scopes**, and **schema-aware resume** (0.8+).

### Validation layers

| Layer | When | Where configured |
|-------|------|------------------|
| Built-in field rules | Each input | `field_type`, `required`, `choices` |
| Declarative rules | Each input | `validation` array on step dict |
| Per-step schema | Each input | `state_schema` on step dict |
| Flow schema | Summary + commit | `state_schema` on `FlowDefinition` |

### Scoping

Each wizard input step enters a named scope (the step slug). Per-step schemas bind to that scope. Prompt bundles and CLI panels expose `scope_stack`, `current_scope`, and `scope_depth` for debugging.

### CLI input coercion

The REPL delivers text input. When a step or flow schema expects `integer` or `number`, Palm coerces compatible strings before validation (e.g. `27` → `27`). Invalid coercion still fails with a clear message and keeps you on the current step.

```bash
palm wizard start schema-onboard
# Enter: Ada → 27 → developer → yes → yes
palm instance list
palm status <instance_id>    # shows scope + answers when waiting
palm process resume <instance_id>
```

### Resume

Snapshots embed `__palm:meta` with `scope_stack`, `scope_schemas`, and `effective_schema`. Resuming a waiting wizard restores the exact scope context — not just flat answers.

## Parallel demo (`parallel-demo`)

Runs **two multi-step wizard branches in parallel** with isolated scopes, per-step schemas, and merged validation.

- **Branches** — inline `pattern: wizard` or `flow_ref` to an existing flow
- **Per-step schemas** — integer age on alpha, enum role on beta
- **Merge** — `all`, `any`, or `first` strategy
- **Parent schema** — validates merged branch answers at completion
- **CLI** — REPL prompt shows `@parallel:<branch>`; `doctor` and `status` show branch progress

```bash
palm flow start parallel-demo
# or: palm start parallel-demo
# Example answers: Ada → 27 → Platform → developer → …
palm doctor
palm status <instance_id>
```

## Todo builder (`todo-builder`)

Dynamic **todo list wizard** using the new `collection` step kind.

- **Collection step** — add, edit, and remove items in a loop before continuing
- **Compact item selection** — edit/remove via menu action, then pick by number or partial title (`label_field`)
- **Per-item scopes** — `todos > item-N > field` for isolated editing
- **Per-field schemas** — title (required), optional due date, priority enum
- **Flow schema** — validates the full `todos` array at summary and commit
- **Resume** — list, draft, and editing phase preserved in snapshots

```bash
palm flow start todo-builder
# intro → Add (1) → fields → Edit an item (2) → milk → … → Remove an item (3) → 2 → yes → Continue → yes → yes
palm status <instance_id>
```

## Quick wizard (`quick`)

Two text steps (`alpha`, `beta`) with backtracking enabled — useful for resume demos.

```bash
palm wizard start quick
palm instance list
palm process resume <instance_id>
```

## State schemas — best practices

1. **Use flow schema for cross-field rules** — required keys, enums across the full answers object, summary/commit gates.
2. **Use per-step schema for immediate feedback** — type constraints (integer age, email format) on the active step.
3. **Prefer inline schemas in examples**; use `state_schema_ref` in production catalogs for reuse.
4. **Keep step slugs aligned** — flow schema property names should match step `slug` values.
5. **Test with string input** — CLI always sends strings; coercion handles common cases, but APIs can pass typed values directly.
6. **Enable snapshots for resume demos** — `PALM_ENABLE_STATE_SNAPSHOT=true` adds audit history; resume still uses the latest `state_snapshot`.

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
| `state_schema` | Flow-level JSON Schema on `FlowDefinition` |
| `state_schema` (step) | Per-step value schema in step dicts |
| `state_schema_ref` | Reference a named schema in the definition repository |
| `step_kind: collection` | Repeatable item builder with `item_fields` and `collection_key` |
| `step_kind: transform` | Apply a transform rule/chain (`source_key`, `target_key`, `rule`, `options`) |

### Transform examples

| Flow | Pattern | Demonstrates |
|------|---------|--------------|
| `transform-demo` | pipeline | `rename_field`, `filter_items` |
| `transform-shaping` | pipeline | `calculate`, `lookup`, `conditional` |
| `transform-example` | wizard | `string_format` between input steps |
| `transform-formats` | pipeline | `json_load` → reshape → `csv_dump` |

Run `palm doctor` to see all built-in transform rules with short descriptions.
| `item_fields` | Per-item field defs (slug, prompt, schema) for collection steps |
| `label_field` | Field slug for item labels and partial edit/remove search |
| `min_items` | Minimum items required before leaving a collection step |

Commit handlers receive a `CommitContext` with `answers`, `state`, and optional `resource_engine` for `fetch_resource()`.

## Full end-to-end demo

[`full_demo.py`](full_demo.py) runs without the REPL: register a flow, submit,
answer the first wizard step, stop the runtime, start a new runtime with shared
storage, resume, and complete summary + commit.

```bash
uv run python examples/full_demo.py
# or: just demo-full
```

## Verify loading

```bash
palm doctor                    # catalog + schema column on flows
palm process list
palm version --full
```