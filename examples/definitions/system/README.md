# System pack — ops datasets & origin Palm resources

Definition-only pack: **`provider: palm`** system-read actions as published
analytics datasets + dashboards.

## Local datasets

| Dataset | Action | Notes |
|---------|--------|--------|
| `palm-system-jobs` | `list_jobs` | this host |
| `palm-system-waiting` | `list_waiting` | |
| `palm-system-instances` | `list_instances` | |
| `palm-system-flows` | `list_flows` | |
| `palm-system-resources` | `list_resources` | |
| `palm-system-instances-per-flow` | virtual | `count_by` on `flow_name` |
| `palm-system-event-log` | kv get | event watch tail (table) |
| `palm-system-events-watch` | internal inbound | `job.completed`, `flow.session.succeeded` only |

Dashboard: **`palm-system`** (includes **Event watch tail** tile)

### Event watchdog (0.45.3–0.45.5)

In-process ingress — no `PALM_ORIGIN_URL` loopback. **0.45.4** wires internal inbound to the runtime orchestration bus. **0.45.7** makes `put_resource` BATCH-mode safe for list tails (no `batch: false` on `persist_log`). See [docs/EVENT-PLANE.md](../../../docs/EVENT-PLANE.md) · [docs/TRANSFORMS.md](../../../docs/TRANSFORMS.md).

Loop guards:

- **Ingress:** `event_types` excludes `resource.changed` / `inbound.received`; engine skips self `job.completed` for the watch flow.
- **Pipeline:** `conditional` + `passthrough` drops rows for owned resources and this flow's own completions.

Read tail via resource invoke (0.45.8 shortcut) or explicit provider path:

```bash
# shortcut — provider resolved from definition
curl -s http://127.0.0.1:8080/v1/api/resources/palm-system-event-log/invoke \
  -H 'Content-Type: application/json' -H 'X-Palm-Subject: dev' \
  -d '{"action":"get"}'

# explicit provider
curl -s http://127.0.0.1:8080/v1/api/providers/kv/palm-system-event-log/invoke \
  -H 'Content-Type: application/json' -H 'X-Palm-Subject: dev' \
  -d '{"action":"get"}'
```

**Durable tail:** default dev server uses memory storage — restart clears the log. For ops dogfood use `PALM_STORAGE_BACKEND=filesystem` (see [docs/OPS.md](../../../docs/OPS.md)).

```bash
just palm-server
# doctor inbound_bindings · dashboard palm-system · tile event_log
```

```bash
just palm-server
# http://127.0.0.1:8080/analytics/?dashboard=palm-system
```

```python
host.analytics.query("palm-system-flows", profile="table")
# no remote_url — resource params are empty (local coordinator)
```

---

## Origin (remote) Palm — the proper way

**Origin is part of the ResourceDefinition**, not an analytics query param.

```text
ResourceDefinition
  name:     origin-system-flows
  provider: palm
  action:   list_flows
  params:   { remote_url: "https://b.example" }   ← contract
        │
        ▼
AnalyticsService.query("origin-system-flows")     ← only the dataset name
        │
        ▼
ResourceEngine merges definition.params → palm provider → HTTP to B
```

### Register from code

```python
from examples.definitions.system.origin_resources import (
    register_origin_system_resources,
)
from examples.definitions.system.origin_dashboard import (
    register_origin_system_dashboard,
)

register_origin_system_resources(
    host.app.repository(),
    "http://127.0.0.1:8090",
    name_prefix="origin",  # → origin-system-flows, …
    # remote_token="…",    # optional bearer for B
)
register_origin_system_dashboard(
    name_prefix="origin",
    remote_url="http://127.0.0.1:8090",
)

# Analytics never needs remote_url
host.analytics.query("origin-system-flows", profile="table")
host.analytics.query("origin-system-instances-per-flow", profile="series")
host.analytics.render_dashboard("origin-system")
```

### Register from env (pack load)

```bash
export PALM_ORIGIN_URL=http://127.0.0.1:8090
# optional:
# export PALM_ORIGIN_TOKEN=…
# export PALM_ORIGIN_PREFIX=origin   # default
just palm-server
# datasets: origin-system-* · dashboard: origin-system
```

### Origin dataset names (default prefix `origin`)

| Dataset | Source |
|---------|--------|
| `origin-system-jobs` | B via `list_jobs` |
| `origin-system-waiting` | B |
| `origin-system-instances` | B |
| `origin-system-flows` | B |
| `origin-system-resources` | B |
| `origin-system-instances-per-flow` | virtual over `origin-system-instances` |

### Anti-pattern (avoid in examples)

```python
# ❌ query-time routing — hides the resource contract
host.analytics.query(
    "palm-system-flows",
    params={"remote_url": "http://b:8080"},
)
```

Provider still **accepts** `remote_url` on invoke for power users / one-offs;
**examples and dashboards** always pin origin on the **definition**.

---

## Assist

Menu → **Analytics datasets** → `open:dataset:origin-system-flows`  
(with origin resources registered — preview uses definition params).

## Composition

- Same `items` envelope local vs origin.
- Multiple origins = multiple resource sets (`staging-system-flows`, …).
- Realtime event stream to the provider is **0.42** (P2); today is request/response.

## Design: propose / publish dashboard (0.41.2)

Dashboards are first-class design artifacts. Commit **registers** the definition
(durable via 0.41 store) — no instance migration.

```python
host.design.publish_dashboard({
    "name": "my-ops",
    "title": "My ops board",
    "tiles": [
        {"id": "flows", "dataset": "palm-system-flows", "profile": "table", "limit": 50},
        {
            "id": "per-flow",
            "dataset": "palm-system-instances-per-flow",
            "profile": "series",
            "series": {"x_field": "flow_name", "y_fields": ["count"]},
        },
    ],
})
# → /analytics/?dashboard=my-ops
```

Origin-bound board (datasets must already be registered as **resources**):

```python
register_origin_system_resources(repo, "http://b:8090")
host.design.publish_dashboard({
    "name": "origin-ops",
    "tiles": [
        {"id": "f", "dataset": "origin-system-flows", "profile": "table"},
    ],
})
```

REST:

```http
POST /v1/api/design/dashboards/publish
X-Palm-Subject: dev
{"name":"my-ops","tiles":[{"id":"t1","dataset":"palm-system-flows","profile":"table"}]}
```

Dispatch aliases: `design/propose-dashboard`, `design/publish-dashboard`.
