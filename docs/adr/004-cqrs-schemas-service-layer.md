# ADR-004: CQRS Schemas and Service Layer

## Status

**Accepted** — June 2026 (Palm 0.15)

## Context

Palm 0.14 delivered a full MCP operator adapter and mature CQRS (command/query buses, projections, pattern contributors). Runtimes nonetheless owned duplicated contracts:

- REST handlers validated bodies with hand-maintained schemas in `rest/schemas.py`
- MCP stdio proxied every tool call through HTTP (`PalmRestClient`)
- Inspect and catalog logic was embedded in route handlers

CQRS types were plain dataclasses with no attached metadata. There was no stable **user-facing business API** between runtimes and buses — making it hard to evolve surfaces independently or validate consistently.

Contributors and agents needed a single story for:
- Where validation schemas live
- How REST/MCP/CLI should call Palm (services, not raw CQRS)
- How instance-centric execution should work (`instance_id` as primary handle)

## Decision

1. **`CqrsSchemaRegistry`** — Register `DictStateSchema` per command/query type. Patterns contribute schemas via extended `CqrsContributor` (`command_schemas`, `query_schemas`). `BaseService.dispatch` / `ask` validate before bus dispatch.

2. **Service layer in `palm.common.services`** — User-facing API that **composes** CQRS (many-to-one):
   - `InternalService` — operational inspect/debug
   - `DefinitionService` — flow/process/resource catalog
   - `ExecutionService` + `InstanceSession` — instance-centric run/input/lifecycle
   - `ReplSession` — CLI REPL active-instance handle

3. **Thin runtime adapters** — REST/MCP handlers map HTTP/MCP args → `service.method()` → response serialization. No business branching in route tables when a service method exists.

4. **Instance-centric execution** — Primary metaphor: `execution.on(instance_id)`. Pattern-specific command selection uses `interactive_runtime` registry hooks and `InspectInstanceQuery` — **not** wizard imports in `palm.common`.

5. **MCP in-process path** — `PalmInProcessBackend` implements the `PalmRestClient` duck-type on `ServerContext`. Enabled via `PALM_MCP_IN_PROCESS=1` or attached `ctx`. Remote HTTP proxy remains for cross-process deployments.

6. **Boundary preserved** — Services live in `palm.common`; they import buses and registries, never `palm.runtimes` or `palm.patterns.wizard`. Pattern status queries register via `instance_status_query` on `CqrsContributor`.

## Alternatives considered

| Alternative | Why not chosen (0.15) |
|-------------|----------------------|
| **Pydantic models for CQRS** | Larger migration; `DictStateSchema` already powers state validation |
| **1:1 CQRS route exposure** | Surfaces stay verbose; no business composition layer |
| **Services in `palm.app` only** | Server standalone mode and tests need services without full host |
| **MCP always HTTP** | Local agent loops pay round-trip latency; in-process is default for dev |
| **`ServiceContributor` registry now** | No pattern yet needs custom business methods beyond instance verbs |

## Consequences

### Positive

- One inspect/catalog/execution API shared by REST, MCP, and host
- MCP local development works without `palm server` when in-process
- Schema registration colocated with CQRS contributors — single source of truth emerging
- `test_common_boundary.py` + service unit tests guard `palm.common` purity
- REST URLs unchanged; handlers shrink

### Negative / trade-offs

- Two MCP backends (`PalmInProcessBackend`, `PalmRestClient`) to maintain
- Some REST schemas remain until OpenAPI is generated from registry
- `ExecutionService` needs runtime resolver on host (slightly more wiring than standalone server)
- Definition write paths still REST/Studio-direct until 0.16

## References

- [docs/VISION-0.15.md](../VISION-0.15.md)
- [docs/superpowers/specs/2026-06-30-cqrs-schemas-service-layer-design.md](../superpowers/specs/2026-06-30-cqrs-schemas-service-layer-design.md)
- [AGENTS.md](../../AGENTS.md) — extension table and MCP conventions
- [docs/MCP.md](../MCP.md) — in-process operator setup