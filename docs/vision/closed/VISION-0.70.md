# VISION 0.70 — Authoring

**Status:** ✅ **Theme closed** (José 2026-09-19). Floor proven `0.70.1`–`0.70.2`. Last growth `0.70.7`. Package stamp stays `0.68.0` (no embedded release).  
**Language:** ASD-STE100 Simplified Technical English.  
**Map:** [PALM.md](../../PALM.md) — read first.  
**ADR:** [038-authoring-adapter.md](../../adr/038-authoring-adapter.md) **Accepted**.  
**Seed (law):** [VISION-AUTHORING](../VISION-AUTHORING.md).  
**Migration:** [MIGRATION-0.70](../../migrations/MIGRATION-0.70.md).  
**Theme law:** [VERSIONING.md](../../VERSIONING.md) (floor · growth · exit judgment).  
**Prior closed:** [VISION-0.69](VISION-0.69.md) Navigator · [ADR-037](../../adr/037-navigator-invert.md) **Accepted**.  
**Not this theme:** [VISION-SURFACE-DEFLATION](../VISION-SURFACE-DEFLATION.md) · [VISION-TINY-LLM](../VISION-TINY-LLM.md) · [VISION-0.56](../VISION-0.56.md) · [VISION-TUNNELS](../VISION-TUNNELS.md).  
**North star:** [VISION-GROVE](../VISION-GROVE.md).

Teaching name (once): **control kit**.  
Law: **authoring adapter** + authoring **definition pack**.

**Exit:** José closed the theme (2026-09-19). Floor held: one embedded land without Assist or Design. ADR-038 **Accepted**. Residual named in §11. No open minor. Create-only stays honest. Names stay working. Invert `LocalPalmInvoker` before any `palm` catalog action.

---

## 1. Goal

[VISION-NAVIGATOR](../VISION-NAVIGATOR.md) inverted consume. Present walks session + execution. Consume has nothing honest to walk until a shape **lands** in the catalog.

Today land is Python in `examples/` plus `DesignService` on fat compositions. Embedded has **definitions** and **no** Design.

| Piece | Role |
|-------|------|
| **Authoring adapter** | Geometry. One host-held object. Walks `host.definitions` (draft / validate / commit). |
| **Authoring definition pack** | Purpose. Catalog wizard present may start. A leaf speaks the adapter door. |
| **Hold** | Already exists: `ApplicationHost` + `CompositionProfile`. Not a kit. |
| **Drive** | Already exists: `palm.kits.present`. Do not grow land verbs on present. |

**Success (floor):**

- Phenotype `CompositionProfile.embedded()`. No Assist. No Design seat.  
- The adapter one-shot commits a `FlowDefinition` through `host.definitions`.  
- Present starts that definition.  
- If that loop is harder than `save_flow` in Python, the adapter is costume.

### 1.1 Ambition and floor

| Concept | Meaning |
|---------|---------|
| **Floor** | One embedded land proves the adapter (see §2). |
| **Growth line** | Theme may grow while José keeps it open — pack, thin apply, snapshot speak, kit install. |
| **Exit** | **José’s** judgment when the home is proper and residual is honest. |

**Who decides:** José Gabriel Gruber — [VERSIONING.md](../../VERSIONING.md) *Who decides*.

---

## 2. Floor

The land walk is **real** when tests on `CompositionProfile.embedded()` (no Assist, no Design) prove this chain:

1. Host holds the authoring adapter.  
2. Adapter walks `host.definitions` (one-shot commit is enough).  
3. A `FlowDefinition` exists in the catalog.  
4. Present starts that definition on the same host.

**Floor function:** that land. Not MCP. Not CLI. Not Portal. Not Flutter. Not YAML-in-core. Not Design propose/impact. Not farm-shaped numbers.

**As-built `0.70.1`:** package `palm.kits.authoring` in `INSTALLED_KITS`. `land(host)` holds `host.definitions`. `commit(body)` walks `create_flow`. Tests: `tests/test_authoring_kit_0_70_1.py` on `ApplicationHost.for_mode("test")` (embedded; no Assist; no Design). Handle class unnamed.

