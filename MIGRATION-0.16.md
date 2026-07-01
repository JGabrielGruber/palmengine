# Migration Guide — Palm 0.16

**Status:** Draft (pre-release)  
**Audience:** REST integrators, MCP agent configs, Explorer maintainers  
**Policy:** Experimental Palm — **no deprecation window**. Old URLs and MCP tool names are removed in 0.16.

0.16 replaces transport-shaped REST (`/v1/wizards`, `/v1/jobs`, monolithic handlers) with **service-domain APIs** under `/v1/api/…`. MCP tools are regrouped to mirror the same three services.

**Vision:** [docs/VISION-0.16.md](docs/VISION-0.16.md)  
**Design:** [docs/superpowers/specs/2026-06-30-service-registry-dynamic-rest-design.md](docs/superpowers/specs/2026-06-30-service-registry-dynamic-rest-design.md)

---

## Mental model shift

| 0.15.4 | 0.16 |
|--------|------|
| REST routes named after resources (`wizards`, `jobs`, `instances`) | REST routes named after **services** (`definitions`, `flows`, `providers`, `system`) |
| `host.internal` | `host.system` (`SystemService`) |
| `host.execution.on(id)` (single class) | `host.execution.flows.on(id)` vs `host.execution.providers.invoke(…)` |
| MCP `palm_wizard_*` cluster | MCP `palm_flows_*` under execution/flows |
| Services in `palm.common.services` | Domain modules in `palm.services` |

**Semantics preserved:** instance-first handles (`instance_id`), plain-string wizard input, compact inspect, in-process MCP (`PALM_MCP_IN_PROCESS=1`). **Names and paths change.**

---

## REST URL mapping

Base prefix: **`/v1/api`**

### Definitions (catalog — what exists?)

| 0.15.4 | 0.16 |
|--------|------|
| `GET /v1/flows` | `GET /v1/api/definitions/flows` |
| `GET /v1/flows/{flow_id}` | `GET /v1/api/definitions/flows/{flow_id}` |
| `POST /v1/flows` (if present) | `POST /v1/api/definitions/flows` |
| `PUT /v1/flows/{flow_id}` | `PUT /v1/api/definitions/flows/{flow_id}` |
| `DELETE /v1/flows/{flow_id}` | `DELETE /v1/api/definitions/flows/{flow_id}` |
| `GET /v1/processes` | `GET /v1/api/definitions/processes` |
| `GET /v1/processes/{process_id}` | `GET /v1/api/definitions/processes/{process_id}` |
| `GET /v1/resources` | `GET /v1/api/definitions/resources` |
| `GET /v1/resources/{resource_ref}` | `GET /v1/api/definitions/resources/{resource_ref}` |
| `POST /v1/flows/validate` | `POST /v1/api/definitions/flows/validate` |

Catalog CRUD writes (deferred in 0.15) land here in 0.16 — not on legacy catalog handlers.

### Execution — flows (interactive instances)

| 0.15.4 | 0.16 |
|--------|------|
| `GET /v1/wizards` | `GET /v1/api/flows` |
| `POST /v1/wizards` | `POST /v1/api/flows/{flow_id}/create` |
| `GET /v1/wizards/{instance_id}` | `GET /v1/api/flows/{flow_id}/session/{session_id}` |
| `POST /v1/wizards/{instance_id}/input` | `POST /v1/api/flows/{flow_id}/session/{session_id}/input` |
| `POST /v1/wizards/{instance_id}/backtrack` | `POST /v1/api/flows/{flow_id}/session/{session_id}/backtrack` |
| `POST /v1/wizards/{instance_id}/resume-child-wait` | `POST /v1/api/flows/{flow_id}/session/{session_id}/resume-child-wait` |
| `POST /v1/wizards/{instance_id}/resume-wizard-tick` | `POST /v1/api/flows/{flow_id}/session/{session_id}/resume` |

Job-oriented paths (non-wizard REPL) move under flows or processes depending on pattern; wizard paths use **flow-centric** URLs above.

| 0.15.4 | 0.16 |
|--------|------|
| `GET /v1/jobs` | `GET /v1/api/flows/instances` (filter) or process-scoped list |
| `GET /v1/jobs/{job_id}` | `GET /v1/api/flows/instances/{instance_id}` |
| `POST /v1/jobs/{job_id}/input` | `POST /v1/api/flows/instances/{instance_id}/input` |
| `POST /v1/jobs/{job_id}/cancel` | `POST /v1/api/flows/instances/{instance_id}/cancel` |
| `GET /v1/jobs/{job_id}/context` | `GET /v1/api/flows/instances/{instance_id}/context` |

### Execution — providers (invoke — distinct from flows)

| 0.15.4 | 0.16 |
|--------|------|
| `POST /v1/resources/invoke` | `POST /v1/api/providers/{provider}/{resource}/invoke` |

Providers have **no** instance `input` / `backtrack` verbs. One-shot invoke only.

### Execution — processes

| 0.15.4 | 0.16 |
|--------|------|
| `POST /v1/plans/prepare` | `POST /v1/api/processes/{process_id}/prepare` |
| `POST /v1/plans/submit` | `POST /v1/api/processes/{process_id}/submit` |

### System (debug & audit — was internal ops)

