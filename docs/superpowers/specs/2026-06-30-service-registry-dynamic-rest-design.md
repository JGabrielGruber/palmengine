# 0.16 Design: Services Are the API

**Status:** Approved (revised June 30, 2026)  
**Version target:** 0.16  
**Supersedes:** Incremental 0.16 items in STATUS/VISION (OpenAPI-from-registry-only, WebSocket-first, definition writes on old REST) — those are **redone inside this architecture**, not skipped as capabilities.

---

## Goal

0.15 proved the service layer behind thin runtimes. **0.16 makes services the product surface.**

- **Delete** the legacy REST handler tree (`/v1/wizards`, `/v1/jobs`, monolithic `handlers/*.py`) and the monolithic MCP tool map.
- **Break** REST and MCP URLs intentionally — experimental Palm, no migration window.
- **Expose** three domain services through runtimes that mirror service structure: handlers **per service domain**, not per CQRS route.
- **Extract** growing service code from `palm/common/services/` into `palm/services/` modules, each with its own registry.

The user-facing layer is **`palm/services/`**. Runtimes translate HTTP/MCP/CLI transport → service methods. CQRS stays internal to services.

---

## Principle

```
User / Agent / Explorer / CLI
        ↓
palm.runtimes.*          ← transport adapters (per service domain)
        ↓
palm.services.*          ← user-facing API (Definition, Execution, System)
        ↓
palm.common.cqrs + patterns/providers   ← dispatch mechanism
        ↓
palm.core.*              ← pure engines
```

**Services are the APIs.** Registries describe what each service domain exposes. REST/MCP mount from those registries — manual, explicit, not a generic metadata framework in 0.16.

---

## Policy

| Rule | 0.16 |
|------|------|
| Experimental breaking changes | Allowed — delete old REST/MCP, no deprecation shim |
| `/v1/wizards`, `/v1/jobs`, … | **Removed** — replaced by `/v1/api/…` |
| MCP tool names (`palm_wizard_input`, …) | **Replaced** — tools grouped by service domain |
| `palm/common/services/{internal,definition,execution}.py` | **Moved** → `palm/services/` |
| `palm/common/services/` | **Retained** — `base.py`, `errors.py` only; `views.py` **deleted** (Task 1b) |
| Core purity | Unchanged — `palm/core/` never imports Palm packages |

---

## Three services

```
palm/services/
  _apps.py                 # ServiceApp bootstrap (like patterns/_apps.py)
  definitions/             # What exists? — catalog CRUD
    registry.py
    service.py
    flows.py, processes.py, resources.py   # domain helpers
  execution/               # What do I run / invoke?
    service.py             # coordinates submodules
    flows/                 # interactive flow instances (distinct behavior)
      registry.py
      service.py
      session.py           # instance REPL (from common session concepts)
    providers/             # provider invoke (distinct behavior)
      registry.py
      service.py
    processes/             # process-scoped execution (REPL-like flows)
      registry.py
      service.py
  system/                  # What's happening? — debug, audit (was InternalService)
    registry.py
    service.py

palm/common/services/
  base.py, errors.py              # BaseService, validation errors only (no views.py)

# Catalog API shapes live in palm/services/definitions/{flows,processes,resources}.py
# and FlowDefinition.catalog_summary() / ProcessDefinition.catalog_summary()
```

| Service | User question | Primary consumers |
|---------|---------------|-------------------|
| **Definition** | What exists? | Studio, catalog MCP/REST, agents listing flows |
| **Execution** | What do I do? | REPL, wizards, provider invoke, process runs |
| **System** | What's going on? | Doctor, waiting jobs, session trees, audit |

---

## Execution: Flows ≠ Providers (distinct behavior)

**Do not unify** flows and providers under one execution registry shape.

### `execution/flows/` — interactive instances

- Pattern-backed flows (wizard primary): **create → instance → input → backtrack → resume**
- Registry encodes flow slug tree and instance verbs
- Session object per instance (evolves `InstanceSession` / `ReplSession`)
- Maps to today's wizard/job interactive paths, but API is **flow-centric REPL**, not `/v1/wizards/{id}/input`

Example mental path:

```
flows → approval → create → inst-5231412 → input
```

### `execution/providers/` — invoke surface

- **Catalog + invoke** — no instance REPL tree
- One-shot or parameterized invocation (`POST …/providers/rest/invoke`)
- Registry shape differs from flows (no `input`/`backtrack` verbs on instances)
- Maps to resource catalog + `invoke_resource` operational paths

### `execution/processes/`

- Process-scoped runs; REPL pattern similar to flows, own registry
- Coordinates multi-flow processes without overloading flow or provider registries

`ExecutionService` in `execution/service.py` **coordinates** submodules; each submodule owns its registry and service class.

---

## Definition Service — catalog CRUD

Shallow, CRUD-first. Separate URL namespace from execution.

