# VISION 0.72 — Composition plugin membership (minimal embed measure)

**Status:** 📋 **Theme open** (José 2026-09-21). Pack `0.72.0` landed. Slice **`0.72.1`** landed (problem register + forward order). Slice **`0.72.2`** landed (composition record). Slice **`0.72.3`** landed (package set + install stroke). Next expected: **`0.72.4`** second menus. Package stamp stays `0.68.0` (no embedded release). Measure **not pass**.  
**Language:** ASD-STE100 Simplified Technical English.  
**Map:** [PALM.md](../PALM.md) — read first.  
**ADR:** [040-composition-plugin-membership.md](../adr/040-composition-plugin-membership.md) **Proposed**.  
**Theme law:** [VERSIONING.md](../VERSIONING.md) (floor · growth · exit judgment).  
**Prior closed:** [VISION-0.71](closed/VISION-0.71.md) Place registry · [ADR-039](../adr/039-place-registry-adopt.md) **Accepted**.  
**Related:** [VISION-ASSEMBLY](VISION-ASSEMBLY.md) · [ADR-032](../adr/032-organism-assembly.md) **Accepted** (organ/place precedent) · [ADR-028](../adr/028-system-boot.md) **Accepted** (plugins ≠ planes) · [ADR-019](../adr/019-composition-profiles.md) **Accepted** (phenotype).  
**Needs later:** [VISION-TINY-LLM](VISION-TINY-LLM.md) · [VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md) · [VISION-TUNNELS](VISION-TUNNELS.md).  
**North star:** [VISION-GROVE](VISION-GROVE.md) — **not** this theme.

Teaching name (once): **composition plugin membership** (package-install).  
Measuring point: **minimal embed pressure** — fail-closed verification altitude for that vertical on the lean host class.

**Open:** José opened **0.72** (2026-09-21) after exiting **0.71**. Floor for `0.72.0` is the plan (vision + ADR + STATUS/PALM honesty). O1–O5 named as bar — **not green**. Do not implement membership as the `0.72.0` default.

---

## 1. Goal

Palm already tells the truth about structure when the subject is **organs and places**: after load, definition is law; seed chooses; admission fails closed ([VISION-ASSEMBLY](VISION-ASSEMBLY.md) · [ADR-032](../adr/032-organism-assembly.md)).

The unpaid sibling is **plugin membership**.

| today | cost |
|-------|------|
| process latch co-loads a fat independent set at host start | hard edges few; most cost = **co-membership without composition ownership** |
| dual truth | latch ran ≠ membership owned |
| fake-green paths | DNA organs/places healthy · phenotype / `only=` thin · boot schedule · mobile demo — none of these are composition ownership |

This is **not** “DNA unfinished.” DNA did its job for organs/places. Different **kind**, same taste: **membership owned by composition / definition law**, not unpaid latch soup.

### 1.1 Ambition and floor

| Concept | Meaning |
|---------|---------|
| **Floor (`0.72.0`)** | Vision + ADR Proposed + STATUS/PALM honesty; O1–O5 named as fail-closed bar (**not** green). |
| **Growth line** | Later `0.72.x` may populate composition-owned install (José sequences) — **not** default `0.72.0`. |
| **Exit** | **José’s** judgment when the home is proper and residual is honest. ADR-040 accept at theme exit. |

**Who decides:** José Gabriel Gruber — [VERSIONING.md](../VERSIONING.md) *Who decides*.

---

## 2. Floor (`0.72.0`)

The theme is **real as a plan** when:

1. This VISION is **open** with floor / growth / non-goals / principles / slice guide named.  
2. [ADR-040](../adr/040-composition-plugin-membership.md) is **Proposed** (structural decisions only — no API recipe as the design).  
3. [STATUS.md](../../STATUS.md) points at **0.72** as present; agent resume → this VISION → ADR-040; slice **`0.72.0`** = plan landed.  
4. [PALM.md](../PALM.md) has one open-theme pointer + kind honesty (composition-owned package membership is the **0.72 raise**; latch dual unpaid today).  
5. Measure bar **O1–O5** is named here as **not pass** — do not claim green from DNA, suite slice, phenotype, or latch-ran.

**Floor function:** that raise in speech and docs. Not Root latch rewrite. Not selective load-set bodies. Not Grove.

### 2.1 Kind split · reading A (José lock 2026-09-21)

