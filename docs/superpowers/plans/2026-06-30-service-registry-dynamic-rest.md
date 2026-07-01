# 0.16 Services-Are-the-API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace monolithic REST/MCP with three domain services in `palm/services/`, per-domain runtime handlers, and intentional API break. Delete legacy handler tree.

**Architecture:** Extract Definition, Execution (flows/providers/processes), System from `palm/common/services/`. Each module has `registry.py` + `service.py`. REST under `rest/{definitions,execution,system}/`; MCP mirrors same split. Experimental — no shims for `/v1/wizards` or old MCP tool names.

**Design spec:** [docs/superpowers/specs/2026-06-30-service-registry-dynamic-rest-design.md](../specs/2026-06-30-service-registry-dynamic-rest-design.md)

**Prerequisite:** 0.15.4 shipped.

---

## Phase 0.16a — Scaffold `palm/services/`

### Task 1: Package skeleton + ServiceApp bootstrap

**Files:**
- Create: `src/palm/services/__init__.py`
- Create: `src/palm/services/_apps.py`
- Create: `src/palm/services/definitions/__init__.py`, `registry.py`, `service.py` (stubs)
- Create: `src/palm/services/execution/__init__.py`, `service.py`
- Create: `src/palm/services/execution/flows/__init__.py`, `registry.py`, `service.py`, `session.py`
- Create: `src/palm/services/execution/providers/__init__.py`, `registry.py`, `service.py`
- Create: `src/palm/services/execution/processes/__init__.py`, `registry.py`, `service.py`
- Create: `src/palm/services/system/__init__.py`, `registry.py`, `service.py`
- Modify: `src/palm/common/services/__init__.py` — export only `BaseService` + errors (no domain services, no views)

- [ ] **Step 1:** Move `DefinitionService` body from `common/services/definition.py` → `services/definitions/service.py` (re-export temporarily from common for one commit if needed)
- [ ] **Step 2:** Move `InternalService` → `services/system/service.py` (rename class to `SystemService`)
- [ ] **Step 3:** Split `ExecutionService` + `InstanceSession` + `ReplSession` → `execution/service.py` + `execution/flows/`
- [ ] **Step 4:** Wire `ApplicationHost` / `ServerContext`: `.definitions`, `.execution`, `.system` (remove `.internal`)
- [ ] **Step 5:** Tests — `tests/test_services_*.py` updated imports
- [ ] **Step 6:** Commit: `feat(services): scaffold palm.services domain modules`

### Task 1b: Eliminate `common/services/views.py`

Catalog API shapes belong to the **definitions service domain**, not a shared `common` dict-builder module. Agent/operator hints do not belong in catalog payloads.

**Files:**
- Create: `src/palm/services/definitions/flows.py`, `processes.py`, `resources.py`
- Modify: `src/palm/definitions/flow.py`, `process.py` — add `catalog_summary()` (facts only)
- Modify: `src/palm/patterns/wizard/bindings/` — move `flow_step_slugs` here (from views)
- Modify: `src/palm/services/definitions/service.py` — use domain helpers, not `views.*`
- Modify: `src/palm/runtimes/server/surfaces/ssr/studio/api/definitions.py`
- Modify: `src/palm/runtimes/mcp/` — process MCP hints from `process.metadata` in resources/prompts, not catalog JSON
- Delete: `src/palm/common/services/views.py`
- Modify: `src/palm/common/services/__init__.py` — remove views exports
- Modify: `tests/test_process_summary.py` → `tests/test_definitions_catalog.py` (or equivalent)

**Ownership rule:**

| Shape | Owner |
|-------|-------|
| Persistence | `palm/definitions/*.to_dict()` |
| Catalog list row | `FlowDefinition.catalog_summary()` / `ProcessDefinition.catalog_summary()` or `services/definitions/*.py` |
| Pattern enrichment (e.g. wizard `step_slugs`) | Pattern `bindings/` |
| Agent submit hints | MCP resources / prompts / `docs/llms.txt` |
| HTTP wire encoding | Runtime handlers (last mile) |

- [ ] **Step 1:** Add `catalog_summary()` on `FlowDefinition` and `ProcessDefinition` — id, name, pattern, flow_count, entry_flow only; **no** `submit_hint` / `avoid`
- [ ] **Step 2:** Create `services/definitions/flows.py`, `processes.py`, `resources.py`; wire `DefinitionService.list_*` / `get_*` through them
- [ ] **Step 3:** Replace `flow_detail` / `process_detail` with `to_dict()` at service layer; replace `resource_summary` with `ResourceCatalog.describe()` (already structured)
- [ ] **Step 4:** Move `flow_step_slugs` → `palm/patterns/wizard/bindings/`; fix `validate_flow` import
- [ ] **Step 5:** Remove MCP operator hints from process catalog responses; expose via MCP definition resources reading `process.metadata.mcp`
- [ ] **Step 6:** Update Studio SSR to call `host.definitions` or `services/definitions` helpers — no `common.services.views` imports
- [ ] **Step 7:** Delete `views.py`; grep guard `palm.common.services.views` → zero hits in `src/` and `tests/`
- [ ] **Step 8:** Commit: `refactor(definitions): drop common services views; domain-owned catalog shapes`

**Deferred (post-0.16.0, optional 0.17):** `ListFlowCatalogQuery` / `ListProcessCatalogQuery` read projections with `DictStateSchema` output types — replaces remaining ad-hoc dict assembly and feeds OpenAPI generation.

---

## Phase 0.16b — Registries + REST prefix

### Task 2: Domain registries (manual)

