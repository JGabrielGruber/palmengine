# Migration Guide — Palm 0.17

**Experimental policy:** Breaking changes ship without deprecation shims. Update integrators in place; do not expect legacy monolith routes to linger.

**Builds on:** [MIGRATION-0.16.md](MIGRATION-0.16.md)

---

## 0.17.0 — System REST parity

Legacy monolith observe/lifecycle routes are **removed**. Use the system service under `/v1/api/system/…`.

### Removed routes

| Legacy | Replacement |
|--------|-------------|
| `GET /v1/jobs` | `GET /v1/api/system/jobs` |
| `GET /v1/jobs/{job_id}` | `GET /v1/api/system/jobs/{job_id}` |
| `GET /v1/jobs/{job_id}/context` | `GET /v1/api/system/jobs/{job_id}/context` |
| `POST /v1/jobs/{job_id}/cancel` | `POST /v1/api/system/jobs/{job_id}/cancel` |
| `GET /v1/instances` | `GET /v1/api/system/instances` |
| `GET /v1/instances/{instance_id}` | `GET /v1/api/system/instances/{instance_id}` |
| `GET /v1/instances/{instance_id}/tree` | `GET /v1/api/system/instances/{instance_id}/tree` |
| `GET /v1/instances/{instance_id}/snapshots` | `GET /v1/api/system/instances/{instance_id}/snapshots` |
| `GET /v1/instances/{instance_id}/snapshots/{snapshot_id}` | `GET /v1/api/system/instances/{instance_id}/snapshots/{snapshot_id}` |
| `POST /v1/instances/{instance_id}/resume` | `POST /v1/api/system/instances/{instance_id}/resume` |

### Removed submit/input routes (use flows)

| Legacy | Replacement |
|--------|-------------|
| `POST /v1/jobs` | `POST /v1/api/flows/{flow_id}/create` |
| `POST /v1/jobs/{job_id}/input` | `POST /v1/api/flows/{flow_id}/session/{session_id}/input` |

`next_actions` in job context now point at flows session input and system paths.

### MCP REST proxy (`PALM_MCP_IN_PROCESS=0`)

`PalmRestClient` methods updated:

- `list_waiting_jobs` → `/v1/api/system/jobs?status=WAITING_FOR_INPUT`
- `get_job_context` → `/v1/api/system/jobs/{job_id}/context`
- `cancel_job` → `/v1/api/system/jobs/{job_id}/cancel`
- `get_instance_tree` → `/v1/api/system/instances/{instance_id}/tree`
- `list_snapshots` / `get_snapshot` → `/v1/api/system/instances/…`
- `provide_job_input` → resolves flow/session from job context, calls flows session input
- `submit_flow` → `/v1/api/flows/{flow_id}/create`

In-process MCP (`PALM_MCP_IN_PROCESS=1`) unchanged at the tool layer.

---

## 0.17.1 — Process execution service

Legacy plan staging routes are **removed**. Use the process execution service under `/v1/api/processes/…`.

### Removed routes

| Legacy | Replacement |
|--------|-------------|
| `POST /v1/plans/prepare` | `POST /v1/api/processes/{process_id}/prepare` |
| `POST /v1/plans/submit` | `POST /v1/api/processes/submit` |

### New convenience route

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/v1/api/processes/{process_id}/run` | Submit a process in one call (no plan staging) |

### MCP REST proxy

- `prepare_plans(body)` → `POST /v1/api/processes/{process_id}/prepare`
- `submit_plans(plan_ids)` → `POST /v1/api/processes/submit`

In-process MCP (`PALM_MCP_IN_PROCESS=1`) calls `host.execution.processes` directly.

### Service API

```python
host.execution.processes.prepare(process_id, body={...})
host.execution.processes.submit(plan_ids)
host.execution.processes.run(process_id, body={...})  # one-shot submit
host.execution.processes.dispatch(["processes", process_id, "run"], {"body": {...}})
```

---

## 0.17.2 — Palm provider remote alignment

The compositional **palm provider** remote client (`providers/palm/flow/remote/client.py`) now uses service-domain paths only.

### Client URL changes

| Function | Legacy | Replacement |
|----------|--------|-------------|
| `submit_flow_remote` | `POST /v1/jobs` | `POST /v1/api/flows/{flow_id}/create` |
| `get_job_remote` | `GET /v1/jobs/{job_id}` | `GET /v1/api/system/jobs/{job_id}` |
| `submit_process_remote` | `POST /v1/plans/prepare` + `/submit` | `POST /v1/api/processes/{process_id}/prepare` + `/submit` |

`invoke_resource_remote` already used `/v1/api/providers/…/invoke` (unchanged).

### Response normalization

`remote_job_payload` accepts `session_id` from flows create responses and maps it to `instance_id` for child-wait correlation.

---

## Later 0.17 phases (preview)

| Release | Theme |
|---------|-------|
| **0.17.1** | ✅ `POST /v1/api/processes/…` replaces `/v1/plans/*` |
| **0.17.2** | ✅ Palm provider remote client alignment |
| **0.17.3** | OpenAPI from per-service registries |

See [docs/superpowers/plans/2026-07-01-0.17-service-completion.md](docs/superpowers/plans/2026-07-01-0.17-service-completion.md).