# ADR-008: Design Service (0.25)

## Status

**Accepted** — July 7, 2026 (Palm 0.25.0 MVP local · final release pending)

## Context

[ADR-007](007-definition-revisioning.md) delivered append-only flow revisions (0.24.1), migration rules and impact queries (0.24.2), and instance migration execution (0.24.3). Agents can still mutate the catalog directly via `DefinitionService` (`create_flow`, `update_flow`) and MCP `palm_definitions_*` tools. There is no structured **propose → validate → impact → commit** loop, no draft envelope, and no orchestration that ties revision publish to instance migration.

External feedback described a Design Service. Palm adapts it as a **sixth user-facing service domain** in `palm/services/design/` — layered atop revisioning, not a replacement for catalog CRUD ([ADR-005](005-service-domain-api.md)).

0.25.0 MVP shipped locally: `DesignService`, in-memory proposals, REST `/v1/api/design/proposals`, MCP `palm_design_*`, and `register_design_contributor()`. Several spec items remain before the **single final PyPI release** that bundles the full 0.24 migration stack and Design Service.

## Decision

1. **Add `palm/services/design/`** as the sixth service domain — structured definition evolution composing `definitions` (validate, impact, publish revision, migrate instance).

2. **Core workflow** — Agents and integrators use:
   - `propose_flow` → `validate_proposal` → `analyze_proposal_impact` → `commit_proposal` (optional `discard_proposal`)
   - `commit_proposal` publishes via `definitions.create_flow` / `update_flow` (revision append semantics from 0.24.1), then closes the proposal.

3. **Layered coexistence** — `DefinitionService` direct writes remain for Explorer and integrators. MCP tool descriptions **steer agents** to `palm_design_*`; definition write tools are not removed.

4. **Business rules live in `DesignService`** — Service methods are the authoritative contract. REST and MCP are thin adapters calling the service. **CQRS command/query bindings are transport plumbing below the service layer** and may be added in a later slice; they are not a prerequisite for shipping business behavior (durable store, auto-migrate, assist aliases, agent safety).

5. **Auto-migrate on commit** — After a successful revision publish, `commit_proposal` **automatically migrates affected instances** that the impact analysis marked compatible. Instances marked blocked are skipped and reported in the commit result; revision publish is not rolled back (append-only). Migration failures set per-instance `migration_*` metadata (0.24.3) and surface in the response; operators may retry via `definitions.migrate_instance`.

6. **Proposal storage** — MVP uses in-memory `DesignProposalRepository`. Final release requires **durable** `StorageEngine` keys (`palm:design:proposals:{id}`) wired on `ApplicationHost` when storage is initialized.

7. **Extension** — `register_design_contributor()` for pattern-specific validators (wizard slug integrity, resource ref checks). Same registry-at-bootstrap pattern as assist and MCP contributors.

8. **Host surface** — `ApplicationHost` / `ServerContext` expose `.design` alongside `.definitions`, `.execution`, `.system`, `.assist`.

9. **Agent safety (final release)** — Design commits follow 0.23 mutation discipline where agents drive writes: validate + impact inspect before commit; optional strict token for `palm_design_commit` (`PALM_MCP_REQUIRE_INPUT_TOKEN` pattern). `palm_assist` design path aliases are part of the final release surface.

10. **Single final release** — PyPI ships **one descriptive release** containing the complete 0.24 revisioning/migration stack (0.24.1–0.24.4) **and** the complete Design Service (0.25 through durable store, auto-migrate, assist integration, docs). No partial 0.24-only or 0.25-only PyPI cut unless explicitly requested.

## Alternatives considered

| Alternative | Why not chosen |
|-------------|----------------|
| Design Service before revisioning (0.24) | Commit needs `publish_flow_revision`; would be validation-only over mutable overwrite ([ADR-007](007-definition-revisioning.md)) |
| Deprecate `palm_definitions_*` write tools | User policy: layered coexistence; steering via descriptions, not removal |
| CQRS-first implementation | Business rules belong in `DesignService`; CQRS is adapter plumbing, not the domain contract |
| Manual migration only on commit | User decision: auto-migrate compatible instances; reduces operator toil for agent-driven evolution |
| Separate PyPI releases for 0.24 and 0.25 | User decision: one final release for the overall migration + design story |
| Durable proposals in `palm/common/services/` | Violates domain ownership; proposals belong in `palm/services/design/` |
| Auto-migrate blocked instances | Unsafe; blocked flag from impact query must be respected |
| Roll back revision on migration failure | Conflicts with append-only revision history; compensation + retry instead |

## Consequences

### Positive

- Agents get a safe, inspectable path for catalog evolution
- Commit ties revision publish to instance migration in one orchestrated step
- Reuses 0.24 impact query, migration rules, and `migrate_instance` — no duplicate evolution logic
- `register_design_contributor()` enables pattern validation without core edits
- Single release tells a coherent story: revisioning → migration → design orchestration

### Negative / cost

- Sixth service domain to wire, test, and document
- Auto-migrate on commit increases commit latency and failure modes (partial migration sets)
- In-memory MVP proposals are lost on restart until durable store ships
- CQRS schemas for design deferred — bus-level inspect/validation parity lags other domains briefly
- Operators must understand: commit always publishes; migration is best-effort for compatible instances

### Relationship to other ADRs

- **Builds on ADR-007** — Design Service orchestrates revision publish and migration primitives
- **Builds on ADR-006** — Optional `palm_assist` aliases for design workflow; assist remains fifth domain
- **Follows ADR-005** — Same `palm/services/` layout, per-domain REST/MCP, `host.design` surface
- **ADR-004 unchanged** — When CQRS bindings land, they compose through `BaseService` like other domains

### Enables (0.25+)

- Dogfooding: meta-flows for `palm://agent/guide` and example catalog maintenance
- Pattern design contributors (wizard, pipeline)
- Append-only audit entries on commit (stretch)
- Process/resource revisioning remains deferred ([ADR-007](007-definition-revisioning.md))

## Implementation phases (pre–final release)

| Phase | Theme | Priority |
|-------|-------|----------|
| 0.25.1 | Docs hygiene, `MIGRATION-0.25.md`, plan sync, this ADR | Now |
| 0.25.2 | Durable `StorageEngine` proposal repository | Required for release |
| 0.25.3 | Auto-migrate on `commit_proposal` | Required for release |
| 0.25.4 | Agent safety + `palm_assist` design aliases | Required for release |
| 0.25.5 | Pattern `register_design_contributor()` implementations | Recommended |
| 0.25.6 | Dogfooding examples | Stretch |
| 0.25.7 | CQRS bindings (transport only) | After business slices |

## References

- [VISION-0.25.md](../VISION-0.25.md)
- [VISION-0.24.md](../VISION-0.24.md)
- [Design Service design spec](../superpowers/specs/2026-07-03-design-service-design.md)
- [Design Service+ plan](../superpowers/plans/2026-07-07-design-service-plus.md)
- [ADR-007](007-definition-revisioning.md) — revisioning and migration foundation
- [ADR-006](006-assist-domain.md) — assist as fifth domain
- [ADR-005](005-service-domain-api.md) — service domain layout
- [MIGRATION-0.24.md](../../MIGRATION-0.24.md)