| lane | verb | owns |
|------|------|------|
| **composition** | **installs** | local packages / plugin families / package membership under composition/boot |
| **structure** | **enables** | capabilities — organs / places / refuse on `StructureDefinition` (DNA) now; capabilities *of* packages only after composition installed them |
| phenotype | services / surfaces | composition-side, separate from package latch and organ capabilities |

**Reading A (lock):** structure enables capabilities **of** packages composition already installed.  
**Reject B:** structure owns package membership as peer of DNA organs.

Definition **SoT after load** — StructureDefinition precedent (seed→law); **package carrier unpaid** under this raise.

### 2.2 Success observables (fail-closed bar — **not pass** @ open)

| # | observable | fail-closed reading |
|---|------------|---------------------|
| O1 | **Membership provenance** | For a minimal embed host start, plugin load-set explainable as composition/definition-owned — not “whatever `ensure_core_plugins` co-loaded.” |
| O2 | **Soup absence** | Independent-set co-membership hard edges do not force unpaid dual for that host class. |
| O3 | **Useful path** | ≥1 admitted useful work path under that owned set (definition → job path / resource speak as the phenotype allows). |
| O4 | **No dual king** | Profile/mode/env remain **seed** choosers; boot schedule ≠ membership law. |
| O5 | **Kind split** | Reports keep labels apart: organ capabilities · places · composition services/surfaces · plugin latch co-membership · catalog name-resolve. Collapsing words = fake-green. |

**Also invariant:** organ/place DNA green does **not** count as plugin-membership green; phenotype flags / `only=` do **not** count as composition ownership.

**As-built honesty:** The bar is named. Measure is **not pass**. Concrete facts are in §2.3. Do not claim green.

### 2.3 As-built observations (code)

These rows are facts in the tree. They are not decisions. [ADR-040](../adr/040-composition-plugin-membership.md) does not repeat them. A later change to this path must update this section.

**Call path.** Two callers, one stroke. The stroke takes package names from a composition record (`0.72.3`).

| Step | Code | What it decides |
|------|------|-----------------|
| First call | `host.kernel.bootstrap` → `PalmKernel.bootstrap(composition)` → `ensure_plugins` | Installs that composition's package names. A kernel call with no composition uses the `all_in_one` record |
| Alias | `palm.app.bootstrap.ensure_plugins` | Reads the profile and calls the stroke |
| Schedule seat | `system.plugins.ensure` → `phase_plugins.run` | Reads `composition_packages` from phase options and calls the stroke. No key: the phase installs nothing |
| Stroke | `palm.common.plugins.ensure_core_plugins` | No process flag. Imports `palm.common.transforms` (that package calls its `autoload` at import), then `autoload(names)` for kits, patterns, providers, runners, and storages |

A later call imports names that are not yet imported. It does not unload names already imported.

**What the stroke walks.** The names on the composition record. Every saved record names the same set in this slice.

| Family | Names on each saved record | Catalog (the walk does not close over this) |
|--------|----------------------------|-----------------------------------------------|
| Kits | `present`, `authoring` | `INSTALLED_KITS` also lists `server`. No record names `server` |
| Patterns | `dag`, `parallel`, `pipeline`, `wizard` | `INSTALLED_PATTERNS` |
| Providers | `rest`, `palm`, `kv`, `file`, `authoring` | `INSTALLED_PROVIDERS` |
| Runners | `local`, `host`, `neonroot` | `INSTALLED_RUNNERS`. The workload plane binds classes already on the registry. `host` starts disabled unless `workload_host_enabled` |
| Storages | `memory`, `filesystem` | `CORE_STORAGES` and `OPTIONAL_STORAGES` stay catalogs. `postgres` and `mongodb` are not on the records. `StorageFactory` still loads them on demand |
| Transforms | import of `palm.common.transforms` | `INSTALLED_TRANSFORMS` is still a second name list (P11, `0.72.4`) |
| Services | the stroke does not call `services.autoload` | `INSTALLED_SERVICES` stays beside `HostServiceRegistry` (P10, `0.72.4`) |

**Controls.**

