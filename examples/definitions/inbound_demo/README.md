# Inbound demo — webhook → inbox → WorkIntent

Definition pack for [VISION-0.43](../../../docs/VISION-0.43.md) / [0.44](../../../docs/VISION-0.44.md):
resources that **listen** via `metadata.inbound` (no separate definition kind).

## Resources

| Name | Mode | Role |
|------|------|------|
| `inbound-inbox` | — | kv inbox (`store_resource` target) |
| `inbound-webhook-demo` | `webhook` | `POST /v1/api/inbound/inbound-webhook-demo` |
| `origin-events-inbound` | `stream` | Only when `PALM_ORIGIN_URL` is set |

Reaction flow: **`on-inbound-webhook`** (wizard ack step).

## Quick test

```bash
palm host server
# work drain starts automatically on the server profile (0.44.1+)
```

```bash
curl -s -X POST http://127.0.0.1:8080/v1/api/inbound/inbound-webhook-demo \
  -H 'X-Palm-Subject: dev' \
  -H 'Content-Type: application/json' \
  -d '{"id":"demo-1","event":"test"}'
```

Expect **202** with `"stored": true` and `"store_resource": "inbound-inbox"`.
Within a second, `on-inbound-webhook` should appear in jobs (`WAITING_FOR_INPUT` on step `ack`).

Optional secret (open when unset):

```bash
export PALM_INBOUND_DEMO_SECRET=my-secret
# add: -H "X-Palm-Inbound-Secret: my-secret"
```

## Debug

```bash
# bindings + signal counts
curl -s http://127.0.0.1:8080/v1/api/inbound -H 'X-Palm-Subject: dev' | jq .

# control plane (work_pending, work_drain_running, inbound_bindings)
curl -s http://127.0.0.1:8080/v1/api/system/doctor -H 'X-Palm-Subject: dev' \
  | jq '.data.control_plane'

# persisted envelope
curl -s -X POST http://127.0.0.1:8080/v1/api/providers/kv/inbound-inbox/invoke \
  -H 'X-Palm-Subject: dev' -H 'Content-Type: application/json' \
  -d '{"action":"get"}' | jq '.data.value.payload'
```

If the webhook returns 202 but no job starts, see [docs/WORK-DRAIN.md](../../../docs/WORK-DRAIN.md).

## Stream binding (optional)

```bash
export PALM_ORIGIN_URL=http://127.0.0.1:8080   # another Palm with events
palm host server
```

`origin-events-inbound` subscribes to `resource.changed` / `job.completed` on the origin.