| 0.15.4 | 0.16 |
|--------|------|
| `GET /v1/doctor` | `GET /v1/api/system/doctor` |
| `GET /v1/instances` (operator list) | `GET /v1/api/system/sessions` |
| `GET /v1/instances/{instance_id}` | `GET /v1/api/system/sessions/{session_id}` |
| `GET /v1/instances/{instance_id}/tree` | `GET /v1/api/system/sessions/{session_id}/tree` |
| `GET /v1/instances/{instance_id}/snapshots` | `GET /v1/api/system/sessions/{session_id}/history` |

### Removed without direct replacement in 0.16

| 0.15.4 | Notes |
|--------|-------|
| `GET /v1/instances/{id}/resume` | Use flows instance verbs or CLI resume |
| Snapshot diff REST | `palm_diff_snapshots` → system/debug tooling in MCP |
| Monolithic `/v1/openapi.json` shape | Regenerated from per-domain route registries (structure changes) |

Explorer SSR (`/explorer`) will be updated to fetch `/v1/api/…` — not a public integrator contract.

---

## MCP tool mapping

Tools are grouped by service domain. Exact names ship with 0.16; plan below.

### Execution — flows

| 0.15.4 | 0.16 |
|--------|------|
| `palm_submit_wizard` | `palm_flows_create_session` |
| `palm_submit_flow` | `palm_flows_create_session` |
| `palm_inspect_instance` | `palm_flows_session` |
| `palm_wizard_input` | `palm_flows_session_input` |
| `palm_wizard_drive` | `palm_flows_session_drive` |
| `palm_wizard_backtrack` | `palm_flows_session_backtrack` |
| `palm_resume_child_wait` | `palm_flows_session_resume_child_wait` |
| `palm_resume_wizard_tick` | `palm_flows_session_resume` |
| `palm_wizard_collection_action` | `palm_wizard_collection_action` (pattern tool, unchanged) |
| `palm_wizard_commit_preview` | `palm_wizard_commit_preview` (pattern tool, unchanged) |
| `palm_compose_status` | `palm_flows_compose_status` |
| `palm_inspect_job` | `palm_system_inspect_job` (job_id) or `palm_flows_session` (session_id) |
| `palm_provide_job_input` | `palm_flows_session_input` or `palm_system_job_input` |

### Execution — providers

| 0.15.4 | 0.16 |
|--------|------|
| `palm_invoke_resource` | `palm_providers_invoke` |

### Definitions

| 0.15.4 | 0.16 |
|--------|------|
| MCP resources (`palm://definitions/…`) | Unchanged URIs; add `palm_definitions_*` tools |
| `palm_validate_flow` | `palm_definitions_validate_flow` |
| `palm_explain_step` | `palm_definitions_explain_step` |

### System

| 0.15.4 | 0.16 |
|--------|------|
| `palm_doctor` | `palm_system_doctor` |
| `palm_list_waiting` | `palm_system_list_waiting` |
| `palm_cancel_job` | `palm_system_cancel_job` |
| `palm_fetch_job` | `palm_system_fetch_job` |
| `palm_trace_events` | `palm_system_trace_events` |
| `palm_diff_snapshots` | `palm_system_diff_snapshots` |

### Processes

| 0.15.4 | 0.16 |
|--------|------|
| `palm_submit_process` | `palm_processes_submit` |
| Pattern tools (`palm_parallel_branch_status`, …) | Remain pattern-contributed (unchanged names) |

Agent prompts updated in `docs/MCP.md` and `docs/llms.txt` (shipped 0.16.5).

---

## Python API mapping

```python
# 0.15.4
host.internal.doctor()
host.definitions.list_flows()
host.execution.on(instance_id).input("yes")

# 0.16
host.system.doctor()
host.definitions.list_flows()          # same surface, new module path
host.execution.flows.on(instance_id).input("yes")
host.execution.providers.invoke(provider, resource, params)
```

Import paths:

| 0.15.4 | 0.16 |
|--------|------|
| `palm.common.services.InternalService` | `palm.services.system.SystemService` |
| `palm.common.services.DefinitionService` | `palm.services.definitions.DefinitionService` |
| `palm.common.services.ExecutionService` | `palm.services.execution.ExecutionService` |
| `palm.common.services.InstanceSession` | `palm.services.execution.flows.InstanceSession` |
| `palm.common.services.ReplSession` | `palm.services.execution.flows.ReplSession` |

`palm.common.services` retains `BaseService`, `errors`, `views` only.

---

## Integrator checklist

1. Replace all `/v1/wizards`, `/v1/jobs`, `/v1/instances` calls with `/v1/api/…` per tables above.
2. Split **catalog** reads (`definitions`) from **instance REPL** (`flows`) from **invoke** (`providers`).
3. Rename MCP tools in agent configs; re-read `docs/MCP.md` and `palm://agent/guide`.
4. Remove `host.internal` / `ctx.internal` — use `host.system`.
5. Pin `palmengine<0.16` if you need the old API during migration work.

---

## Explicitly deferred (post-0.16)

These were on the old incremental 0.16 roadmap; they return **on the new service-shaped API**, not as patches to legacy handlers:

- WebSocket live streaming → binds to `execution/flows` (0.17+)
- Full OpenAPI-only generation milestone → folded into per-domain registries
- Standalone catalog-write patches on old `DefinitionService` location → `definitions` service CRUD

---

## References

- [docs/VISION-0.16.md](docs/VISION-0.16.md)
- [docs/adr/005-service-domain-api.md](docs/adr/005-service-domain-api.md)
- [RELEASE-0.16.0.md](RELEASE-0.16.0.md) (at release)