| Control | What it gates |
|---------|----------------|
| Saved composition records | Each record has package name fields (`0.72.3`). Phenotype fields are unchanged. `embedded` services stay `inspect`, `session`, `definitions`, `execution`. Surfaces empty. Capabilities empty. Package names match the other records |
| `BootMode` | Stores the profile built from a record. It does not choose packages by itself |
| Phase options | `composition_packages` is the set the host passed. The phase does not invent a set |
| Kit `server` | On `INSTALLED_KITS`. Off every saved record. The server runtime imports it when that surface starts |
| Runner `host` | On the record, so the stroke imports it. The engine binds the registered class. OFF is `workload_host_enabled` |
| Storage names | The record names `memory` and `filesystem`. `include_optional` is gone |

**O-reading from these facts.**

| # | Observation |
|---|-------------|
| O1 | The load-set is the record's package names. The stroke walks those names |
| O2 | Every saved record names the same set. `embedded` drops no package. Co-membership of that set remains |
| O3 | There is an owned set. It is the same set on every record. A useful path under a smaller embed set is not shown |
| O4 | The host passes the record's names. The phase reads them. `BootMode` stays order |
| O5 | Services and surfaces stay phenotype fields. Package names are separate fields on the same record. Organs stay on `StructureDefinition`. Runner OFF is an engine flag on a class the record installed |

Measure stays **not pass**. A separate package carrier (boot YAML, or a fold into DNA) stays unpaid ([ADR-040](../adr/040-composition-plugin-membership.md) D4).

---

## 3. Growth

Later `0.72.x` (José sequences) may populate composition-owned package install, reading-A enable-of-installed bodies, latch thinness, package SoT carrier shape. Those are **growth**, not the `0.72.0` floor.

Do not invent carriers or suites in this plan pack.

---

## 4. Why now

0.71 closed the place-registry adopt remainder. The unpaid dual on plugin membership is the next honest raise. Minimal embed is the measuring host class — not a second vertical and not a vision owner (desk / mobile may illustrate pressure only).

---

## 5. Non-goals

| Non-goal | Why |
|----------|-----|
| **`only=` / phenotype flags as the landing** | thin path ≠ composition ownership |
| **Grove / tunnels season** | wrong season; north star stays queue |
| **Reading B** | José rejected — structure does not own package membership as DNA peer |
| **DNA owns latch** | collapses install vs enable |
| **BootMode as membership SoT** | schedule/mode ≠ membership law ([ADR-028](../adr/028-system-boot.md)) |
| **Mobile owns theme** | illustrate pressure only |
| **Measure pass in `0.72.0`** | O1–O5 unpaid; claiming pass = fake-green |
| **Root implement as `0.72.0` default** | raise-vertical + docs first; implement only if José expands |
| **API-as-design / ensure_core_plugins rewrite recipe** | structural decisions in ADR; no API sketch as “the” design |
| **Tiny LLM / surface deflation as this raise** | later seeds |

---

## 6. Principles

1. **Kind split** — composition **installs**; structure **enables**; do not cross-wire.  
2. **Reading A** — enable capabilities *of* already-installed packages; reject B.  
3. **Definition SoT after load** — StructureDefinition precedent; package carrier unpaid.  
4. **Plugins ≠ planes** — [ADR-028](../adr/028-system-boot.md) D5 continuity.  
5. **Minimal embed = measuring point** — not a second vertical.  
6. **Services/surfaces** stay composition phenotype ([ADR-019](../adr/019-composition-profiles.md)); organ names are not composition members after DNA ([ADR-028](../adr/028-system-boot.md) D4 succession honesty).  
7. **STE** for theme docs. Spoken words are teaching only.  
8. **José exits** — checklist theater does not close the season.

---

## 7. Locks (José 2026-09-21)

| Locked | Speech |
|--------|--------|
| Theme | **0.72** composition plugin membership (package-install) |
| Measuring point | minimal embed pressure |
| Reading | **A** — reject **B** |
| Pack `0.72.0` | vision write + docs align + close threads that block a clean open |
| Stamp | stays `0.68.0` until José cuts a release |
| Measure | **not pass** at theme open |

---

## 8. Slice guide (ordered intent, not a sealed contract)

