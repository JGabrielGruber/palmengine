# Appendix — structure materialize cut (2026-08-17)

**Status:** Standing engineering note. **Not** a theme plan. **Not** a VISION rewrite.  
**Locked by José:** first unit and “no no-op.”  
**Code (2026-08-17):** `StructureDefinition.capabilities` + manager materialize of `work_drain`; host/mode/composition are no longer peer kings for that unit.  
**Stamp:** José closed **0.64** (2026-08-18) at `0.64.0`.

**Read after compact:** [VISION-0.64 after compact](../../vision/closed/VISION-0.64.md#after-compact-2026-08-17) → **this file §1 + §7** → implement.  
Do not re-harvest the tree unless code contradicts this note.

**Map:** [PALM.md](../../PALM.md) · [TECH-DEBT SD-020 / SD-021 / SD-016](../../../TECH-DEBT.md) · present [VISION-0.64](../../vision/closed/VISION-0.64.md) · seed [VISION-ASSEMBLY §0](../../vision/VISION-ASSEMBLY.md#0-progress-honesty-2026-08-08)

---

## 1. Situation (as-built)

Admission is real. **`work_drain` membership install is real.** Other capabilities still live on composition.

| Layer | Built | Residual |
|-------|--------|----------|
| Core structure | Reconciler + `StructureDefinition.capabilities`. Builtin definitions list `work_drain` on cli/server/all_in_one/worker. Omit is enough. | No definition `requires` / start-fact vocabulary. |
| System structure | Walker `apply_local_capabilities` loops `LOCAL_CAPABILITY_HANDS`. Hand takes `CapabilitySeats`. Assemble fills seats from `ctx` + install board. Journal is an attach hand (not a loop). | Inbound still freelance. |
| Boot / runtime | `system.background.start` starts **registered** drain when start ports are bound. `system.outbox.wire` skips when DNA omits `outbox`. | |
| Host | Definition seed at spawn. Host schedule ends at ready. Host does not start drain. Status and coordinator read `runtime.work_plane`. Composition does not list `work_drain`. Assemble uses `shell.structure`. Vitality default probes share `attr_resolver` / hub / `first_resolver`. | Inventory still probes structure as eyes. |
| Product | Admission oath on assist + four execution façades. | Constructors still take a runtime bag. No service takes `ExecutionPort`. |
| Surfaces | Transport + admission voice. | Not this cut (`SU-*`). |

A new organ is a definition name + hand. Composition no longer writes `work_drain`. Settings/deployment have no drain switch.

---

## 2. Classification (do not mix)

| Class | Meaning | Examples |
|-------|---------|----------|
| **Spine** | Sequential. One owner. Definition as install set. | Membership field on definition; manager apply; demote `composition.has` / `BootMode` on that unit. |
| **Same-cut** | After the interface is frozen. May parallel later. | Product `ExecutionPort` / session seat / drop `admission_gate()` fallback to the runtime. |
| **Named residual** | Leave named. | Cancel/stop, LIST/DESCRIBE, unit engine access, packaging env, doctor, `*_to_runtime`. |
| **Other theme** | Do not open here. | Surface deflation, plugin catalog as structure definition, OS/workload place spawn as first unit, SD-019, Grove. |
| **Docs drift** | Do not treat as done. | Seed comments that definition is king of **wiring**; `composition.py` as sole membership switch; vault skeleton. |

Isolated “fix SD-016 everywhere” or residual-ledger cleanup is a workaround. Product does not own structure.

---

## 3. Locked (landed) — first unit

| Decision | Lock |
|----------|------|
| First materialize unit | **`work_drain` under a `capabilities` section** (local source only). |
| No-op prove-out | **No.** Do not land `journal` (or similar always-on) only to prove the field. |
| Scope of first slice | Definition names capabilities → manager materializes **`work_drain`** → seed/mode/profile stop being peer kings **for that unit**. Admission stays fail-closed. |
| Surfaces | Out of cut. |
| Product seat DI (SD-016) | Boy-scout only on files this spine already touches. Not a second front. |

### 3.1 Why `work_drain`

It is already a triple king: settings flag → `MEMBERSHIP_CAPABILITY_SEEDS` → `composition.has("work_drain")` → host schedule → definition `refuse:background_drain`.

Not first: default planes (always-on kernel), `ensure_core_plugins` (wide), always-on `journal` / `projections` / `workloads`, `outbox` (store vs loop vs node role).

### 3.2 Spine steps (sequential, one workspace)

1. Add local **capabilities** on `StructureDefinition` (frozenset of names). Builtin definitions **list what the body has**, not only what it refuses.
2. Manager **materializes** that set: register/start `work_drain` only if listed.
3. `composition.has("work_drain")` becomes a projection of the definition, or dies on that path.
4. `BootMode.allow_background_drain` stops being a peer OR.
5. Proof: drain starts iff the definition lists it (embedded vs cli/server).

Do not fan this out across worktrees. Shared types.

**After** this contract is in code, same-cut product seats may use parallel worktrees.

---

## 4. Theme routing

José stamped **0.64** (2026-08-17). The engineering cut in §3 does not change.

---

## 5. Code homes (start here)

| Concern | Path |
|---------|------|
| Definition | `src/palm/core/structure/definition.py` |
| Reconciler | `src/palm/core/structure/engine.py` (today: places + admission only) |
| Seed catalog | `src/palm/system/structure/seed.py` (`MEMBERSHIP_CAPABILITY_SEEDS`) |
| Seat / assemble | `src/palm/system/structure/seat.py`, `loop.py`, `phase_assemble.py` |
| Composition seed | `src/palm/app/host/composition.py` (does not type `work_drain`) |
| Hands / walker | `src/palm/system/structure/hands.py`, `materialize.py` |
| Host schedule | `src/palm/app/host/boot/host_schedule.py` (ends at `host.ready`; does not start drain) |
| System start | `src/palm/system/subsystems/supervisor/phase_background.py` (`system.background.start`) |
| Freelance catalog | `src/palm/system/subsystems/supervisor/definition.py` (`DEFAULT_CONTINUOUS_DEFINITIONS` is empty; hands register `work_drain` and `outbox`; no named `WORK_DRAIN_SERVICE` / `OUTBOX_SERVICE` recipes) |
| Bootstrap flag → cap | `src/palm/app/bootstrap.py` |

---

## 6. Explicit non-goals for the focused session

- Re-run a repo-wide harvest.
- Close 0.63 by more residual cartography.
- Invent a second admission path.
- Surface compost, MCP dual stack, explorer splits.
- Full SD-016 sweep.
- Provider / cache membership sources (local only).
- Invent definition `requires` / install-port vocabulary.
- Land journal as a second organ before pile B is honest.

---

## 7. Next motion after compact

José locked this order (2026-08-17). Not a slice table. Not patch stamps.

**Landed:** definition `capabilities` · walker · `CapabilitySeats` from `ctx` + board · start from registered service · no `host._work_drain_listed` · tests/status use `runtime.work_plane` · default wire catalog does not register `work_drain`. Commits `6e50fd6b`, `d1b3c23a`.

**Process:** explore agents in parallel. One implementer at a time. Do not fan `seed.py`, `hands.py`, `phase_assemble.py`, `definition.py` (supervisor) across writers.

| Pile | Do | Do not |
|------|----|--------|
| **A** | **Landed.** `allow_background_drain` gone. Seed twins gone. | Do not put the field back. |
| **B1** | **Landed.** Default catalog is empty. Hands register `work_drain` and `outbox`. Unregister-on-unlist stays. | Do not put those names back on `DEFAULT_CONTINUOUS_DEFINITIONS`. |
| **B2** | **Landed.** `refuse_violations` reads `definition.has_capability("work_drain")`. Token stays `background_drain`. | Do not invent a new refuse vocabulary. |
| **B3** | **Landed.** Presets and seed fold do not write `"work_drain"`. Embedded definition no longer refuses `background_drain`. Omit is enough. Journal composition king paid 0.67.7. Projections composition king paid 0.67.9. Compensation composition king paid 0.67.11. Webhook composition king paid 0.67.13. Analytics composition king paid 0.67.16. Analytics leftover paid 0.67.17. | Do not wipe DNA membership to hide a listed organ. |
| **C** | **Landed.** Coordinator and host read `runtime.work_plane`. `host.start_plane` / `_start_plane` gone. Host schedule ends at ready. Drain start is `system.background.start`. Assemble uses `shell.structure`. Settings/deployment have no `enable_work_drain_service`. Vitality default probes share `attr_resolver` / hub / `first_resolver`. Journal attach hand landed 0.67.7; leftover costume paid 0.67.8 (one organ on the runtime bus). Projections leftover costume paid 0.67.10 (one organ on the runtime bus). Compensation leftover costume paid 0.67.12 (one organ on the runtime bus). Webhook leftover costume paid 0.67.14 (one dispatcher; URLs refine that object). Unread packaging flags composted 0.67.15. Analytics attach hand landed 0.67.16. Analytics leftover costume paid 0.67.17 (one organ; `analytics_enabled` refines that object). | No definition `requires`. |

**Copyable and closed** (José 2026-08-18) — [VISION-0.64](../../vision/closed/VISION-0.64.md). Outbox is [VISION-0.65](../../vision/closed/VISION-0.65.md) (**closed**). Admission face is [VISION-0.66](../../vision/closed/VISION-0.66.md) (**closed**). Step 4 dependents: [VISION-0.67](../../vision/closed/VISION-0.67.md) (**closed**). Costume composted: [VISION-0.68](../../vision/closed/VISION-0.68.md) (**closed**). Residual [SD-023](../../../TECH-DEBT.md#sd-023).
