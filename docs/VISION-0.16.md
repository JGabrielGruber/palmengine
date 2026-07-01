# Vision 0.16 — Services Are the API

**Theme:** Break legacy REST/MCP. Extract domain services to `palm/services/`. Runtimes mount per service — handlers per domain, not per resource file.

**Status:** Approved (June 2026)  
**Builds on:** [0.15.4](VISION-0.15.md) — CQRS schemas, service layer proof, in-process MCP

---

## Problem

0.15 put business logic in services but left **transport-shaped** REST (`handlers/wizard.py`, `handlers/jobs.py`, …) and MCP tools mirroring those paths. Services lived in `palm/common/services/` as three flat classes — too small for domain growth.

Execution **flows** (instance REPL) and **providers** (invoke) share one `ExecutionService` but behave differently. Integrators read REST routes, not services.

---

## Goal

| Shift | From | To |
|-------|------|-----|
| User-facing layer | REST handlers + thin services | **`palm/services/` modules** with registries |
| REST | `/v1/wizards`, `/v1/jobs`, … | **`/v1/api/{definitions,flows,providers,system}/…`** |
| MCP | Monolithic tools on old REST | **Per-service tool packages** |
| Execution | One service class | **`execution/flows`**, **`execution/providers`**, **`execution/processes`** |
| Internal ops | `InternalService` | **`system`** service |

**Breaking release.** Experimental Palm — delete old handlers; `MIGRATION-0.16.md` for integrators.

---

## Architecture

```
CLI / Explorer / REST / MCP
        ↓
palm/runtimes/          thin mounts (per-service routes + MCP)
        ↓
palm/services/          USER API
  definitions/
  execution/
    flows/              instance REPL
    providers/          invoke (distinct)
    processes/
  system/
        ↓
palm/common/            CQRS, schemas, hooks, views
        ↓
palm/core/
```

---

## What ships (0.16)

1. `palm/services/` extraction from `palm/common/services/`
2. Per-service `registry.py` (REST + MCP entries)
3. REST under `/v1/api/…` only — legacy handlers deleted
4. MCP remounted by service; old tool names removed
5. Flows vs providers distinct execution behavior
6. Delete `common/services/views.py` — catalog shapes owned by definitions service domain
7. `MIGRATION-0.16.md`, `VISION-0.16.md`, ADR update

---

## Explicitly not 0.16 (redo later on new API)

- Standalone “OpenAPI from registry only” milestone
- WebSocket surface (binds to `execution/flows` after remount)
- Incremental catalog writes in old `DefinitionService` location

---

## References

- Spec: [docs/superpowers/specs/2026-06-30-service-registry-dynamic-rest-design.md](superpowers/specs/2026-06-30-service-registry-dynamic-rest-design.md)
- Plan: [docs/superpowers/plans/2026-06-30-service-registry-dynamic-rest.md](superpowers/plans/2026-06-30-service-registry-dynamic-rest.md)
- ADR: [docs/adr/005-service-domain-api.md](adr/005-service-domain-api.md) (0.16); [ADR 004](adr/004-cqrs-schemas-service-layer.md) (0.15 foundation)
- Migration: [MIGRATION-0.16.md](../MIGRATION-0.16.md)