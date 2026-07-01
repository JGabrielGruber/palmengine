# Release checklist — 0.17.0

**Theme:** System REST parity — `/v1/api/system/…` owns observe/lifecycle; legacy monolith job/instance routes removed.

## Pre-ship

- [x] System REST routes: jobs context/cancel, instances, tree, snapshots, resume
- [x] MCP `PalmRestClient` aligned to system paths
- [x] `job_context.next_actions` → flows session + system paths
- [x] Legacy `/v1/jobs`, `/v1/instances`, `/v1/snapshots` removed from `route_table.py`
- [x] `MIGRATION-0.17.md` section 0.17.0
- [x] Tests updated and passing
- [x] Version **0.17.0** · `just docs-check` · `just guard-common`

## Still transitional

- `/v1/plans/*` — **0.17.1**
- `providers/palm/flow/remote/` legacy URLs — **0.17.2**
- OpenAPI from service registries — **0.17.3**

## Verify

```bash
uv run pytest tests/test_system_service_routes.py tests/test_rest_system_routes.py \
  tests/test_server_runtime.py tests/test_mcp_tools.py -v
just docs-check && just guard-common
rg '/v1/jobs|/v1/instances' src/palm --glob '!**/providers/palm/**'
```

## Tag

```bash
git commit -m "feat(0.17.0): system REST parity — remove legacy job/instance routes"
git tag -a v0.17.0 -m "Palm Engine 0.17.0 — System REST parity"
```