**As-built `0.70.2`:** `palm.kits.present` starts the committed definition by catalog id (`start(..., by_id=True)`). Same host. No land verbs on present. Existing consume doors. Tests: `tests/test_authoring_present_start_0_70_2.py`.

**As-built `0.70.3`:** authoring pack wizard. Pack id unnamed. Working catalog name `authoring-pack`. Land via adapter; present starts it; waits on shape. Tests: `tests/test_authoring_pack_0_70_3.py`.

**As-built `0.70.4`:** thin apply. Working catalog names `authoring-apply` and `authoring-snapshot` (José may rename). Pytest `land(host).commit` still publishes the apply flow (job leaf is `0.70.5`). Snapshot resource lands via `host.definitions.create_resource` (resource verb is `0.70.6`). Present starts the apply by catalog id. Wizard resource step writes file JSON data; confirm waits; present submit completes the apply. Pack stays waiting. Tests: `tests/test_authoring_apply_snapshot_0_70_4.py`.

**As-built `0.70.5`:** pack submit is a `FlowDefinition` mapping. Resource `authoring-commit` (provider working name `authoring`) walks `bound().commit`. Catalog revision exists. Pytest is not that leaf. Present starts the new id. Tests: `tests/test_authoring_job_leaf_0_70_5.py`. Hole named [SD-025](../../../TECH-DEBT.md#sd-025).

**As-built `0.70.6`:** `commit(body)` walks catalog `kind` (`flow` → `create_flow`, `resource` → `create_resource`). Pack submit of a `ResourceDefinition` mapping lands the snapshot. Pytest is not that leaf. Present starts apply; file data is still the file provider. Tests: `tests/test_authoring_resource_land_0_70_6.py`. `0.70.4` still uses `create_resource` as a library bypass.

**As-built `0.70.7`:** `bound()` takes definitions from the started host on the bound runtime (same door file/kv use). `land(host)` is library-only. Tests: `tests/test_authoring_bind_ambient_0_70_7.py`.

---

## 3. Growth

While the theme stays open, slices may:

- ✅ Install the kit (`INSTALLED_KITS`) — `0.70.1`.  
- ✅ Add the authoring pack as a wizard present can start — `0.70.3` (as-built `authoring-pack`; pack id unnamed).  
- ✅ Let a leaf commit a **thin apply flow** — `0.70.4` (as-built `authoring-apply`).  
- ✅ Let that apply flow speak a snapshot resource (file is enough) and wait when unsure — `0.70.4` (`authoring-snapshot`).  
- ✅ Drive the apply flow with present (full dogfood loop from the seed) — `0.70.4`.  
- ✅ Let a **leaf of the pack run** speak the adapter — `0.70.5` (working provider `authoring`; [SD-025](../../../TECH-DEBT.md#sd-025)).  
- ✅ Let that leaf land a **resource** through the same `commit` door — `0.70.6`.  
- ✅ Let `bound()` walk the started host, not a `land()` stash — `0.70.7`.  
- Name handle / Protocol / pack id / provider when José locks them.  
- Decide whether catalog speak becomes a `palm` provider action or stays adapter-only.

**Not floor:** env spelling. Constructor override. Design commit on fat phenotypes. Shallow draft language (YAML / diagram) as compile source.

---

## 4. Why now

1. **0.69** closed consume. Residual Assist stays until surface deflation.  
2. Seed locks in [VISION-AUTHORING](../VISION-AUTHORING.md) are complete (law word, floor **A**, Design overlay).  
3. José named **0.70** (2026-09-19).  
4. Extra present surfaces without land are transports of an empty walk.

**Thesis:** Purpose is a definition. The adapter only lands. Present only drives.

---

## 5. Non-goals (other seeds — not forever bans)

| Out of this theme’s *subject* | Home |
|-------------------------------|------|
| Compost Assist / CLI forest / Portal | [VISION-SURFACE-DEFLATION](../VISION-SURFACE-DEFLATION.md) |
| Tiny model body / typed speak | [VISION-TINY-LLM](../VISION-TINY-LLM.md) |
| Workload place book | [VISION-0.56](../VISION-0.56.md) |
| Tunnels / Grove | [VISION-TUNNELS](../VISION-TUNNELS.md) · [VISION-GROVE](../VISION-GROVE.md) |
| Design propose → impact → migrate | [ADR-008](../../adr/008-design-service.md) on fat phenotypes |
| Workspace / Flutter / edge capture | Farm OS product later — not this adapter |
| Host wizard-named flats | [SD-024](../../../TECH-DEBT.md#sd-024) — do not pay as Authoring |
| 0.68 leftover duals | [SD-023](../../../TECH-DEBT.md#sd-023) |

**Forbidden always (layer law):**

- A `ControlService` / `AuthoringService` / `DesignKit` / `GatewayService` product domain.  
- Land verbs on `palm.kits.present` (`draft` / `commit` / catalog menu).  
- `from palm.core import Sequence` (or public BT factory) as the authoring product.  
- YAML parser as this theme’s floor.  
- Require Design on `embedded()`.  
- Put a name on `INTENTION_KITS` before a package exists.  
- New MCP / CLI / Portal / Flutter surfaces for present or for authoring.  
- Treat a resource snapshot (rules-as-data) as a definition revision.  
- Hot-reload Drive as catalog truth.

---

## 6. Principles

Bind to [PALM.md](../../PALM.md), [VISION-AUTHORING](../VISION-AUTHORING.md), [ADR-037](../../adr/037-navigator-invert.md), and [ADR-008](../../adr/008-design-service.md).

1. **Hold / land / drive stay split.** Host holds. Adapter lands. Present drives.  
2. **Kit-as-composition.** Copy present *law*, not present verbs. One library object. Host holds it. Walks existing doors.  
3. **Floor phenotype A.** `CompositionProfile.embedded()`: inspect, session, definitions, execution.  
4. **Design is overlay.** Fat phenotypes keep `DesignService`. Embedded must not pretend the seat exists.  
5. **Purpose is a definition.** The pack is catalog work. The adapter is geometry.  
6. **Catalog truth** stays `FlowDefinition` / `ResourceDefinition`.  
7. **Body law.** Draft is control flow and speak contracts. Thresholds and books are snapshot rows.  
8. **STE** for theme docs. Spoken words are teaching only ([VISION-AUTHORING](../VISION-AUTHORING.md) §2).  
9. **Theme exit is José’s judgment** when the home is proper.

**Spirit:** Do not grow a second land spine. Use `host.definitions`.

---

## 7. Locks (carried from the seed)

José locked these on **2026-09-19**. Detail: [VISION-AUTHORING](../VISION-AUTHORING.md).

| Cut | Law |
|-----|-----|
| **Law word** | **Authoring adapter** (not control kit). |
| **Floor phenotype** | **A** — walk `host.definitions` on `embedded()`. |
| **Hold** | `CompositionProfile` + `ApplicationHost`. Not a kit. |
| **Drive** | `palm.kits.present`. No land verbs. |
| **Land** | Adapter + authoring definition pack. |
| **Design** | Overlay on fat phenotypes. Not the embedded floor. |
| **INTENTION_KITS** | Empty until a real package exists. |
| **Rules-as-data** | Resource snapshot. Not this adapter. |

---

## 8. Slice guide (ordered intent, not a sealed contract)

| Slice | Intent |
|-------|--------|
| **0.70.0** | Plan. This file. ADR **Proposed**. STATUS. |
| **0.70.1** | ✅ Adapter `palm.kits.authoring` walks `host.definitions` (one-shot `commit`). |
| **0.70.2** | ✅ Present starts the committed definition (remaining floor). |
| **0.70.3** | ✅ Authoring pack — wizard present can start. Pack id unnamed; as-built `authoring-pack`. |
| **0.70.4** | ✅ Thin apply speaks a file snapshot; waits when unsure; present drives. |
| **0.70.5** | ✅ Pack job leaf commits the submitted shape via adapter (resource walks `bound().commit`). |
| **0.70.6** | ✅ `commit` lands `kind: resource`; pack leaf publishes the snapshot; present drives apply. |
| **0.70.7** | ✅ `bound()` walks the started host. `land(host)` is library-only. |

**Named later (not this pass — not QA in 0.70.1):**

| Residual | Home |
|----------|------|
| Handle class / Protocol types | José locks when the door is tired of `_Authoring` |
| Env spelling / constructor override | `land(host)` is as-built; José may rename |
| Provider `create_flow` hole | Adapter door until José locks a `palm` action. Job leaf uses resource `authoring-commit` ([SD-025](../../../TECH-DEBT.md#sd-025)) |
| Adapter resource commit | ✅ `0.70.6` `commit` walks `kind: resource`. `0.70.4` test still calls `create_resource` |
| Provider name `authoring` | Duals the kit package. Working name. José may rename |
| Pack id lock | As-built `authoring-pack`; unnamed until José locks |
| Fat phenotypes: Design commit vs `definitions` write | [ADR-008](../../adr/008-design-service.md) overlay; not embedded floor |
| Shallow draft language (YAML / diagram) | Not a parser theme to have an adapter |

This table is **not** a kill contract. Residual after exit is §11.

---

## 9. Open (not locked)

These remain questions. They are not architecture law.

- Package name under `palm.kits.*` — **locked** `palm.kits.authoring` (José 2026-09-19).  
- Handle class, Protocol types, env spelling. Library door as-built `land(host)` (`0.70.1`); José may rename.  
- Authoring pack id (`author` is spoken only until locked).  
- Whether catalog speak becomes a `palm` provider action or stays adapter-only.  
- When a shallow draft language compiles into `FlowDefinition`.  
- When fat phenotypes must use Design commit instead of `definitions` write.

---

## 10. Related debt

| ID / seed | Role |
|-----------|------|
| [VISION-NAVIGATOR](../VISION-NAVIGATOR.md) · [ADR-037](../../adr/037-navigator-invert.md) | Consume walk — do not steal it |
| [ADR-008](../../adr/008-design-service.md) | Design overlay on fat phenotypes |
| [VISION-SURFACE-DEFLATION](../VISION-SURFACE-DEFLATION.md) | Do not birth new Assist-shaped surfaces |
| **SD-022** | Talk as types — clean when touched |
| **SD-023** / **SD-024** | Not this theme |

---

## 11. Exit judgment

José closed the theme (2026-09-19).

- Floor holds: `tests/test_authoring_kit_0_70_1.py` + `tests/test_authoring_present_start_0_70_2.py` on `CompositionProfile.embedded()`.  
- Job leaf holds: `tests/test_authoring_job_leaf_0_70_5.py`.  
- Resource land holds: `tests/test_authoring_resource_land_0_70_6.py`.  
- Bind ambient holds: `tests/test_authoring_bind_ambient_0_70_7.py`.  
- ADR-038 **Accepted**.  
- Package stamp stays `0.68.0` (no embedded release).  
- Residual **named** (not paid):

| Residual | Home |
|----------|------|
| Pack id, handle class, Protocol types, door `land`, provider `authoring` | Working names. José locks when the door is tired |
| `LocalPalmInvoker` open-coded `if` menu | Invert **before** any `palm` catalog action ([SD-025](../../../TECH-DEBT.md#sd-025) · [AGENTS §1.1](../../../src/palm/AGENTS.md)) |
| `0.70.4` still calls `create_resource` | Historical test. Job leaf is `0.70.6` |
| `update_flow` / validate | Only if a later loop edits a landed shape. Create-only stays honest |
| Runtime bind | [SD-016](../../../TECH-DEBT.md#sd-016) |
| Assist / CLI forest / Portal | [VISION-SURFACE-DEFLATION](../VISION-SURFACE-DEFLATION.md) |
| Host wizard flats | [SD-024](../../../TECH-DEBT.md#sd-024) |
| 0.68 leftover duals | [SD-023](../../../TECH-DEBT.md#sd-023) |

Do not keep the theme open to invert the palm invoker or to lock names.

*Purpose is a definition. The adapter only lands. Present only drives.*
