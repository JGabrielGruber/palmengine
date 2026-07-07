# Vision 0.25 — Design Service (deferred)

**Theme:** A sixth service domain for safe, structured definition evolution — propose, validate, analyze impact, and commit revisions.

**Status:** Stub — depends on [0.24 definition revisioning](VISION-0.24.md)  
**Target:** 0.25.0 implementation after 0.24.1–0.24.3 land

---

## Why 0.25, not 0.24

Design Service orchestrates **revision publishes** and **migration triggers**. Without append-only revision history (0.24), it would be a thin wrapper around today's mutable `DefinitionService.create_flow` / `update_flow` — useful validation, but not safe evolution.

---

## Goal (preview)

| Responsibility | Delegates to |
|----------------|--------------|
| Propose definition changes | In-memory or storage-backed proposal store |
| Validate proposals | `definitions.validate_flow`, `prepare_flow_from_body`, pattern validators |
| Analyze impact | 0.24 impact query — affected instances, compatibility flags |
| Commit | `definitions.publish_flow_revision` (0.24.1) |
| Trigger migration | 0.24 migration rules + optional migration flows |
| Agent surface | MCP `palm_design_*` tools + optional `palm_assist` aliases |

**Layered coexistence:** `DefinitionService` CRUD remains for direct integrators. Design Service is the **recommended agent path**.

---

## References

- Draft spec: [design-service-design.md](superpowers/specs/2026-07-03-design-service-design.md)
- Foundation: [VISION-0.24.md](VISION-0.24.md)