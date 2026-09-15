# Appendix — open questions

**Status:** Living. José locks answers.  
Record decisions in ADRs, [principles.md](../principles.md), or glossary when locked.

---

## Structure definition and membership

- Exact schema of membership sections (`plugins`, `products`, `surfaces`, refuse, places) **beyond first cut**?  
- **Locked (2026-08-17):** first unit = **`work_drain`** under a **`capabilities`** section (local only). No no-op prove-out. See [structure-materialize-cut.md](structure-materialize-cut.md).  
- How far does structure definition own bootstrap wire vs host seed still freelancing? (First unit paid: `work_drain` install reads definition `capabilities`.)  
- **Locked (2026-08-17):** packages `palm.core.structure` / `palm.system.structure`. Types `StructureDefinition` / `StructureEngine` / `StructureStatus` / `StructureSeat`. Vision/ADR keep the word assembly.

---

## Engine vs manager (mostly decided — confirm)

- **Intent:** reconciler (engine) in **core**; manager (seat, loop, hands, materialize, resolvers) in **system**.  
- Open: any pure types that must stay system-only? Any manager API surface on the shell beyond admission + structure effects?  
- **Locked (2026-08-20):** admission snapshot publishes **installed** `capabilities` / `has_capability`. [VISION-0.66](../../vision/closed/VISION-0.66.md) · [ADR-035](../../adr/035-admission-sits-on-capabilities.md) **Accepted**.  
- **Locked (2026-08-21, Accepted):** two doors — `require_business_admission` (ready) and `require_capability` (ready then name). No decorators. [VISION-0.67](../../vision/closed/VISION-0.67.md) · [ADR-036](../../adr/036-require-capability.md) **Accepted**. Costume composted: [VISION-0.68](../../vision/closed/VISION-0.68.md) (**closed**). Residual [SD-023](../../../TECH-DEBT.md#sd-023).

---

## Membership source and Palm provider

- When does **membership source** appear on the definition (`local` only until then)?  
- What is a **definition package** (format, signing, version)?  
- Palm provider protocol for structure: which verbs, which home (support vs authority)?  
- Worker spawn: definition **cut** served by support — what is minimal cut?  
- **Cache / replicate** (provide → local store → local materialize): when is it in scope vs Grove/tunnels?

---

## Scale roles (orchestrator / support / worker)

- Confirm intended: thin orchestrator, support serves definitions/membership, worker uses — under structure definition, not freestyle.  
- Is “support serves custom plugins/products/surfaces” only via **provide definition packages**, or also runtime proxy? (Prefer provide + local materialize unless proxy is required.)

---

## Theme 0.63 exit

- **Open (2026-08-17):** stay on **0.63** for this materialize cut, or stamp **0.64** later. Engineering cut does not wait on that stamp. Do not draft a new VISION until José chooses.  
- How deep must **structure manager / materialize** be before José exits 0.63 vs admission-floor + named residual?  
- Is architecture vault fill a gate for exit, or parallel standing work?

---

## Package diagram (next SE step)

- First diagram: package families only, or include `core.structure` / `system.structure` split in v1?

---

## Navigator (queue seed — not locked)

Seed: [VISION-NAVIGATOR](../../vision/VISION-NAVIGATOR.md). José named the seed **2026-08-19**. Not an ADR.

- Kit package name for the presentation adapter (`palm.kits…`)?
- Default operator-guidance definition: catalog tag vs structure/settings seed?
- When (if ever) does definition visibility become a system interface beside admission?
- Surface as a separate OS process vs in-process adapter — first dogfood?
