# VISION 0.43 — Inbound Resources

**Status:** Implementation (0.43.x)  
**Decision:** Inbound is **not** a separate definition kind. **Resources can listen.**

## Mental model

> A resource is a named external capability. Some are pull (invoke). Some are **inbound** (listen). Many will be both.

```text
signal (webhook | stream | poll)
  → metadata.inbound on ResourceDefinition
  → WorkIntent enqueue
  → run when able (host.tick_work / drain)
```

## Contract

`ResourceDefinition.metadata.inbound` (see `palm.common.resource.inbound.parse_inbound_spec`):

| Field | Role |
|-------|------|
| `enabled` | Bind listener |
| `mode` | `webhook` \| `stream` \| `poll` |
| `path` | Webhook path slug (default: resource name) |
| `work.flow_id` | WorkIntent target |
| `secret_param` / `secret_header` | Optional shared secret from `params` |
| `event_types` | Stream filter |
| `coalesce_field` / `debounce_seconds` | Storm control |

## Surfaces

| | |
|--|--|
| `POST /v1/api/inbound/{name}` | Webhook → 202 + intent |
| `GET /v1/api/inbound` | List bindings |
| Doctor `control_plane.inbound_*` | Ops visibility |
| Event `inbound.received` | Journal/public catalog |

## Non-goals

- `InboundDefinition` type  
- Running flows on the HTTP/WS reader thread  
- Core WorkEngine  

See [VISION-0.40](VISION-0.40.md) for composition priority; 0.43 completes **external → Palm** using the same resource brand.
