# VISION 0.44 — Inbound polish (store, poll, stream)

**Status:** Implementation (0.44.x)
**Builds on:** [VISION-0.43](VISION-0.43.md)

## Deliverables

| Feature | Role |
|---------|------|
| `store_resource` / `store_action` | Persist inbound envelope via resource invoke **before** WorkIntent |
| `mode=poll` | Background worker — HTTP GET `url` or pull-invoke the listening resource |
| Stream transport | Prefer WebSocket (`PalmEventsWebSocketClient`); HTTP journal poll fallback |

## Contract additions

```yaml
metadata:
  inbound:
    store_resource: inbound-inbox   # kv put resource name
    store_action: put               # optional; default from store resource or put
    mode: poll
    debounce_seconds: 10            # poll interval when mode=poll (default 5s)
    url: https://example.com/hook   # poll GET target (optional)
```

WorkIntent payload gains `stored`, `store_resource`, `store_action`, or `store_error`.

**0.44.1:** `host server` enables background work drain by default — see [WORK-DRAIN.md](WORK-DRAIN.md) and [inbound_demo README](../examples/definitions/inbound_demo/README.md).

## Non-goals (0.44)

- Mesh authz / multi-worker fan-out (0.45+)
- Running flows on ingress thread
- `InboundDefinition` kind