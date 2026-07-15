# Event plane — host vs runtime buses

**Status:** 0.45.5 contract  
**See also:** [VISION-0.45](VISION-0.45.md) Phase D / hygiene train

Palm runs **two** in-process `EventEngine` instances when `ApplicationHost` is started with a runtime:

| Bus | Property | Emits | Subscribers |
|-----|----------|-------|-------------|
| **Orchestration** | `runtime.event` | `job.completed`, `flow.session.succeeded`, `flow.session.failed`, `job.status_changed`, … | Internal inbound, work-drain triggers, orchestration projections |
| **Host coordination** | `host.event` | `host.started`, `host.shutdown`, `host.outbox.processed`, … | Event journal (durable append), host recorder, worker coordinator |

## Rule of thumb

**Anything that reacts to job or flow lifecycle must subscribe to `runtime.event`.**  
Do not emit or assert orchestration events on `host.event` — unit tests that did masked the 0.45.4 server bug (empty event tail on `palm host server`).

```python
# Correct — orchestration bus
host.app.runtime().event.emit("job.completed", job_id="j-1", flow="quick", status="SUCCEEDED")

# Wrong for orchestration — host coordination bus only
host.event.emit("job.completed", job_id="j-1")
```

## Wiring (ApplicationHost)

- `InboundBindingService` (`mode: internal`) → `_runtime_event_engine()`
- `WorkDrainService` trigger subscriptions → `_runtime_event_engine()`
- `OrchestrationEngine` → `runtime.event` (set at runtime bootstrap)
- Event journal + outbox reliable delivery → `host.event`

When the runtime is not started, `_runtime_event_engine()` falls back to `host.event` (embedded/tests without full server profile).

## Session terminal events (0.45.5)

On terminal job status, `OrchestrationEngine` emits:

| Job status | Event |
|------------|-------|
| `SUCCEEDED` | `flow.session.succeeded` |
| `FAILED` | `flow.session.failed` |

Payload includes `job_id`, `status`, and `flow_id` / `flow` when present in job metadata. These power `on_flow` triggers and definitions that list `flow.session.succeeded` in `inbound.event_types` (e.g. `palm-system-events-watch`).

## Doctor / ops

`host.control_plane_status()["event_plane"]` and REST/MCP doctor reports expose which bus inbound and work-drain use. CLI `palm doctor` prints an **Event Plane** table when host-backed.

## Tests

Use `tests.helpers.event_plane.runtime_event_engine(host)` and `emit_orchestration_event(...)` — never `host.event.emit` for orchestration contract tests.