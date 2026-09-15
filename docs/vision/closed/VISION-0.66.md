# VISION 0.66 — Admission sits on capabilities

**Status:** ✅ **Theme closed** (José 2026-08-20) at `0.66.0`.  
**ADR:** [035](../../adr/035-admission-sits-on-capabilities.md) **Accepted**  
**Migration:** [MIGRATION-0.66](../../migrations/MIGRATION-0.66.md)  
**Map:** [PALM.md](../../PALM.md) · seed [VISION-ASSEMBLY](../VISION-ASSEMBLY.md) · prior [VISION-0.65](VISION-0.65.md) (**closed**) · [VISION-0.64](VISION-0.64.md) (**closed**)  
**Debt:** [SD-020](../../../TECH-DEBT.md#sd-020) (face paid; dependents later)

**Exit:** José closed the theme (2026-08-20). The face publishes installed names. Step 4 dependents: [VISION-0.67](VISION-0.67.md) (**closed**). Costume composted: [VISION-0.68](VISION-0.68.md) (**closed**). Residual [SD-023](../../../TECH-DEBT.md#sd-023).

This minor is **assembly remainder step 3**: the admission face still answers “may this act run.” It **reads installed capabilities**. It is not a second walker.

---

## Goal

Business does not dig `StructureSeat` or the supervisor to learn which organs are here.

`AdmissionSnapshot` already publishes ready / phase / reasons. It now also publishes **installed** names: `capabilities` and `has_capability`. Same words as `StructureDefinition`. One meaning.

Membership law does not move. DNA lists → walker → hand. Omit means it is not here. Admission **reads** `StructureSeat.materialized_capabilities`. It does not copy `LOCAL_CAPABILITY_HANDS`.

## Floor

- Snapshot carries `capabilities: frozenset[str]` (default empty).  
- `has_capability(name)` on the snapshot.  
- `may_run_business` stays the organism-ready wall (phase READY, no block reasons, truth home up).  
- Coerce / `to_dict` / duck round-trip the new fields. Extra keys have defaults. Bool-only tests keep.  
- One proof: a product-shaped caller reads `has_capability("work_drain")` on the published gate and does not touch `runtime.structure`.  
- Engine does not become the walker. Seat fills the snapshot after materialize.

**Ready / refuse** stay a short gate. Do not invent a fake capability named `ready`.

**Floor met.** Eyes growth paid in 0.66.2.

## Growth

Eyes that nest `to_dict()` (inspect, menu, vitality raw) pick up keys for free. Doctor / packaging 3-key fallbacks may show the column.

**Not floor:** `require_business_admission` taking an organ name. `able` as membership. Journal / other composition kings. [SD-021](../../../TECH-DEBT.md#sd-021).

## Locks (José 2026-08-20)

| # | Lock |
|---|------|
| **1** | Publish **installed** names (`materialized_capabilities`), not DNA-listed-but-not-installed. |
| **2** | Field names: **`capabilities`** and **`has_capability`**. Do not invent a second word. |

## Forbidden always

- Copy `LOCAL_CAPABILITY_HANDS` onto the snapshot.  
- Definition `requires`.  
- A fake capability named `ready`.  
- Swap step 3 and step 4: do not retune `able` / façades as the first execute motion.  
- Land journal as a no-op organ to prove the field.

## Not this theme

- Step 4 dependents (`able`, façades, tests that freeze `may_run_business` as the organ list) — [VISION-0.67](VISION-0.67.md) (**closed**).  
- Remaining `composition.has` kings (journal, projections, webhook, compensation, analytics).  
- Places, surface compost, navigator, tunnels, Grove.  
- If drain/outbox still show first-organ costume, that work is still **0.64** / **0.65** law.

## Guide slices (not a sealed contract)

| Slice | Intent |
|-------|--------|
| **0.66.0** | Plan + ADR-035 Proposed + locks. ✅ |
| **0.66.1** | Snapshot + coerce + seat publish + proof test. ✅ |
| **0.66.2** | Eyes columns: packaging / doctor / vitality load + `admission_as_dict`. Nested `to_dict` was already enough for inspect / menu / vitality raw. ✅ |
| **exit** | José · ADR-035 Accepted · stamp `0.66.0`. ✅ |

*The face reads the fact. The walker stays the walker.*