```
GET/POST/PUT/DELETE  /v1/api/definitions/flows/{id}
GET/POST/…           /v1/api/definitions/processes/…
GET/POST/…           /v1/api/definitions/resources/…
```

`/v1/api/definitions/flows/approval` (catalog) ≠ `/v1/api/flows/approval/inst-x/input` (execution).

Definition writes deferred in 0.15 are **implemented here**, not as patches on old catalog handlers.

---

## System Service — debug & audit

Renamed from `InternalService`. Operator/debug only.

```
GET /v1/api/system/doctor
GET /v1/api/system/waiting
GET /v1/api/system/sessions
GET /v1/api/system/sessions/{session_id}
GET /v1/api/system/sessions/{session_id}/history
GET /v1/api/system/sessions/{session_id}/tree
```

`system/registry.py` — read-heavy; limited writes (e.g. cancel) where needed for operators.

---

## REST layout (per service domain — replaces old handlers)

**Delete:** `rest/handlers/wizard.py`, `jobs.py`, `catalog.py`, `instances.py`, `route_table.py` monolith, etc.

**Add:**

```
palm/runtimes/server/surfaces/rest/
  prefix.py                    API_PREFIX = "/v1/api"
  shared/                      errors, auth, schema_validation (transport only)

  definitions/
    routes.py                  mounts definitions.registry
    handlers.py                thin → palm.services.definitions

  execution/
    flows/
      routes.py, handlers.py   → palm.services.execution.flows
    providers/
      routes.py, handlers.py   → palm.services.execution.providers
    processes/
      routes.py, handlers.py   → palm.services.execution.processes

  system/
    routes.py, handlers.py     → palm.services.system

  surface.py                   register_definitions(), register_execution(), register_system()
```

Handlers are **domain-specific** (flows handlers ≠ provider handlers). They do not embed business logic — only HTTP mapping + auth.

OpenAPI is assembled from per-domain route registries (not the old `rest/schemas.py` monolith). Full registry-driven OpenAPI is in-scope as part of this layout, not a separate 0.16 bullet.

---

## MCP layout (break + mirror services)

**Delete:** monolithic `mcp/tools.py` operator map tied to old REST paths.

**Add:**

```
palm/runtimes/mcp/
  definitions/                 catalog tools/resources
  execution/
    flows.py                   drive instances (replaces palm_wizard_* cluster)
    providers.py               invoke tools
    processes.py
  system/                      doctor, waiting, sessions
  in_process.py                dispatches to new service modules on ServerContext
```

`PALM_MCP_IN_PROCESS=1` calls `palm.services.*` directly (same as today’s service path, new module paths). Remote mode proxies new `/v1/api/…` REST.

Update `docs/MCP.md`, `docs/llms.txt`, `.grok/config.toml` conventions — instance-first semantics preserved, **tool names and URLs change**.

---

## Host / ServerContext wiring

```python
host.definitions   # palm.services.definitions.service.DefinitionService
host.execution     # palm.services.execution.service.ExecutionService
host.system        # palm.services.system.service.SystemService
# host.internal → removed (alias deleted, no shim)
```

`ServerContext` exposes the same three properties. `CqrsSchemaRegistry` remains on `BaseService` in common.

CLI/REPL: `ReplSession` lives under `execution/flows/`; CLI imports from `palm.services.execution.flows`.

---

## What we are NOT doing in 0.16

| Deferred / out of scope | Notes |
|-------------------------|-------|
| Generic service metadata framework | Manual registries per domain only |
| Keeping old `/v1/wizards` routes | Breaking change |
| `PalmRestClient` compatibility shim | Experimental — update clients |
| Pydantic CQRS migration | Still out |
| WebSocket streaming | Redo after service-shaped REST exists (0.17+) |
| Incremental patches on old handlers | Delete tree instead |

---

## Migration (experimental)

- **No deprecation period** for REST/MCP/handler removal.
- **`MIGRATION-0.16.md`** — URL/tool mapping table (old → new), not a long sunset schedule.
- **ADR 005** — [docs/adr/005-service-domain-api.md](../../adr/005-service-domain-api.md)
- **MIGRATION-0.16.md** — integrator URL/tool mapping

---

## Success criteria

1. Zero imports from deleted `rest/handlers/{wizard,jobs,catalog,…}.py`
2. `palm/services/{definitions,execution,system}/` own registries + service classes
3. `execution/flows` and `execution/providers` have **different** registry contracts and handlers
4. MCP and REST both mount from service domain registries
5. `host.execution.flows.on(instance_id)` (or equivalent) is the primary interactive API
6. `just guard-common` — no pattern logic leaking into wrong layers; services may import patterns via CQRS only

---

## References

- [0.15 vision](../../VISION-0.15.md) — foundation this breaks forward from
- [ADR 004](../../adr/004-cqrs-schemas-service-layer.md) — superseded for **service package location** by this design; CQRS-in-services principle remains
- [Implementation plan](../plans/2026-06-30-service-registry-dynamic-rest.md)