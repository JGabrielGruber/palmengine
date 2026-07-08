# ADR-009: Service CQRS Contributors

## Status

**Accepted** — July 2026 (Palm 0.25.9+)

## Context

Pattern apps register CQRS transport via `CqrsContributor` (`patterns/_registry.py`). Service domains (definitions, design) added revisioning and design orchestration types that were wired only on `ApplicationHost` (`cqrs_wiring.py`), not on standalone `ServerContext` used by in-process MCP. `DefinitionService.analyze_impact()` and `migrate_instance()` failed in standalone mode with `No handler registered for AnalyzeDefinitionImpactQuery`.

ADR-004 deferred a `ServiceContributor` registry. Design 0.25.7 added `wire_design_service_cqrs()` as a one-off third wiring path.

## Decision

1. **`ServiceCqrsContributor`** in `palm/services/_cqrs_registry.py` — mirrors pattern contributors for service-domain transport only.

2. **Domain-owned bindings** — `palm/services/<domain>/bindings/cqrs/` owns handlers, type catalog, contributor registration, and `wire_*` hooks. Business rules remain in `service.py`.

3. **Unified catalog** — `palm/common/cqrs/catalog.py` `collect_cqrs_*_types(mode="host"|"standalone")` is the single type list for host and standalone bus registration.

4. **Overwrite registration** — Generic host/standalone handlers register all catalog types first; `wire_all_service_cqrs()` overwrites service-owned types with domain handlers.

5. **Schema drain** — `build_schema_registry()` registers `command_schemas` / `query_schemas` from service contributors (design today; definitions when schemas are added).

6. **Host-only queries** — Projection-backed queries (`GetResourceInvocationsQuery`, etc.) stay in catalog `mode="host"` only.

## Consequences

- In-process MCP achieves parity with `ApplicationHost` for definitions impact/migrate and design commit.
- New service CQRS types: add contributor in domain `bindings/cqrs/`, extend catalog if core type, add parity test.
- `wire_service_cqrs_contributors` skips contributors without bootstrap context (supports partial host profiles).

## References

- [ADR-004](004-cqrs-schemas-service-layer.md)
- [ADR-008](008-design-service.md)
- [Plan](../superpowers/plans/2026-07-08-cqrs-bus-parity-and-0.26.md)