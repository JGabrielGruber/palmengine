# Design Service Design (0.25)

**Status:** 0.25.0 MVP shipped (local) · completion per [ADR-008](../../adr/008-design-service.md) + [plan](../plans/2026-07-07-design-service-plus.md)  
**Version target:** 0.25.0 MVP ✅ · final release bundles 0.24 + 0.25  
**Depends on:** [ADR-007 definition revisioning](../../adr/007-definition-revisioning.md) · [0.24.1+ implementation](../plans/2026-07-03-definition-revisioning.md) ✅  
**Vision:** [VISION-0.25.md](../../VISION-0.25.md)

---

## Problem

Agents can mutate definitions today via [`DefinitionService`](../../../src/palm/services/definitions/service.py) (`create_flow`, `update_flow`) and MCP `palm_definitions_*` tools. There is no structured **propose → validate → impact → commit revision** loop. External feedback described a Design Service; Palm adapts it as a **sixth service domain** atop revisioning — not a replacement for catalog CRUD.

---

## Goal

Introduce **`palm/services/design/`** as the recommended path for **agent-driven definition evolution**:

1. **Proposal envelope** — durable draft before commit
2. **Validation** — reuse `validate_flow`, pattern-specific contributors
3. **Impact analysis** — delegate to 0.24 `analyze_impact`
4. **Commit** — revision append via `create_flow` / `update_flow` (0.24.1)
5. **Migration trigger** — **auto-migrate** compatible instances on commit ([ADR-008](../../adr/008-design-service.md))
6. **MCP surface** — `palm_design_*` tools; optional `palm_assist` aliases

**Layered coexistence:** `DefinitionService` CRUD stays for direct integrators and Explorer.

---

## Principle

```
Agent / MCP
    ↓
palm/services/design/     propose · validate · impact · commit_revision
    ↓
palm/services/definitions/   publish_flow_revision · analyze_impact
    ↓
palm/common/persistence/       revisioned catalog
palm/common/transforms/        migration rules
    ↓
palm/definitions/ + palm/instances/
```

**Not** in `palm/common/services/` (primitives only since 0.16).  
**Not** in `palm/core/definitions/` (definitions live in `palm/definitions/`).

---

## Domain model (sketch)

### DesignService

Thin `BaseService` subclass composing `definitions`, `execution`, `system`:

| Method | Behavior |
|--------|----------|
| `propose_flow(body, *, base_flow_id=None)` | Store proposal; return `proposal_id` + validation preview |
| `get_proposal(proposal_id)` | Load proposal envelope |
| `list_proposals(*, flow_id=None)` | List open proposals |
| `validate_proposal(proposal_id, *, dry_run=True)` | `validate_flow` + optional BT dry-run |
| `analyze_proposal_impact(proposal_id)` | → `definitions.analyze_impact` for target revision |
| `commit_proposal(proposal_id)` | → `definitions.publish_flow_revision`; close proposal; audit entry |
| `discard_proposal(proposal_id)` | Remove draft |
| `dispatch(path, params)` | Command-path transport (mirror assist/flows) |

### Proposal storage

Recommend: `StorageEngine` keys `palm:design:proposals:{id}` with TTL optional. Alternative: in-memory for 0.25.0 MVP.

### Extension

`register_design_contributor()` — pattern-specific validators (wizard step slug integrity, resource ref checks). Same registry pattern as assist.

---

## CQRS (0.25 implementation)

| Command / Query | Summary |
|-----------------|---------|
| `ProposeFlowDefinitionCommand` | Create proposal |
| `ValidateDesignProposalQuery` | Validation + dry-run result |
| `AnalyzeDesignProposalImpactQuery` | Impact report |
| `CommitDesignProposalCommand` | Publish revision |
| `DiscardDesignProposalCommand` | Drop proposal |
| `ListDesignProposalsQuery` | Catalog open proposals |

Schemas in `palm/services/design/bindings/cqrs/`.

---

## REST / MCP (0.25 implementation)

### REST (`/v1/api/design/…`)

| Route | Verb |
|-------|------|
| `/design/proposals` | POST propose, GET list |
| `/design/proposals/{id}` | GET, DELETE discard |
| `/design/proposals/{id}/validate` | POST |
| `/design/proposals/{id}/impact` | GET |
| `/design/proposals/{id}/commit` | POST |

### MCP tools

| Tool | Summary |
|------|---------|
| `palm_design_propose_flow` | Create proposal from body |
| `palm_design_validate` | Validate proposal |
| `palm_design_impact` | Impact report |
| `palm_design_commit` | Publish revision |
| `palm_design_list_proposals` | List open proposals |

Agent policy: MCP descriptions steer definition mutations to design tools; `palm_definitions_create_flow` remains for direct integrators.

---

## Agent write safety

Reuse 0.23 mutation discipline where applicable:

- Inspect proposal / impact before commit
- Optional strict token for `commit` in agent deployments (`PALM_MCP_REQUIRE_INPUT_TOKEN` pattern — spec detail at 0.25 impl)
- Structured errors (`DesignCommitRejectedError` or reuse `MutationRejectedError` pattern)

---

## Dogfooding (0.25+)

Stretch goals after core commit path works:

- Meta-flow: “Propose MCP guide update from description”
- Partial maintenance of `palm://agent/guide` via design proposals
- Self-validation: design proposals for Palm's own catalog flows

---

## Explicit non-goals (0.25 MVP)

- Blockchain governance
- Deprecating DefinitionService MCP write tools
- Explorer visual designer
- Full automatic migration of all affected instances on commit

---

## References

- Foundation: [definition-revisioning-design.md](2026-07-03-definition-revisioning-design.md)
- Vision: [VISION-0.25.md](../../VISION-0.25.md)
- Assist precedent: [assist-domain-design.md](2026-07-01-assist-domain-design.md)
- ADR: [007-definition-revisioning.md](../../adr/007-definition-revisioning.md)