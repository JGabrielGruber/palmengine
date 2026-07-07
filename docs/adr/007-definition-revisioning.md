# ADR-007: Definition Revisioning & Migration (0.24)

## Status

**Accepted** — July 3, 2026 (Palm 0.24 vision)

## Context

Palm stores flow definitions in a **mutable** [`DefinitionRepository`](../../src/palm/common/persistence/definition_repository.py). Each [`ProcessInstance`](../../src/palm/instances/process_instance.py) snapshots `flow_definition` at submit time, so running sessions survive catalog overwrites. This implicit pinning works for resume but fails for **evolution**:

- No revision history or rollback
- No explicit `flow_id + revision` binding on instances
- No migration path for live instances when step topology or state schema changes
- A future **Design Service** cannot implement meaningful `commit` without `publish revision N+1`

External feedback proposed a Design Service first. Palm's architecture assessment concluded **revisioning and migration primitives must precede** Design Service (deferred to 0.25).

[`FlowDefinition`](../../src/palm/definitions/flow.py) already serializes `"version": 1` — this is **format version**, not semantic revision. The two must not be conflated.

## Decision

1. **Append-only revisions for flows (0.24.1)** — `DefinitionRepository` stores `flow:{id}:rev:{n}` with a `latest` pointer. `publish_flow_revision` appends; `get_flow` resolves latest by default.

2. **Instance revision pin** — `ProcessInstance` gains `flow_revision: int | None`. Submit sets pin + retains snapshot. Resume prefers snapshot; no silent auto-upgrade to catalog latest.

3. **Migration rules registry (0.24.2)** — `DefinitionMigrationRule` in `palm/common/persistence/definition_migration.py` with `can_migrate` + `migrate_state`. Dedicated `register_migration_rule()` registry; no core changes.

4. **Impact query v0 (0.24.2)** — Definitions domain query listing instances behind `latest_revision` with compatibility flags. Feeds 0.25 Design Service.

5. **Migration execution hooks (0.24.3)** — Instance metadata `migration_status`, optional example migration wizard flow, compensation on multi-step failure.

6. **DefinitionService CRUD retained** — `create_flow` / `update_flow` semantics evolve to publish revisions; direct integrator path unchanged at transport level. Design Service (0.25) layers propose/validate/orchestrate on top.

7. **Core purity preserved** — Revision types and repository logic in `palm/definitions/` + `palm/common/persistence/`. No `palm/core/` imports from outer packages.

## Alternatives considered

| Alternative | Why not chosen |
|-------------|----------------|
| Design Service first (0.24) | Commit model needs revisions; would duplicate mutable overwrite with extra validation only |
| External version store (Git, OCI) | Palm already has `StorageEngine`; inline revision keys keep resume/inspect cohesive |
| Content-hash-only revisions (no monotonic int) | Harder for operators and migration rules; monotonic `revision` + optional `content_hash` |
| Auto-migrate all instances on publish | Risky; explicit migration request + rules required |
| New `palm/core/` versioning engine | Violates registry-based extension; repository + hooks sufficient |
| Deprecate DefinitionService writes | User policy: layered coexistence; agents steered to Design Service in 0.25, not forced |

## Consequences

### Positive

- Clear upgrade path for live instances
- Rollback via loading prior revision
- Design Service (0.25) gets a real `commit_revision` primitive
- Impact analysis grounded in instance projection data
- Reuses `TransformEngine` registry pattern and `CompensationCoordinator`

### Negative / migration cost

- Repository key layout change; lazy migration for legacy records
- `update_flow` semantic change (append vs overwrite) — requires `MIGRATION-0.24.md` at 0.24.1 ship
- Instance model field addition; persistence format bump
- Process/resource revisioning deferred — flows-only in 0.24.1

### Enables (0.25+)

- `palm/services/design/` — propose, validate, impact, commit
- Append-only audit log on revision publishes
- Agent MCP tools for safe definition evolution

## References

- [VISION-0.24.md](../VISION-0.24.md)
- [Definition revisioning design spec](../superpowers/specs/2026-07-03-definition-revisioning-design.md)
- [Design Service draft (0.25)](../superpowers/specs/2026-07-03-design-service-design.md)
- [ADR-005](005-service-domain-api.md) — service domain layout
- [ADR-006](006-assist-domain.md) — assist as fifth service; design as sixth in 0.25