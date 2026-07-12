# System pack — ops datasets & remote Palm

Definition-only pack: **`provider: palm`** system-read actions as published
analytics datasets + dashboard **`palm-system`**.

## Datasets

| Dataset | Action | Notes |
|---------|--------|--------|
| `palm-system-jobs` | `list_jobs` | |
| `palm-system-waiting` | `list_waiting` | |
| `palm-system-instances` | `list_instances` | |
| `palm-system-flows` | `list_flows` | |
| `palm-system-resources` | `list_resources` | |
| `palm-system-instances-per-flow` | virtual | `count_by` on `flow_name` |

## Local (same host)

```bash
just palm-server
# open http://127.0.0.1:8080/analytics/?dashboard=palm-system
```

```python
host.analytics.query("palm-system-flows", profile="table")
host.analytics.render_dashboard("palm-system")
```

## Remote Palm (0.40.5)

Same resource names; pass **`remote_url`** (and optional `remote_token`) on
query/invoke so the palm provider talks HTTP to the **origin** Palm.

```text
Palm A (analytics / dashboard)
    provider: palm · params.remote_url = https://b.example
        GET /v1/api/definitions/flows
        GET /v1/api/system/instances
        …
Palm B (origin)
```

```python
# A queries B's catalog
host.analytics.query(
    "palm-system-flows",
    profile="table",
    params={"remote_url": "http://127.0.0.1:8090"},
)

# Virtual views forward params to the source fact invoke
host.analytics.query(
    "palm-system-instances-per-flow",
    profile="series",
    params={"remote_url": "http://127.0.0.1:8090"},
)
```

REST (A):

```http
POST /v1/api/analytics/query
X-Palm-Subject: dev
{"dataset":"palm-system-flows","profile":"table","params":{"remote_url":"http://b:8080"}}
```

Optional auth on B:

```python
params={"remote_url": "...", "remote_token": "<bearer>"}
```

## Assist

Menu → **Analytics datasets** → chip `open:dataset:palm-system-flows`  
(preview is **local** unless query params carry `remote_url` — use REST/MCP with params for remote).

## Composition note

- **Critical for mesh:** same contracts local vs remote (`items` envelope).
- **Realtime WS** to the provider is **0.42** (P2); today remote is request/response.
