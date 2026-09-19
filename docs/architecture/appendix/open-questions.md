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

## Navigator (closed 0.69)

Theme: [VISION-0.69](../../vision/closed/VISION-0.69.md) (**closed**). Seed: [VISION-NAVIGATOR](../../vision/VISION-NAVIGATOR.md). ADR: [037](../../adr/037-navigator-invert.md) **Accepted**. José named the seed **2026-08-19**; opened the minor **2026-09-17**; closed **2026-09-17**. Package stamp stays `0.68.0`.

**Locked (José 2026-09-15–16):** operator-guidance **instance stays** attached (focus returns). Entry chooser and definition **visibility** are **principal / user-plane**, not this invert’s floor. Floor: one anonymous outside subject; one process default guidance definition; adapter does not filter the catalog. Fail-closed later = **system interface**, not admission, not adapter. Kit **`palm.kits.present`** (**kit-as-composition:** one object holds `BoundSurface`, walks session + execution). Surfaces stay **in-process**. First adapter = **embedded library surface** (`CompositionProfile.embedded()`). `EmbeddedRuntime` is the engine, not the adapter. **Turn invert:** kit walks; pattern fills `JobInspectable` / `InputCapable`; no pattern `if` in the kit. **Pack:** new wizard definition beside `operator_entry`; same-session sibling; stay `WAITING_FOR_INPUT`; return is `focus`. Session **metadata** key **`guidance_instance_id`**. **Walk writes** through a system interface (floor degenerate; user plane later installs). **Job is session-ignorant** (attach is session-side). **Dashboard model:** chooser shell; session-owned titles; no `WaitInterest` on siblings. **Kit-contributed settings:** present owns `guidance_definition_id` (not core `PalmSettings`). **Stamp caller:** kit asks after attach; `SessionService` writes. **Replace predicate:** kit; attached; definition id equals `guidance_definition_id`. Interface type unnamed.

**Scout harvest (José 2026-09-16):** returned in [VISION-NAVIGATOR](../../vision/VISION-NAVIGATOR.md) §6.1. Turn invert, kit-as-composition, pack, and `guidance_instance_id` locked. Protocol types unnamed.

Homes (kit, kit-as-composition, first adapter, guidance instance, principal seam, turn invert, pack, `guidance_instance_id`, walk writes, job is session-ignorant, dashboard model, kit-contributed settings, stamp caller, replace predicate) are locked. Engine glue shipped: session-side attach (`0.69.2`), spawn without nested park (`0.69.3`), stamp caller (`0.69.5`), kit owns the key (`0.69.8`).

**Still unnamed:** Protocol types, kit handle class, walk-write interface type, env spelling, constructor override. Pattern inspect/input fill (pipeline / DAG). Assist compost is [VISION-SURFACE-DEFLATION](../../vision/VISION-SURFACE-DEFLATION.md).

---

## Authoring (open 0.70)

Theme: [VISION-0.70](../../vision/VISION-0.70.md) (**open**, plan `0.70.0`). Seed: [VISION-AUTHORING](../../vision/VISION-AUTHORING.md). ADR: [038](../../adr/038-authoring-adapter.md) **Proposed**. José named the seed **2026-09-19**; opened the minor **2026-09-19**. Package stamp stays `0.68.0`.

**Locked (José 2026-09-19):** law word **authoring adapter**; floor phenotype **A** (`host.definitions` on `CompositionProfile.embedded()`); hold / land / drive split; Design overlay on fat phenotypes; no `INTENTION_KITS` until a package exists.

**Locked (José 2026-09-19, package):** `palm.kits.authoring`. As-built `0.70.1`: `INSTALLED_KITS`; `land(host)` / `commit(body)` walks `create_flow`.

**Still unnamed:** handle class, Protocol types, authoring pack id, env spelling, whether catalog speak becomes a `palm` provider action. Constructor spelling is as-built `land`; José may rename.
