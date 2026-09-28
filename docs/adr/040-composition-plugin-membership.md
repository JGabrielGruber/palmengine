# ADR-040 — Composition plugin membership (package-install · minimal embed measure)

**Status:** Proposed  
**Date:** 2026-09-21  
**Theme:** [VISION-0.72](../vision/VISION-0.72.md) (**open**)  
**Prior closed:** [VISION-0.71](../vision/closed/VISION-0.71.md) · [ADR-039](039-place-registry-adopt.md) **Accepted**  
**Related:** [ADR-041](041-bundle-start.md) **Proposed** (amends D2, D4, D7) · [ADR-032](032-organism-assembly.md) **Accepted** (organ/place precedent) · [ADR-028](028-system-boot.md) **Accepted** (plugins ≠ planes) · [ADR-019](019-composition-profiles.md) **Accepted** (phenotype) · [ADR-036](036-require-capability.md) **Accepted** (organ require)  
**Map:** [PALM.md](../PALM.md)

José opened theme **0.72** (2026-09-21) after exiting **0.71**. Pack `0.72.0` is vision + docs align + thread close. Package stamp stays `0.68.0`. Accept at theme exit. This ADR records **structural decisions only** — no API sketch, no `ensure_core_plugins` rewrite recipe.

---

## Context

1. [ADR-032](032-organism-assembly.md) / DNA made organ and place membership honest as definition law after load. That precedent holds.  
2. Plugin / package **membership** remains an unpaid dual: process latch co-loads an independent set; latch-ran ≠ composition-owned membership.  
3. José locked **reading A** (2026-09-21): structure enables capabilities **of** packages composition already installed. **Reject B** (structure owns package membership as DNA peer).  
4. Minimal embed is the **measuring point** for the raise — lean host class pressure — not a second vertical and not a vision owner.  
5. [ADR-028](028-system-boot.md) already splits plugins from planes and treats BootMode as order. That continuity must hold; BootMode is not package-membership SoT.

## Decision

### D1 — New minor 0.72

Composition **plugin membership** (package-install vertical), measured on minimal embed, is theme **0.72**. Do not reopen closed place-registry **0.71** as this subject.

### D2 — The profile names the sets the loader installs

**Amended 2026-09-28 by [ADR-041](041-bundle-start.md).** The profile assigned to the bundle names a driver set and a plugin set. The loader installs each once, during bundle start, through the load contract (ADR-041 D4–D6). The kernel owns neither set. It receives bound drivers and a structure seed. Provenance stays with the bundle and records both sets.

The loader is not in the tree yet. Naming this owner is not claiming the body landed.

### D3 — Structure enables capabilities (reading A)

Structure **enables** organs / places / refuse on `StructureDefinition` now; capabilities *of* packages only **after** composition installed them. **Reading A** locked. **Reject B**.

### D4 — Definition SoT after load

StructureDefinition seed→law is the precedent. **Amended 2026-09-28 by [ADR-041](041-bundle-start.md):** the package carrier is the profile's driver set and plugin set (ADR-041 D4), returned as provenance beside the bound drivers and never passed to the kernel. The assembly definition stays the system's. Still no boot YAML DSL and no plugins in DNA.

### D5 — Minimal embed = measuring point

Minimal embed pressure is the fail-closed measuring altitude (O1–O5 in [VISION-0.72](../vision/VISION-0.72.md)). It is **not** a second vertical. Measure is **not pass** at theme open.

### D6 — Plugins ≠ planes; BootMode ≠ membership SoT

[ADR-028](028-system-boot.md) D5 continuity: planes are not plugins. BootMode / boot schedule chooses **order**, not package-membership law.

### D7 — CompositionProfile phenotype honesty

The profile still names services and surfaces ([ADR-019](019-composition-profiles.md)). **Amended 2026-09-28 by [ADR-041](041-bundle-start.md) D11:** surface code stays in the bundle; service code lives on `src/services`. Organ names are **not** composition members after DNA ([ADR-028](028-system-boot.md) D4 succession honesty).

### D8 — Stamp

Package version stays `0.68.0` until José cuts an embedded release.

### D9 — Accept at theme exit

Status stays **Proposed** until José exits **0.72** and accepts this ADR.

## Explicit non-decisions

This ADR does **not** decide:

- `only=` / phenotype flags as membership landing  
- Grove / tunnels as this theme  
- API-as-design / Root latch rewrite / `ensure_core_plugins` recipe as `0.72.0` default  
- Reading B / DNA owns latch  
- Measure pass (O1–O5 green) at open or in `0.72.0`

## Consequences

- STATUS / PALM / VISION speech name the raise and the measuring bar without claiming green.  
- As-built observations (call path, tuples, controls that are not membership) live in [VISION-0.72](../vision/VISION-0.72.md) §2.3. This ADR does not repeat them.  
- Problem sites live in [VISION-0.72](../vision/VISION-0.72.md) §12. `0.72.2` builds the composition record (P5–P8). `0.72.3` puts package names on that record and the install stroke walks them (P1–P4, P9, P12–P14). `0.72.4` names transforms on that record and the host imports the service tuple (P10, P11). `0.72.5` removes the kernel install phase. `0.72.6` passes bound drivers into `start`. The kernel does not import or default a storage or a runner. This ADR does not add an API recipe. Status stays **Proposed**.  
- The package carrier decision now lives in [ADR-041](041-bundle-start.md) **Proposed**. This ADR does not claim the loader has landed.  
- Later `0.72.x` may populate composition-owned install under José sequence — outside this ADR’s default for `0.72.0`.  
- DNA organ/place green and phenotype theater remain fake-green if cited as membership proof.

## Status

**Proposed** until José exits 0.72 and accepts this ADR. D2, D4, and D7 were amended 2026-09-28 by [ADR-041](041-bundle-start.md), which stays **Proposed** with this one.
