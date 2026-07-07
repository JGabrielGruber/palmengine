# Vision 0.25 — Design Service

**Theme:** A sixth service domain for safe, structured definition evolution — propose, validate, analyze impact, commit revisions, and auto-migrate compatible instances.

**Status:** Shipped **0.25.0** on PyPI (bundles full 0.24 + 0.25 stack per [ADR-008](adr/008-design-service.md))  
**Depends on:** [0.24 definition revisioning](VISION-0.24.md) ✅  
**ADR:** [008-design-service.md](adr/008-design-service.md) · **Plan:** [design-service-plus.md](superpowers/plans/2026-07-07-design-service-plus.md)

---

## Why 0.25, not 0.24

Design Service orchestrates **revision publishes** and **migration triggers**. Without append-only revision history (0.24), it would be a thin wrapper around today's mutable `DefinitionService.create_flow` / `update_flow` — useful validation, but not safe evolution.

---

## What shipped (0.25.0)

| Surface | Delivered |
|---------|-----------|
| Service | `DesignService` — `propose_flow`, `validate_proposal`, `analyze_proposal_impact`, `commit_proposal`, `discard_proposal` |
| Host | `host.design` / `ctx.design` |
| REST | `POST/GET /v1/api/design/proposals`, `…/validate`, `…/impact`, `…/commit` |
| MCP | `palm_design_*` tools (recommended agent path for catalog writes) |
| Extension | `register_design_contributor()` for pattern-specific validation |

## Goal

| Responsibility | Delegates to |
|----------------|--------------|
| Propose definition changes | In-memory or storage-backed proposal store |
| Validate proposals | `definitions.validate_flow`, `prepare_flow_from_body`, pattern validators |
| Analyze impact | 0.24 impact query — affected instances, compatibility flags |
| Commit | `definitions.create_flow` / `update_flow` (revision append, 0.24.1) |
| Trigger migration | **Auto-migrate** compatible instances on commit (0.25.3); 0.24 rules + `migrate_instance` |
| Agent surface | MCP `palm_design_*` tools + `palm_assist` design aliases (final release) |

**Layered coexistence:** `DefinitionService` CRUD remains for direct integrators. Design Service is the **recommended agent path**.

---

## References

- Draft spec: [design-service-design.md](superpowers/specs/2026-07-03-design-service-design.md)
- Foundation: [VISION-0.24.md](VISION-0.24.md)