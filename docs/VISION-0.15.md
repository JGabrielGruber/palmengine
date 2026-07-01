# Vision 0.15 — CQRS Schemas + Service Layer

**Theme:** Unify Palm's user-facing API behind schema-described CQRS and instance-centric services — runtimes become thin adapters.

**Status:** Shipped as **0.15.4** (June 2026)

---

## Problem

Through 0.14, Palm had mature CQRS and multiple runtime surfaces (REST, MCP, CLI, Explorer). Each surface maintained parallel contracts:

- REST hand-maintained `DictStateSchema` bodies in `rest/schemas.py`
- MCP HTTP proxy via `PalmRestClient` (loopback round-trips)
- CLI mixed direct-runtime and bus paths

There was no user-facing business API — surfaces talked to CQRS handlers or REST routes directly. Validation and inspect shapes duplicated across layers.

---

## Goals

| Goal | Outcome |
|------|---------|
| CQRS schemas | `CqrsSchemaRegistry` + contributor `command_schemas` / `query_schemas` |
| Service layer | `BaseService` composes CQRS (many-to-one, not 1:1 routes) |
| Instance-centric execution | `host.execution.on(instance_id)` + `InstanceSession` |
| Thin runtimes | REST/MCP delegate inspect, catalog, and wizard writes to services |
| In-process MCP | `PALM_MCP_IN_PROCESS=1` — tools call services without HTTP |
| Extension | Patterns register CQRS + schemas via `CqrsContributor` |

---

## What shipped

### CQRS schemas (0.15a)

- `CqrsSchemaRegistry`, `ValidationResult`, `build_schema_registry()`
- `CqrsContributor` extended with schema maps + `instance_status_query`
- Core + wizard schema bootstrap; `tests/test_cqrs_schemas.py`

### Service layer (0.15b–e)

| Service | Role |
|---------|------|
| `InternalService` | `doctor`, `list_jobs`, `inspect_job`, `inspect_instance`, `list_instances`, `list_snapshots`, `cancel_job` |
| `DefinitionService` | `list_flows`, `get_flow`, `validate_flow`, `list_processes`, `get_process`, `list_resources`, `get_resource` |
| `ExecutionService` | `on(instance_id)`, `run_wizard`, `run_flow` |
| `InstanceSession` | `status`, `input`, `backtrack`, `resume`, `resume_child_wait`, `cancel` |
| `ReplSession` | CLI REPL active-instance handle (`ctx.repl`) |

Wired on `ApplicationHost` and `ServerContext` as `.internal`, `.definition`, `.execution`, `.schemas`.

### Runtime adapters (0.15c–e)

- REST inspect/catalog/wizard write routes → services
- MCP `PalmInProcessBackend` — duck-types `PalmRestClient` via `ServerContext`
- Server HTTP `/mcp` reuses hosting `ServerContext` (no loopback REST)
- CLI REPL holds `ReplSession` synced with `active_instance_id`

### Quality

- Boundary tests preserved (`palm.common` has no wizard imports)
- Targeted service, MCP, and wizard REST tests green

---

## Non-goals (deferred)

- Pydantic migration for CQRS types
- `ServiceContributor` registry for pattern-owned business methods
- Definition catalog write paths (save/update/delete) — read + validate only
- WebSocket live streaming
- Breaking REST URL changes

---

## Success criteria (met)

1. `host.execution.on(id).input("yes")` drives wizards without surface-specific CQRS imports in `palm.common`.
2. MCP with `PALM_MCP_IN_PROCESS=1` runs operator tools without a REST server.
3. REST `/v1/wizards/{id}/input` delegates to `ctx.execution.on(id).input(...)`.
4. `just check` and service/MCP/wizard tests pass.

---

## Architecture snapshot

```
REST / MCP / CLI  →  palm.common.services  →  CQRS buses  →  patterns/providers
```

**Primary metaphor:** instance handle (`execution.on(instance_id)`).  
**REPL metaphor:** `ReplSession` tracks active instance in CLI.  
**Remote MCP:** `PALM_MCP_IN_PROCESS=0` + `PALM_BASE_URL` preserves 0.14 HTTP proxy mode.

---

## References

- Design spec: [docs/superpowers/specs/2026-06-30-cqrs-schemas-service-layer-design.md](superpowers/specs/2026-06-30-cqrs-schemas-service-layer-design.md)
- 0.15.3 cleanup spec: [docs/superpowers/specs/2026-06-30-0.15.3-legacy-cleanup-design.md](superpowers/specs/2026-06-30-0.15.3-legacy-cleanup-design.md)
- ADR: [docs/adr/004-cqrs-schemas-service-layer.md](adr/004-cqrs-schemas-service-layer.md)
- Implementation plan: [docs/superpowers/plans/2026-06-30-cqrs-schemas-service-layer.md](superpowers/plans/2026-06-30-cqrs-schemas-service-layer.md)
- 0.15.3 plan: [docs/superpowers/plans/2026-06-30-0.15.3-legacy-cleanup.md](superpowers/plans/2026-06-30-0.15.3-legacy-cleanup.md)

---

## Next — cleanup track

Master spec: [docs/superpowers/specs/2026-06-30-0.15-cleanup-track-design.md](superpowers/specs/2026-06-30-0.15-cleanup-track-design.md)

### 0.15.0 — release hygiene
- Ruff fix (59 issues) + version bump + CHANGELOG + `RELEASE-0.15.0.md`

### 0.15.2 — dedupe (public APIs stable)
- REST input validation → `CqrsSchemaRegistry` via `rest/schema_bridge.py`
- Serializer imports → `services.views`; MCP dual-backend test clarity

### 0.15.3 — legacy removal (no migration window)
- Delete `create_cli_app`, `interactive_runtime` wizard aliases, `ChildWizardCompletionHook`, remaining shims
- Spec: [docs/superpowers/specs/2026-06-30-0.15.3-legacy-cleanup-design.md](superpowers/specs/2026-06-30-0.15.3-legacy-cleanup-design.md)

### 0.16 — Services Are the API (supersedes incremental bullets below)

**Authoritative direction:** [docs/VISION-0.16.md](VISION-0.16.md)

- Extract services to `palm/services/` (definitions, execution, system) with per-domain registries
- Delete legacy REST handlers; break REST (`/v1/api/…`) and MCP (per-service tools) intentionally
- Runtimes mirror services — handlers per domain, not per resource file
- `execution/flows` vs `execution/providers` — distinct behavior
- Migration: [MIGRATION-0.16.md](../MIGRATION-0.16.md)

**Deferred and redone on new API (not separate 0.16 milestones):**

- Definition catalog writes → `definitions` service CRUD
- OpenAPI generation → per-domain route registries
- WebSocket streaming → post-0.16, binds to `execution/flows`