| Slice | Intent | Status |
|-------|--------|--------|
| **0.72.0** | Plan: VISION, ADR Proposed, STATUS, PALM pointer / kind honesty; O1–O5 named **not pass** | **landed** |
| **0.72.1** | Problem register (§12) and this forward order. No membership implement. No profile rewrite. | **landed** |
| **0.72.2** | Composition record. The host builds `CompositionProfile` from data. Preset methods become saved records. `ApplicationHost.__init__`, `composition_profile_from_settings`, and `BootMode` stop calling those methods (P5–P8). | **landed** |
| **0.72.3** | Package names on that record (P9), then one install stroke. `autoload` walks the set. Latch callers use the stroke (P1–P4). `CORE_KITS`, runner `host` always-import, and `include_optional` stop being the law in this same slice (P12–P14). | **landed** |
| **0.72.4** | Second menus after the record is how a set is named: `services.autoload` (P10) and `INSTALLED_TRANSFORMS` (P11). Does not block the embed measure. | **expected** |

Order is the dependency: `0.72.3` reads the record `0.72.2` builds. `0.72.4` waits on that. One slice is one law and its call sites. Spine stays green (job path, wait, session). `just check` covers the modes that slice declares. A preset the slice does not declare may break. Measure stays **not pass** until a later prove-it. Do not invent fake slices as landed. Do not solve a §12 row inside `0.72.1`.

---

## 9. Debt budget

| Pay or leave | Note |
|--------------|------|
| `composition-plugin-membership` unpaid raise | **Name** in speech (this theme). No new debt id. Implement bodies = later `0.72.x` under José. |
| Package SoT carrier shape | **Leave** unpaid (StructureDefinition taste; carrier invent forbidden here). |
| O1–O5 measure suite | **Leave** named bar; suite not invented; **not pass**. |
| Grove · tunnels · Tiny-LLM · surface | **Leave** on later seeds. |
| 0.71 named place leftovers | **Leave** on closed [VISION-0.71](closed/VISION-0.71.md) §11. |

---

## 10. Related (cite, do not extend)

| Cite | Role |
|------|------|
| [VISION-ASSEMBLY](VISION-ASSEMBLY.md) · [ADR-032](../adr/032-organism-assembly.md) | organ/place seed→law **precedent** — not package latch |
| [ADR-028](../adr/028-system-boot.md) | plugins ≠ planes; BootMode = order ≠ package SoT; D4 organ succession honesty |
| [ADR-019](../adr/019-composition-profiles.md) | presets / phenotype — not package install king |
| [ADR-036](../adr/036-require-capability.md) | organ `require_capability` stays structure |
| [VISION-0.71](closed/VISION-0.71.md) · [ADR-039](../adr/039-place-registry-adopt.md) | prior closed · Accepted |

---

## 11. Residual (open)

Theme stays **open**. Pack `0.72.0` is plan landed. Measure **not pass**. Membership implement unpaid. Package carrier unpaid. Named O1–O5 bar holds as fail-closed observables for later slices — do not claim green.

| Residual | Truth |
|----------|-------|
| Unpaid latch dual / composition-owned install | Raise named; bodies deferred to José-sequenced `0.72.x`. |
| Package membership data carrier | Unpaid. No boot YAML DSL. No fold into DNA. |
| O1–O5 | Bar named; **not pass** @ open. |
| Reading A populate (enable-of-installed) | After composition owns install — later growth. |
| Problem register | **Landed** as `0.72.1` (§12). Forward order is §8. |
| Composition record | **Landed** as `0.72.2`. The host builds `CompositionProfile` from saved records. Preset methods are not the path. |
| Package names + install stroke | **Landed** as `0.72.3`. Each record names kits, patterns, providers, runners, and storages. The stroke walks those names. Every saved record names the same set. `CORE_KITS` and `include_optional` are gone. Runner `host` imports when the record names it. |
| Deployment seed names a record | When there is no `BootMode` and no `composition` argument, `server`, `worker`, and `cli` still take their record name from `boot_mode_name_for_deployment`. Structure seed uses that same name. Removing the name would load a record the definition refuses. |

---

## 12. Problem register (`0.72.1`)

A mark answers one question: does this block belong to theme **0.72**? The register keeps the sites that do, so later work changes that law. A workaround around an unnamed site is out of this slice. A row names a site and the problem. It does not choose a fix. O1–O5 stay the measure bar (§2.2). Facts of the current stroke stay in §2.3.

**Mark:** José selects a block. Judge fit before adding a row.

| Fit | Action |
|-----|--------|
| **In theme** | The block is part of the membership law (who names the package set, or who builds the composition record that will name it). Add a `P` row only when no existing row already owns that law. Otherwise cite the block on that row. |
| **Same law** | Symptom of a named row. Do not add an id. |
| **Not this theme** | Leave it. One sentence on why it stays out, if the mark was easy to confuse with membership. |
| **Workaround** | Do not write it as a goal. A flag, a thinner tuple, or a preset method that hides the law is not a fit. |

