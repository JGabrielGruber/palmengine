# ADR-005: Service Domain API (0.16)

## Status

**Proposed** — June 2026 (Palm 0.16)

## Context

ADR-004 (0.15) established a service layer in `palm.common.services` composing schema-validated CQRS. REST and MCP adapters became thinner, but **transport shape still dominated the product API**:

- REST handlers lived in resource-oriented files (`handlers/wizard.py`, `handlers/jobs.py`, …)
- MCP tools mirrored those paths (`palm_wizard_input`, …)
- `ExecutionService` unified interactive flows and provider invoke despite different behavior
- Three flat service classes in `common/` could not grow per domain without bloating the middle layer

0.15.4 completed internal cleanup (no migration window for experimental internals). External integrators still read `/v1/wizards` — not services.

## Decision

1. **Extract user-facing services to `palm/services/`** — Domain modules with own registries:
   - `definitions/` — catalog CRUD (flows, processes, resources)
   - `execution/` — coordinates `flows/`, `providers/`, `processes/` submodules
   - `system/` — debug, audit, sessions (renamed from `InternalService`)

2. **Retain shared primitives in `palm.common.services`** — `BaseService`, validation errors, read-model views only. CQRS buses and `CqrsSchemaRegistry` stay in `palm.common`.

3. **Runtimes mirror services** — REST handlers **per service domain** under `rest/{definitions,execution,system}/`, not per legacy resource file. MCP splits into matching packages. Prefix: `/v1/api/…`.

4. **Flows ≠ providers** — Separate registry contracts and service classes:
   - `execution/flows/` — instance REPL (create, input, backtrack, resume)
   - `execution/providers/` — catalog + invoke (no instance verb tree)
   - `execution/processes/` — process-scoped runs

5. **Intentional breaking change** — Delete legacy REST handler tree and monolithic MCP tool map. No compatibility shim for `/v1/wizards` or `palm_wizard_*`. Document in `MIGRATION-0.16.md`.

6. **Host surface** — `ApplicationHost` / `ServerContext` expose `.definitions`, `.execution`, `.system`. Remove `.internal`.

## Alternatives considered

| Alternative | Why not chosen |
|-------------|----------------|
| Incremental OpenAPI/registry on old handlers | Perpetuates transport-shaped API; superseded by service extraction |
| Keep services in `palm.common` | Violates SRP as domains grow; blurs common coordination vs user API |
| Single execution registry for flows + providers | Different verbs and mental models; forces false uniformity |
| Deprecation window for REST/MCP | User direction: experimental break; redo integrator docs not shims |
| Generic `ServiceContributor` metadata framework | 0.16 uses manual per-domain registries; framework deferred |

## Consequences

### Positive

- **Services are the product** — CLI, REST, MCP, Explorer all document against `palm.services`
- Domain modules scale independently with own `registry.py`
- Clear separation: catalog (`definitions`) vs run (`execution`) vs observe (`system`)
- Flows and providers evolve without coupling invoke to instance REPL

### Negative / migration cost

- All REST clients and MCP agent configs must update URLs and tool names
- Explorer and tests touching old paths require bulk update
- Temporary duplication possible during phased extraction (plan phases 0.16a–e)

### Supersedes (partial)

- ADR-004 **service package location** (`palm.common.services` → `palm.services`)
- ADR-004 principles **remain**: CQRS composition in services, thin runtimes, instance-centric flows, in-process MCP

## References

- [ADR-004](004-cqrs-schemas-service-layer.md)
- [VISION-0.16](../VISION-0.16.md)
- [MIGRATION-0.16](../../MIGRATION-0.16.md)
- [Design spec](../superpowers/specs/2026-06-30-service-registry-dynamic-rest-design.md)