**Files:**
- `src/palm/services/definitions/registry.py` — CRUD route entries for flows/processes/resources
- `src/palm/services/execution/flows/registry.py` — flow slug + instance verbs
- `src/palm/services/execution/providers/registry.py` — provider list + invoke (different shape)
- `src/palm/services/system/registry.py` — doctor, waiting, sessions

- [ ] **Step 1:** Define registry datatypes (route id, method, path template, handler fn name)
- [ ] **Step 2:** Register flows entries: list, create, get instance, input, backtrack
- [ ] **Step 3:** Register providers entries: list, get, invoke — **no** instance input verbs
- [ ] **Step 4:** Unit tests `tests/test_service_registries.py`
- [ ] **Step 5:** Commit: `feat(services): manual domain registries`

### Task 3: REST scaffold per domain

**Files:**
- Create: `src/palm/runtimes/server/surfaces/rest/prefix.py`
- Create: `src/palm/runtimes/server/surfaces/rest/definitions/{routes,handlers}.py`
- Create: `src/palm/runtimes/server/surfaces/rest/execution/flows/{routes,handlers}.py`
- Create: `src/palm/runtimes/server/surfaces/rest/execution/providers/{routes,handlers}.py`
- Create: `src/palm/runtimes/server/surfaces/rest/system/{routes,handlers}.py`
- Modify: `src/palm/runtimes/server/surfaces/rest/surface.py`

- [ ] **Step 1:** `API_PREFIX = "/v1/api"`; mount definitions + system read paths first
- [ ] **Step 2:** Flows handlers call `ctx.execution.flows.*` (thin)
- [ ] **Step 3:** Integration test one path: `POST /v1/api/flows/{flow}/create` → instance
- [ ] **Step 4:** Commit: `feat(rest): per-domain handlers under /v1/api`

---

## Phase 0.16c — MCP per domain

### Task 4: Break and rebuild MCP tools

**Files:**
- Create: `src/palm/runtimes/mcp/definitions/`, `execution/flows.py`, `execution/providers.py`, `system/`
- Modify: `src/palm/runtimes/mcp/in_process.py`, `server.py`, `contributors.py`
- Modify: `docs/MCP.md`, `docs/llms.txt`, bundled `mcp/data/llms.txt`

- [ ] **Step 1:** Map old tools → new service methods (document in `MIGRATION-0.16.md`)
- [ ] **Step 2:** Register execution/flows tools (inspect, input, drive, resume_child_wait)
- [ ] **Step 3:** Register system tools (doctor, list_waiting, session tree)
- [ ] **Step 4:** Update `test_mcp_in_process.py`, `test_mcp_tools.py`
- [ ] **Step 5:** Commit: `feat(mcp): service-domain tools (breaking)`

---

## Phase 0.16d — Definition CRUD + providers invoke

### Task 5: Definition writes on new surface

- [ ] Implement POST/PUT/DELETE on `/v1/api/definitions/flows/…` via new CQRS commands (pattern-registered schemas)
- [ ] Studio SSR routes point at `palm.services.definitions` (catalog shapes from Task 1b helpers, not `views.py`)

### Task 6: Providers execution domain

- [ ] `execution/providers/service.py` — invoke path only
- [ ] REST + MCP invoke wired; tests `tests/test_rest_resources_invoke.py` adapted

---

## Phase 0.16e — Delete legacy surface

### Task 7: Remove old REST/MCP/common services

**Delete:**
- `src/palm/runtimes/server/surfaces/rest/handlers/wizard.py`
- `src/palm/runtimes/server/surfaces/rest/handlers/jobs.py`
- `src/palm/runtimes/server/surfaces/rest/handlers/catalog.py`
- `src/palm/runtimes/server/surfaces/rest/handlers/instances.py`
- `src/palm/runtimes/server/surfaces/rest/route_table.py`, `routes.py` (monolith)
- `src/palm/common/services/internal.py`, `definition.py`, `execution.py`, `session.py`, `views.py`
- `src/palm/runtimes/mcp/tools.py` (monolith — after split complete)

- [ ] **Step 1:** Grep guard — no imports of deleted modules
- [ ] **Step 2:** Update Explorer fetch paths to `/v1/api/…`
- [ ] **Step 3:** `MIGRATION-0.16.md` — old URL/tool → new mapping
- [ ] **Step 4:** Commit: `refactor(0.16): remove legacy REST handlers and monolithic MCP`

---

## Phase 0.16f — Docs + release

- [ ] `docs/VISION-0.16.md`, ADR 005 draft
- [ ] Update `ARCHITECTURE.md`, `AGENTS.md` extension table (`palm/services/`)
- [ ] `CHANGELOG [0.16.0]`, `RELEASE-0.16.0.md`
- [ ] `just guard-common`, focused pytest suite green

---

## Final verification

```bash
rg 'handlers/wizard|InternalService|/v1/wizards' src tests
rg 'palm\.common\.services\.(internal|execution|definition|views)' src tests
rg 'common/services/views' src tests
uv run pytest tests/test_service_registries.py tests/test_definitions_catalog.py \
  tests/test_mcp_in_process.py tests/test_server_wizards.py -v   # adapted to new paths
just guard-common
```

---

## Plan self-review

| Spec section | Task |
|--------------|------|
| `palm/services/` extraction | 1 |
| Drop `common/services/views` | 1b |
| `common/services` = base + errors only | 1, 1b, 7 |
| Flows ≠ providers | 2, 6 |
| Per-domain REST | 3, 7 |
| Per-domain MCP | 4 |
| Definition CRUD | 5 |
| Delete legacy | 7 |
| Breaking policy | 7, MIGRATION-0.16.md |