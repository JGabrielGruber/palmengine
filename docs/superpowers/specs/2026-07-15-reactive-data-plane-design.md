# Reactive Data Plane — Design Specification

| Field | Value |
|-------|--------|
| **Date** | 2026-07-15 |
| **Status** | Approved for 0.45 track |
| **Vision** | [docs/VISION-0.45.md](../../VISION-0.45.md) |
| **Plan** | [docs/superpowers/plans/2026-07-15-reactive-data-plane-0.45.md](../plans/2026-07-15-reactive-data-plane-0.45.md) |

---

## Why same-process ingress before examples

Stream inbound today can fall back to HTTP journal poll, but **same-host dogfood** still uses loopback (`PALM_ORIGIN_URL`, WS to self). That is:

- Extra moving parts (port, auth, reconnect) unrelated to the watchdog logic
- Easy to misconfigure in docs and CI
- Not the ingress model we want operators to learn

The system event-watch example should use **in-process** event subscription. Shipping definitions on loopback would encode a workaround as canonical Palm style.

**Ordering rule:** Phase A (data plane) → Phase C (ingress) → Phase B (definitions). Migrations follow a proven stack.

---

## Layer model

| Plane | Container | Consumed by |
|-------|-----------|-------------|
| Signal | `WorkIntent.payload` | Drain, doctor, tests |
| Observability | `SubmitFlowCommand.metadata` → `job.metadata` | Inspect, journal |
| Data | `SubmitFlowCommand.state` → blackboard | Transforms, resource leaves |

Today work drain calls `run_wizard({"flow_name", "metadata": payload})` but `flow_command_from_body` ignores `metadata` — bug, not convention.

---

## Phase A — Data plane (0.45.1)

### 1. `flow_command_from_body`

Extend [src/palm/services/execution/flows/service.py](../../src/palm/services/execution/flows/service.py):

- Read optional `metadata` dict and `state` from body on all branches (`flow`, `wizard`, `flow_name`).
- Pass through to `SubmitFlowCommand`.
- DRY duplicate in [jobs.py](../../src/palm/runtimes/server/surfaces/rest/handlers/jobs.py).
- Fix MCP [in_process.py](../../src/palm/runtimes/mcp/in_process.py) `submit_flow` to forward `command.metadata` and `command.state`.

### 2. `coerce_job_state`

New [src/palm/common/executions/job_state.py](../../src/palm/common/executions/job_state.py):

- `dict` → `BlackboardState`
- `BlackboardState` passthrough
- `None` → `None`

Use in `prepare_flow_submission`.

### 3. `work.seed_state`

Extend `InboundWork` in [inbound.py](../../src/palm/common/resource/inbound.py):

```python
seed_state: dict[str, str] = field(default_factory=dict)
# target_key: path_in_payload
```

Resolver in [src/palm/common/work/seed_state.py](../../src/palm/common/work/seed_state.py) using existing `jsonpath_get`.

At signal time ([inbound_service.py](../../src/palm/app/host/inbound_service.py)):

```python
if spec.work.seed_state:
    payload["_seed_state"] = resolve_seed_state(spec.work.seed_state, payload)
```

Work drain ([application_host.py](../../src/palm/app/host/application_host.py)):

```python
seed = payload.pop("_seed_state", None)
run_wizard({"flow_name": flow_id, "metadata": payload, "state": seed})
```

### 4. `append_item`

New rule in [append_item.py](../../src/palm/common/transforms/rules/append_item.py).

- Input: single item (`context.value` from `source_key`)
- Read list from `context.state` at `options.list_key` or `options._target_key`
- `prepend` default `true`, `max_items`, `unique_field` optional
- Output: updated list → written to `target_key` by TransformLeaf

Inject `_target_key` in `TransformEngine.apply_to_state`.

### 5. `put_resource`

New rule — pipeline persist without wizard:

```yaml
- name: persist
  source_key: events
  rule: put_resource
  options:
    resource: palm-system-event-log
    action: put
```

Invokes `ResourceEngine` with value at `source_key`. Required before Phase B can stay definition-only.

---

## Phase C — Same-process ingress (0.45.2)

### Option A: `mode: internal` (preferred)

On palm provider resources with `metadata.inbound`:

```yaml
metadata:
  inbound:
    enabled: true
    mode: internal
    event_types: [resource.changed, job.completed, inbound.received]
    store_resource: palm-system-event-inbox
    work:
      flow_id: palm-system-watch-event
      seed_state:
        event: inbound.payload
```

`InboundBindingService` subscribes to host `EventEngine` when mode is `internal` — same code path as stream/webhook after envelope normalize (no background HTTP/WS worker).

### Option B: `on_event` trigger

Extend [triggers/parse.py](../../src/palm/common/triggers/parse.py) with `kind: on_event` and `event_types: [...]`. Reuses `TriggerRegistry` + work drain; does not require inbound metadata on a palm resource.

**0.45.2 ships one.** Internal mode keeps inbound semantics unified; `on_event` is lighter if internal mode slips.

---

## Phase B — Coherence (0.45.3)

Definitions only (no new engine fiction):

| Asset | Role |
|-------|------|
| `palm-system-event-inbox` | kv, `store_resource` target |
| `palm-system-event-log` | kv, `analytics.published` |
| `palm-system-events-watch` | palm inbound `mode: internal` |
| `palm-system-watch-event` | pipeline: map_fields → append_item → put_resource |
| Dashboard tile | table on log dataset |

Coconut: migrate one non-interactive path from wizard resource chain to pipeline.

---

## Acceptance criteria

| Release | Done when |
|---------|-----------|
| 0.45.1 | Drain submits inbound webhook; job.metadata has `inbound`; pipeline reads seeded `event`; append + put_resource tests green |
| 0.45.2 | Same-process event fires watchdog without `PALM_ORIGIN_URL` loopback |
| 0.45.3 | System dashboard shows shaped event log; coconut slice uses pipeline pattern |