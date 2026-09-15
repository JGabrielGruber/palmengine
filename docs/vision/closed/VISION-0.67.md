# VISION 0.67 — Dependents require the organ

**Status:** ✅ **Theme closed** (José 2026-08-21) at `0.67.0`.  
**ADR:** [036](../../adr/036-require-capability.md) **Accepted**  
**Migration:** [MIGRATION-0.67](../../migrations/MIGRATION-0.67.md)  
**Map:** [PALM.md](../../PALM.md) · seed [VISION-ASSEMBLY](../VISION-ASSEMBLY.md) · prior [VISION-0.66](VISION-0.66.md) (**closed**) · sequence [VISION-0.64](VISION-0.64.md) step 4  
**Debt:** [SD-020](../../../TECH-DEBT.md#sd-020) (face paid; dependents paid)

**Exit:** José closed the theme (2026-08-21). Dependents ask the published face. Costume composted: [VISION-0.68](VISION-0.68.md) (**closed**). Residual [SD-023](../../../TECH-DEBT.md#sd-023).

This minor is **assembly remainder step 4**: callers that still treat `may_run_business` as the organ list now ask the published face. The face already publishes installed names. Dependents must use them.

---

## Goal

An act that needs an organ **requires that organ** on the published gate. Business does not dig `StructureSeat` or the supervisor. Ready stays the short wall. Membership is a second question on the same snapshot.

`require_business_admission` stays ready-only. A sibling **`require_capability(source, name)`** fail-closes on ready, then on `has_capability(name)`.

`able` is a query. Zero-arg `able()` stays `started ∧ may_run_business`. A name is extra fact, not a decorator, not a second wall.

## Floor

- `require_capability(source, name)` in the same home as `require_business_admission` (`palm.system.structure.errors`).  
- Same published *source* (snapshot, gate, zero-arg factory). Coerce once.  
- Not ready → `AdmissionRefusedError` (same as today). Ready but name missing → `CapabilityRefusedError` (carries snapshot + name).  
- One proof: a drain-shaped caller uses `require_capability(..., "work_drain")` and does not treat `may_run_business` as membership.  
- `able` may close over a name. The install-board type stays `Callable[[], bool]`. Do not add `@require` / `@able`.

**Ready / refuse** stay a short gate. Do not invent a capability named `ready`.

**Floor function:** `require_capability` + `CapabilityRefusedError` + drain-shaped proof (0.67.1). Ready without the organ is not membership.

## Growth

Façades and tests that freeze `may_run_business` as the organ list. Work-plane `able` that should mean drain is here. Host `start_ports.able` (drain + ready; wait stays ready) landed 0.67.3. Surface voice for `CapabilityRefusedError` landed 0.67.4. Schedule fire (`tick_schedules` / host `tick_work`) landed 0.67.5. Vitality `work_cycle` drain proofs pin `local.cli` (0.67.6). First remaining composition king **journal** landed 0.67.7 (DNA list + attach hand; `composition.has` dies on that unit). Journal leftover (one attach, one host object, not a fake loop) landed 0.67.8. Next remaining composition king **projections** landed 0.67.9 (DNA list + attach hand; `composition.has` dies on that unit). Projections leftover (one attach, one host object, not a fake loop) landed 0.67.10. Next remaining composition king **compensation** landed 0.67.11 (DNA list + attach hand; `composition.has` dies on that unit). Compensation leftover (one attach, one host object, not a fake loop) landed 0.67.12. Next remaining composition king **webhook** landed 0.67.13 (DNA list + attach hand; `composition.has` dies on that unit). Webhook leftover (one dispatcher; host slot aliases it; URLs refine that object; not a fake loop) landed 0.67.14. Unread packaging flags `enable_compensation` / `enable_webhook_dispatcher` composted 0.67.15. Next remaining composition king **analytics** landed 0.67.16 (DNA list + attach hand; `composition.has` dies on that unit). Analytics leftover (one organ; host slot aliases it; `analytics_enabled` refines that object; not a fake loop) landed 0.67.17.

**Not floor:** retune every `require_business_admission` site. Optional organ arg on that function.

## Locks (José 2026-08-20)

| # | Lock |
|---|------|
| **1** | **Two doors.** `require_business_admission` = ready. `require_capability` = ready **then** installed name. Do not add an organ argument to the first function. |
| **2** | **No decorators.** Inject a gate, then require. A wrapper may close over a name. |
| **3** | Field names stay **`capabilities`** / **`has_capability`**. |
| **4** | Remaining composition kings start **in 0.67** (0.67.7+). Do not open 0.68 for this pile. |
| **5** | **Roles, not a shared drain** (José 2026-08-21). Do not pay webhook leftover or delivery as two processes polling one `OutboxStore`. Do not add a cross-process file lock as the scale story. Scale home is [VISION-0.56](../VISION-0.56.md): a parent process starts child runtimes and assigns place/storage. Spoken names: orchestrator, supporter, worker → law: control home / [support place](../../PALM.md) / [work place](../../PALM.md). Each role owns its work. They do not race one pending index. Recursion is the [Palm provider](../../PROVIDER-APPS.md) (Palm calling Palm), not a fight for a data-dir file. |
| **6** | **No outside callers** (José 2026-08-21). Current use is dogfood and examples. Do not keep unread flags, twin seats, or living docs that promise POST in order to protect a missing operator. Trim the costume. Closed chronicles stay history. |

Lock 1 is the fork from the 0.66 close sitting. José opened 0.67 after the two questions were named. Override if the one-door optional arg is preferred. Lock 5 is the fork from leftover option B as “whoever drains the shared store POSTs.” Lock 6 is the fork from preserving webhook packaging for legacy.

## Forbidden always

- Copy `LOCAL_CAPABILITY_HANDS` onto the snapshot or the require.  
- Definition `requires`.  
- A fake capability named `ready`.  
- `require_capability` that skips the ready wall.  
- Land journal as a no-op organ.  
- Hide the gate in a decorator stack.  
- Pay webhook leftover as two drainers on one `OutboxStore` (flock / first-ACK-wins).  
- Keep unread packaging or a recover twin “for operators” that do not exist.

## Not this theme

- Engine as walker. Places. Surface compost. Navigator. Tunnels. Grove.  
- Workload spawn of support / work processes (lock 5). That is [VISION-0.56](../VISION-0.56.md), not a 0.67 leftover.  
- If drain/outbox still show first-organ costume, that work is still **0.64** / **0.65** law.  
- Remaining costume after leftover (empty boot phases, bare `enable_event_outbox`, living POST lies) — [VISION-0.68](VISION-0.68.md) (**closed**).

## Guide slices (not a sealed contract)

| Slice | Intent |
|-------|--------|
| **0.67.0** | Plan + ADR-036 Proposed + locks. ✅ |
| **0.67.1** | `require_capability` + `CapabilityRefusedError` + drain-shaped proof. ✅ |
| **0.67.2** | Work-plane `able` closes over `work_drain`. Wait stays ready. ✅ |
| **0.67.3** | Host `start_ports.able` is drain; wait stays ready. ✅ |
| **0.67.4** | Surface voice for `CapabilityRefusedError` (`capability_refused`). ✅ |
| **0.67.5** | Schedule fire uses the same able as tick (drain). ✅ |
| **0.67.6** | Vitality `work_cycle` drain proofs pin `local.cli`. ✅ |
| **0.67.7** | Journal: DNA list + attach hand + `composition.has` dies on that unit. ✅ |
| **0.67.8** | Journal leftover: one organ on the runtime bus; host slot aliases it; not a loop. ✅ |
| **0.67.9** | Projections: DNA list + attach hand + `composition.has` dies on that unit. ✅ |
| **0.67.10** | Projections leftover: one organ on the runtime bus; host slot aliases it; not a loop. ✅ |
| **0.67.11** | Compensation: DNA list + attach hand + `composition.has` dies on that unit. ✅ |
| **0.67.12** | Compensation leftover: one organ on the runtime bus; host slot aliases it; not a loop. ✅ |
| **0.67.13** | Webhook: DNA list + attach hand + `composition.has` dies on that unit. ✅ |
| **0.67.14** | Webhook leftover: one dispatcher; host slot aliases it; URLs refine that object; not a loop. ✅ |
| **0.67.15** | Unread-flag compost: settings drop `enable_compensation` / `enable_webhook_dispatcher`; dead `attach_runtimes` gone. ✅ |
| **0.67.16** | Analytics: DNA list + attach hand + `composition.has` dies on that unit. ✅ |
| **0.67.17** | Analytics leftover: one organ; host slot aliases it; `analytics_enabled` refines that object; not a loop. ✅ |
| **0.67.18+** | Not opened. José exited; costume is [VISION-0.68](VISION-0.68.md) (**closed**). |
| **exit** | José · ADR-036 Accepted · stamp `0.67.0`. ✅ |

*The face reads the fact. Dependents ask the face.*
