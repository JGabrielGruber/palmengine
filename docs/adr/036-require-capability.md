# ADR-036 — Require capability (dependents of the admission face)

**Status:** Accepted  
**Date:** 2026-08-20 · **Accepted:** 2026-08-21  
**Theme:** [VISION-0.67](../vision/closed/VISION-0.67.md) (**closed**)  
**Map:** [PALM.md](../PALM.md)  
**Related:** [ADR-032](032-organism-assembly.md) **Accepted** · [ADR-033](033-one-walker.md) **Accepted** · [ADR-035](035-admission-sits-on-capabilities.md) **Accepted**  
**Sequence:** [VISION-0.64](../vision/closed/VISION-0.64.md) step 4 · [SD-020](../../TECH-DEBT.md#sd-020)

José accepted (2026-08-21). Theme closed. Dependents ask the published face. Costume composted: [VISION-0.68](../vision/closed/VISION-0.68.md) (**closed**). Residual [SD-023](../../TECH-DEBT.md#sd-023).

---

## Context

1. Admission is the **business-rule face**: may this act run. Capability is the **structure fact**: is this organ here. [VISION-0.64](../vision/closed/VISION-0.64.md).  
2. [ADR-035](035-admission-sits-on-capabilities.md) published installed names on `AdmissionSnapshot`. `require_business_admission` still fail-closes only on `may_run_business`.  
3. Dependents (`able`, façades, tests) still treat the ready wall as the organ list. That is the old face as a second membership king.  
4. The two questions must stay two questions. Ready false is not “organ missing.” Organ missing on a ready organism is not a corridor around the wall.  
5. A decorator would hide the gate and hunt `admission` on `self` — the dig 0.66 stopped.

## Decision

### D1 — Two doors, same source

`require_business_admission(source)` stays ready-only.

`require_capability(source, name)` lives beside it. Same coerce. Fail closed if the snapshot is missing or `may_run_business` is false (`AdmissionRefusedError`). Then fail closed if `has_capability(name)` is false (`CapabilityRefusedError`, snapshot + name).

Callers that only need “organism up” keep the first door. Callers that need an organ use the second. The second door always includes the wall.

### D2 — `able` stays a query

Zero-arg `able()` remains `started ∧ may_run_business`. A closure may also read `has_capability`. The install-board type stays `Callable[[], bool]`. No `@able`. No `@require`.

### D3 — No organ argument on the ready door

Do not add `capability=` to `require_business_admission`. Mixing the questions in one signature makes “admission” mean two things and invites every submit path to pass a name.

## Consequences

### Positive

- Submit / CQRS / Assist keep a ready-only oath.  
- Drain-shaped acts can require `work_drain` without digging structure.  
- Tests can freeze membership as `has_capability`, not as `may_run_business`.

### Negative / residual

- Two functions to teach.  
- Host `start_ports.able` is drain-shaped from 0.67.3; wait uses `install_admission_able` (ready + host `_started`).  
- Surfaces speak `capability_refused` from 0.67.4 (REST/MCP 409). Ready-false stays `admission_refused`.  
- Schedule fire (`tick_schedules` / host `tick_work`) uses drain able from 0.67.5.  
- Vitality `work_cycle` drain proofs pin `local.cli` from 0.67.6. Embedded ready is not membership.  
- Journal is DNA + attach hand from 0.67.7. Projections is DNA + attach hand from 0.67.9. Compensation is DNA + attach hand from 0.67.11. Webhook is DNA + attach hand from 0.67.13. Analytics is DNA + attach hand from 0.67.16. Analytics leftover paid 0.67.17 (host slot aliases the install organ; `analytics_enabled` refines that object). Remaining [SD-021](../../TECH-DEBT.md#sd-021) packaging duals. Costume composted: [VISION-0.68](../vision/closed/VISION-0.68.md). Residual [SD-023](../../TECH-DEBT.md#sd-023).

### Forbidden

- Skip ready inside `require_capability`.  
- Decorators on the wall.  
- Definition `requires`.  
- A fake capability named `ready`.

## Alternatives considered

- Optional organ arg on `require_business_admission` — rejected as the default. Same home, but one name for two questions. José may override (VISION lock 1).  
- `require_capability` that does not check ready — rejected. Capability true on a closed organism is a corridor.  
- Decorators — rejected. They hide the published gate.

## Links

- [VISION-0.67](../vision/closed/VISION-0.67.md)  
- [VISION-0.68](../vision/closed/VISION-0.68.md) (**closed**) · [SD-023](../../TECH-DEBT.md#sd-023)  
- [VISION-0.66](../vision/closed/VISION-0.66.md)  
- [VISION-0.64](../vision/closed/VISION-0.64.md)  
- [VISION-ASSEMBLY](../vision/VISION-ASSEMBLY.md)
