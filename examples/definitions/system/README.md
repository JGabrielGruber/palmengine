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

Dashboard: **`palm-system`**

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
