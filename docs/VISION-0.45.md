# VISION 0.45 — Reactive data plane

**Status:** Planning (0.45.0 docs) → implementation 0.45.1+
**Builds on:** [VISION-0.44](VISION-0.44.md) (inbound store, poll, stream, work drain)

## Problem

Inbound → WorkIntent → flow works, but the **data plane** has holes that force workarounds:

| Gap | Forces today | Maturity cost |
|-----|--------------|---------------|
| `flow_command_from_body` drops `metadata` / `state` | Work drain payload lost on submit | Reactive flows look broken while wired |
| No `work.seed_state` | Mandatory inbox `get` in every flow | Wizard-as-ETL becomes “the Palm way” |
| No `append_item` | kv `put` replaces; no ring buffer | Every log/tail invents merge logic |
| Stream inbound needs loopback URL | `PALM_ORIGIN_URL` / WS to self for same-host | Examples bake ceremony; not true dogfood |
| Pipeline has no `put_resource` | Wizard resource steps for persist | Pattern semantics lie |

**Principle:** Engine and ingress contracts first; definitions and migrations **prove** them — never define them.

## Release train

| Version | Scope |
|---------|--------|
| **0.45.0** | This vision + design spec + implementation plan |
| **0.45.1** | Phase A — metadata/state plumbing, `work.seed_state`, `append_item`, `put_resource` |
| **0.45.2** | Phase C — same-process inbound (`mode: internal` on palm resource **or** `on_event` trigger) |
| **0.45.3** | Phase B — system event-watch definitions + coconut pipeline migration slice |

Phase C before Phase B so the watchdog example does **not** ship on loopback/WS self-connect. Examples consume the real ingress contract.

```mermaid
flowchart LR
  docs[0.45.0 docs]
  phaseA[0.45.1 data plane]
  phaseC[0.45.2 same-process ingress]
  phaseB[0.45.3 examples plus migrations]
  docs --> phaseA --> phaseC --> phaseB
```

## Target flow (post 0.45.3)

```
palm resource (inbound internal/stream)
  → store_resource inbox (audit)
  → WorkIntent
  → drain: seed_state → SubmitFlowCommand.state
  → pipeline: map_fields → append_item → put_resource
  → kv log (analytics.published) → dashboard tile
```

## Phase A contracts (0.45.1)

### Submission plumbing

REST/MCP/work-drain bodies may include:

```json
{
  "flow_name": "my-pipeline",
  "metadata": { "inbound": {}, "source": "stream" },
  "state": { "event": {} }
}
```

`metadata` → job observability. `state` → blackboard seed (coerced to `BlackboardState`).

### `work.seed_state`

```yaml
metadata:
  inbound:
    store_resource: palm-system-event-inbox
    work:
      flow_id: palm-system-watch-event
      seed_state:
        event: inbound.payload
        source: source
```

Paths resolve against WorkIntent payload (dot or `$.` jsonpath). Engine stores resolved map as `_seed_state` on payload; drain strips it into `SubmitFlowCommand.state`.

`store_resource` + inbox remains the durable audit handoff; seed state removes mandatory inbox `get` on the happy path.

### `append_item` transform

```yaml
rule: append_item
options:
  max_items: 50
  unique_field: offset
  prepend: true
```

Appends `source_key` value into list at `target_key` (via `_target_key` from TransformEngine).

### `put_resource` transform

Thin persist leaf for pipelines — invoke resource `put` from blackboard `source_key` (unblocks definition-only watchdog).

## Phase C contracts (0.45.2)

**Preferred:** `metadata.inbound.mode: internal` on palm provider resources — subscribe to host `EventEngine` in-process (no HTTP/WS loopback).

**Alternative:** `metadata.triggers` `on_event` kind matching `resource.changed`, `job.completed`, `inbound.received`, etc.

Pick one for 0.45.2; document the other as follow-up if both are needed.

## Phase B (0.45.3)

- System pack: `palm-system-events-watch`, inbox, log, pipeline `palm-system-watch-event`, dashboard tile
- Coconut (or one slice): non-interactive wizard-ETL → pipeline

## Non-goals (0.45.x)

- Full system logger / journal-as-resource
- Mesh multi-worker inbound fan-out
- `InboundDefinition` kind
- Replacing inbox audit with seed-only

## References

- [WORK-DRAIN.md](WORK-DRAIN.md)
- [inbound_demo README](../examples/definitions/inbound_demo/README.md)
- Design: [docs/superpowers/specs/2026-07-15-reactive-data-plane-design.md](superpowers/specs/2026-07-15-reactive-data-plane-design.md)
- Plan: [docs/superpowers/plans/2026-07-15-reactive-data-plane-0.45.md](superpowers/plans/2026-07-15-reactive-data-plane-0.45.md)