Rows that stay **named** are not implemented. **`0.72.2`** paid P5–P8: those sites build `CompositionProfile` from a saved record. They do not call a preset method. **`0.72.3`** paid P1–P4, P9, and P12–P14: the record names packages, and the install stroke walks that set. P10 and P11 stay named (`0.72.4`).

**Already holds (do not file as a problem):** `HostServiceRegistry.build_all(only=composition.services)` reads the service tuple once a `CompositionProfile` exists. `DeploymentProfile.from_roles` builds a deployment record from a name set. `BootMode` still calls deployment presets. That axis is not this record.

| Id | Site | Problem | Status |
|----|------|---------|--------|
| P1 | `palm.common.plugins.ensure_core_plugins` | Process flag `_loaded` keeps the first package set. The function takes no composition record. | **packages** (`0.72.3`) |
| P2 | `palm.system.runtime.phase_plugins.run` | `system.plugins.ensure` discards `BootContext` and phase options, then calls the latch. | **packages** (`0.72.3`) |
| P3 | `PalmKernel.bootstrap` → `ensure_plugins` | First caller of the latch. It runs before any composition record is applied to packages. | **packages** (`0.72.3`) |
| P4 | `autoload` in `palm.patterns`, `palm.providers`, `palm.runners`, `palm.kits`, `palm.storages` | Each walk closes over a module tuple (`INSTALLED_*` or `CORE_*`). The tuple is the membership law. | **packages** (`0.72.3`) |
| P5 | `CompositionProfile` classmethods in `palm.app.host.composition` | `embedded`, `server`, `worker`, `cli`, `mcp`, and `all_in_one` were the host law. The dataclass constructor was not the host path. | **record** (`0.72.2`) |
| P6 | `ApplicationHost.__init__` else branch | With no `composition` argument and no `BootMode`, the branch called `CompositionProfile.server`, `worker`, or `cli`. | **record** (`0.72.2`) |
| P7 | `composition_profile_from_settings` | Started from `CompositionProfile.all_in_one()` and replaced capabilities only. | **record** (`0.72.2`) |
| P8 | `BootMode` classmethods in `palm.app.host.boot.modes` | Each mode called a composition preset. Third hard-coded menu of those methods. | **record** (`0.72.2`) |
| P9 | `CompositionProfile` fields | The record has `services`, `surfaces`, and `capabilities`. It has no package names. The saved `embedded` record cannot steer `autoload`. | **packages** (`0.72.3`) |
| P10 | `palm.services._apps.autoload` | No caller. `INSTALLED_SERVICES` is a menu beside `HostServiceRegistry`. | named |
| P11 | `palm.common.transforms.autoload` | The stroke is `register_builtin_rules()`. `INSTALLED_TRANSFORMS` is a second hard-coded name list. | named |
| P12 | `CORE_KITS` in `palm.kits._apps` | `server` is on `INSTALLED_KITS` and off `CORE_KITS` by a constant in that module. Not a composition record. | **packages** (`0.72.3`) |
| P13 | `INSTALLED_RUNNERS` entry `host` | `autoload` imports the package and registers `HostWorkloadRuntime`. "Default OFF" is `workload_host_enabled` in `phase_engines`. | **packages** (`0.72.3`) |
| P14 | `palm.storages.autoload` | The function accepts `include_optional`. The latch calls it with no argument, so `postgres` and `mongodb` stay out by that default. | **packages** (`0.72.3`) |

`0.72.2` build path: `COMPOSITION_RECORDS` holds the six shapes. `CompositionProfile.from_record` and `composition_profile_from_name` build the profile. `composition_profile_from_settings` copies services and surfaces from the `all_in_one` record and writes capabilities from settings. `BootMode` stores that built profile. With no `BootMode` and no `composition` argument, `server`, `worker`, and `cli` still select the record by `boot_mode_name_for_deployment` (§11). `all_in_one` uses the settings build.

`0.72.3` adds package name fields on that record and on the profile. The settings build copies those fields from the `all_in_one` record. `ensure_core_plugins` walks the names. `autoload` takes the names. The host bootstrap passes the host composition. The system phase reads `composition_packages`. Every saved record names the same package set. Measure stays **not pass**.
