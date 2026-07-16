# Work drain service

**WorkIntent** is Palm's deferred-work queue (0.37+): enqueue at signal time, **run when able**.

Sources that enqueue work:

- `metadata.triggers` on flows (e.g. `resource.changed` → `todo-analytics`)
- `metadata.inbound` on resources (webhook / stream / poll → reaction flow)
- Durable **schedules** (`tick_schedules`)

Execution does **not** happen on the HTTP or event reader thread. Something must **drain** the queue.

## Two modes

| Mode | When | Use case |
|------|------|----------|
| **Explicit** | `host.tick_work(limit=N)` | Tests, scripts, `all_in_one` / embedded CLI |
| **Background** | `WorkDrainService.start_background()` | `palm host server`, production reactive paths |

Background drain polls the durable store (like the outbox service), claims due intents, and submits flows when the host is able.

## Enable background drain

### Server profile (default since 0.44.1)

```bash
palm host server
```

The **`server`** host profile sets `enable_work_drain_service=True` on `DeploymentProfile`. No env var required for inbound webhooks or triggers to run.

### Environment override

```bash
# force on (any profile)
export PALM_ENABLE_WORK_DRAIN_SERVICE=1

# force off (even on server profile)
export PALM_ENABLE_WORK_DRAIN_SERVICE=0
```

Settings (`PalmSettings.enable_work_drain_service`) win when set explicitly; otherwise the host profile applies.

Related knobs:

| Variable | Default | Meaning |
|----------|---------|---------|
| `PALM_WORK_DRAIN_POLL_INTERVAL` | `1.0` | Background poll seconds |
| `PALM_WORK_DRAIN_BATCH_SIZE` | `10` | Intents per tick |
| `PALM_WORK_DRAIN_MAX_DEPTH` | `8` | Drop intents beyond depth (storm guard) |

## Explicit drain (embedded / tests)

```python
host.tick_work(limit=10)  # also runs due schedules when schedules=True (default)
```

Example packs (todos, inbound tests) use this path so behavior stays deterministic.

## Ops visibility

`host.control_plane_status()` and `GET /v1/api/system/doctor` → `control_plane`:

| Field | Meaning |
|-------|---------|
| `work_pending` | Queued WorkIntents not yet processed |
| `work_drain_running` | Background drain thread active |
| `work_dropped_depth` | Intents refused (depth limit) |
| `inbound_bindings` | Inbound listeners (0.43+) |

## Mental model

```text
signal (webhook, resource.changed, schedule)
  → WorkIntent enqueue (202 / durable store)
  → drain: tick_work() OR background service
  → submit_flow(target, payload)
```

Inbound specifically: [inbound_demo README](../examples/definitions/inbound_demo/README.md) · [VISION-0.43](VISION-0.43.md).

## Flow submission (0.45.6)

Work drain calls `FlowExecutionService.submit_flow_body()` — not `run_wizard()`. Both accept REST-shaped bodies (`flow_name`, `metadata`, `state`); `run_wizard` wraps the same path but returns an interactive `FlowSession`.

## Inbound coalesce vs debounce (0.45.6)

| Knob | Scope | Behavior |
|------|--------|----------|
| `coalesce_key` | WorkIntent store | One pending intent per key; **latest payload wins** on re-enqueue (burst collapse) |
| `coalesce_field` | Per-event | Builds key `inbound:{resource}:{field_value}` from envelope payload — separate intents per distinct field value |
| `debounce_seconds` | Inbound signal | **Defer** (trailing): signals in-window update pending envelope; after quiet period `flush_debounced()` enqueues **once** with latest payload. Poll mode uses debounce as poll interval instead. |

Loop guards (internal inbound): `skip_self` (default `true`) skips orchestration events for the bound `work.flow_id`; `skip_flows` adds more; `skip_event_types` defaults to `job.completed` + `flow.session.*`.

Explicit / server drain should call `host.tick_work()` — it flushes deferred inbound before claiming WorkIntents.

## Not the same as

- **Outbox** — reliable external delivery of events (webhooks to third parties)
- **`enable_webhook_dispatcher`** — dispatches journal events to configured URLs
- **Inbound REST** — ingress that *enqueues* work; drain *executes* it