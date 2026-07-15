# Ops dogfood — server, invoke, storage

**Status:** 0.45.8  
**See also:** [WORK-DRAIN.md](WORK-DRAIN.md) · [EVENT-PLANE.md](EVENT-PLANE.md) · [system pack README](../examples/definitions/system/README.md)

## Resource invoke (REST)

| Route | When to use |
|-------|-------------|
| `POST /v1/api/providers/{provider}/{resource_ref}/invoke` | Explicit provider (catalog, docs) |
| `POST /v1/api/resources/{resource_ref}/invoke` | **Shortcut** — provider resolved from definition (0.45.8) |

Body: `{"action":"get","params":{...}}` · Header: `X-Palm-Subject: dev`

Example (event tail):

```bash
curl -s http://127.0.0.1:8080/v1/api/resources/palm-system-event-log/invoke \
  -H 'Content-Type: application/json' -H 'X-Palm-Subject: dev' \
  -d '{"action":"get"}'
```

There is **no** `/v1/api/resources/...` route without `/invoke`.

## Doctor / control_plane

`GET /v1/api/system/doctor` → `control_plane`:

| Key | Meaning |
|-----|---------|
| `work_drain_running` | Background drain thread active |
| `work_drain_background` | Same (deprecated alias, 0.45.8) |
| `ops.invoke_route` / `ops.invoke_route_short` | Invoke path templates |
| `ops.storage_durable` | Host storage survives restart |
| `ops.event_log_durable` | `palm-system-event-log` kv backend ≠ memory |
| `ops.server_profile_hint` | Shown when `palm host server` uses memory storage |

## Durable ops tail (server profile)

Default `palm host server` uses `PALM_STORAGE_BACKEND=memory` in dev — **event watch tail is amnesiac** (`backend: auto` on kv → memory).

For production-like dogfood:

```bash
export PALM_STORAGE_BACKEND=filesystem
export PALM_DATA_DIR=./.palm-data
palm host server
```

Or set `params.backend: storage` on kv resources when host storage is durable.

## Tests and cwd examples

`PalmSettings.load_example_definitions=false` (and `for_tests(load_examples=False)`) **does not** scan `./examples/definitions` from cwd — only `data_dir/definitions` and explicitly registered defs. Packaged examples load only when `load_example_definitions=true`.