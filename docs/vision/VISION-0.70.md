# VISION 0.70 — Authoring

**Status:** 🚧 **Theme open** (José **2026-09-19**). Plan `0.70.0`. Adapter `0.70.1`. Present start `0.70.2`. Pack `0.70.3`. Thin apply `0.70.4`. Job leaf `0.70.5`. Package stamp stays `0.68.0` (no embedded release).  
**Language:** ASD-STE100 Simplified Technical English.  
**Map:** [PALM.md](../PALM.md) — read first.  
**ADR:** [038-authoring-adapter.md](../adr/038-authoring-adapter.md) **Proposed**.  
**Seed (law):** [VISION-AUTHORING](VISION-AUTHORING.md).  
**Migration:** [MIGRATION-0.70](../migrations/MIGRATION-0.70.md).  
**Theme law:** [VERSIONING.md](../VERSIONING.md) (floor · growth · exit judgment).  
**Prior closed:** [VISION-0.69](closed/VISION-0.69.md) Navigator · [ADR-037](../adr/037-navigator-invert.md) **Accepted**.  
**Not this theme:** [VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md) · [VISION-TINY-LLM](VISION-TINY-LLM.md) · [VISION-0.56](VISION-0.56.md) · [VISION-TUNNELS](VISION-TUNNELS.md).  
**North star:** [VISION-GROVE](VISION-GROVE.md).

Teaching name (once): **control kit**.  
Law: **authoring adapter** + authoring **definition pack**.

**Open:** José named **0.70** (2026-09-19). Floor phenotype **A** stays: walk `host.definitions` on `CompositionProfile.embedded()`. Package **`palm.kits.authoring`** locked (José 2026-09-19). Handle class and pack id stay **unnamed**. Library door as-built `0.70.1`: `land(host)` then `commit(body)`. As-built `0.70.2`: present starts that catalog id. As-built `0.70.3`: authoring pack wizard (working catalog name `authoring-pack`; José may rename). As-built `0.70.4`: thin apply (`authoring-apply`) speaks file snapshot (`authoring-snapshot`); present drives. As-built `0.70.5`: pack job leaf walks the adapter (working provider `authoring`; José may rename). [SD-025](../../TECH-DEBT.md#sd-025) named.

---

## 1. Goal

[VISION-NAVIGATOR](VISION-NAVIGATOR.md) inverted consume. Present walks session + execution. Consume has nothing honest to walk until a shape **lands** in the catalog.

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

**Who decides:** José Gabriel Gruber — [VERSIONING.md](../VERSIONING.md) *Who decides*.

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

**As-built `0.70.4`:** thin apply. Working catalog names `authoring-apply` and `authoring-snapshot` (José may rename). Pytest `land(host).commit` still publishes the apply flow (job leaf is `0.70.5`). Snapshot resource lands via `host.definitions.create_resource` (adapter has no resource verb). Present starts the apply by catalog id. Wizard resource step writes file JSON data; confirm waits; present submit completes the apply. Pack stays waiting. Tests: `tests/test_authoring_apply_snapshot_0_70_4.py`.

**As-built `0.70.5`:** pack submit is a `FlowDefinition` mapping. Resource `authoring-commit` (provider working name `authoring`) walks `bound().commit`. Catalog revision exists. Pytest is not that leaf. Present starts the new id. Tests: `tests/test_authoring_job_leaf_0_70_5.py`. Hole named [SD-025](../../TECH-DEBT.md#sd-025).

---

## 3. Growth

While the theme stays open, slices may:

- ✅ Install the kit (`INSTALLED_KITS`) — `0.70.1`.  
- ✅ Add the authoring pack as a wizard present can start — `0.70.3` (as-built `authoring-pack`; pack id unnamed).  
- ✅ Let a leaf commit a **thin apply flow** — `0.70.4` (as-built `authoring-apply`).  
- ✅ Let that apply flow speak a snapshot resource (file is enough) and wait when unsure — `0.70.4` (`authoring-snapshot`).  
- ✅ Drive the apply flow with present (full dogfood loop from the seed) — `0.70.4`.  
- ✅ Let a **leaf of the pack run** speak the adapter — `0.70.5` (working provider `authoring`; [SD-025](../../TECH-DEBT.md#sd-025)).  
- Name handle / Protocol / pack id / provider when José locks them.  
- Decide whether catalog speak becomes a `palm` provider action or stays adapter-only.

**Not floor:** env spelling. Constructor override. Design commit on fat phenotypes. Shallow draft language (YAML / diagram) as compile source.

---

## 4. Why now

1. **0.69** closed consume. Residual Assist stays until surface deflation.  
2. Seed locks in [VISION-AUTHORING](VISION-AUTHORING.md) are complete (law word, floor **A**, Design overlay).  
3. José named **0.70** (2026-09-19).  
4. Extra present surfaces without land are transports of an empty walk.

**Thesis:** Purpose is a definition. The adapter only lands. Present only drives.

---

## 5. Non-goals (other seeds — not forever bans)

| Out of this theme’s *subject* | Home |
|-------------------------------|------|
| Compost Assist / CLI forest / Portal | [VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md) |
| Tiny model body / typed speak | [VISION-TINY-LLM](VISION-TINY-LLM.md) |
| Workload place book | [VISION-0.56](VISION-0.56.md) |
| Tunnels / Grove | [VISION-TUNNELS](VISION-TUNNELS.md) · [VISION-GROVE](VISION-GROVE.md) |
| Design propose → impact → migrate | [ADR-008](../adr/008-design-service.md) on fat phenotypes |
| Workspace / Flutter / edge capture | Farm OS product later — not this adapter |
| Host wizard-named flats | [SD-024](../../TECH-DEBT.md#sd-024) — do not pay as Authoring |
| 0.68 leftover duals | [SD-023](../../TECH-DEBT.md#sd-023) |

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

Bind to [PALM.md](../PALM.md), [VISION-AUTHORING](VISION-AUTHORING.md), [ADR-037](../adr/037-navigator-invert.md), and [ADR-008](../adr/008-design-service.md).

1. **Hold / land / drive stay split.** Host holds. Adapter lands. Present drives.  
2. **Kit-as-composition.** Copy present *law*, not present verbs. One library object. Host holds it. Walks existing doors.  
3. **Floor phenotype A.** `CompositionProfile.embedded()`: inspect, session, definitions, execution.  
4. **Design is overlay.** Fat phenotypes keep `DesignService`. Embedded must not pretend the seat exists.  
5. **Purpose is a definition.** The pack is catalog work. The adapter is geometry.  
6. **Catalog truth** stays `FlowDefinition` / `ResourceDefinition`.  
7. **Body law.** Draft is control flow and speak contracts. Thresholds and books are snapshot rows.  
8. **STE** for theme docs. Spoken words are teaching only ([VISION-AUTHORING](VISION-AUTHORING.md) §2).  
9. **Theme exit is José’s judgment** when the home is proper.

**Spirit:** Do not grow a second land spine. Use `host.definitions`.

---

## 7. Locks (carried from the seed)

José locked these on **2026-09-19**. Detail: [VISION-AUTHORING](VISION-AUTHORING.md).

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

**Named later (not this pass — not QA in 0.70.1):**

| Residual | Home |
|----------|------|
| Handle class / Protocol types | José locks when the door is tired of `_Authoring` |
| Env spelling / constructor override | `land(host)` is as-built; José may rename |
| Provider `create_flow` hole | Adapter door until José locks a `palm` action. Job leaf uses resource `authoring-commit` ([SD-025](../../TECH-DEBT.md#sd-025)) |
| Adapter resource commit | `0.70.4` / `0.70.5` used `host.definitions.create_resource`; `_Authoring.commit` is still `create_flow` only |
| Provider name `authoring` | Duals the kit package. Working name. José may rename |
| Pack id lock | As-built `authoring-pack`; unnamed until José locks |
| Fat phenotypes: Design commit vs `definitions` write | [ADR-008](../adr/008-design-service.md) overlay; not embedded floor |
| Shallow draft language (YAML / diagram) | Not a parser theme to have an adapter |

This table is **not** the remaining work. See §11.

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
| [VISION-NAVIGATOR](VISION-NAVIGATOR.md) · [ADR-037](../adr/037-navigator-invert.md) | Consume walk — do not steal it |
| [ADR-008](../adr/008-design-service.md) | Design overlay on fat phenotypes |
| [VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md) | Do not birth new Assist-shaped surfaces |
| **SD-022** | Talk as types — clean when touched |
| **SD-023** / **SD-024** | Not this theme |

---

## 11. Remaining direction (after `0.70.5`)

The theme is a **seed**. Slice rows above are a walk we took. They are not the answer and not a kill contract.

José keeps exit. Agents explore the home until it is proper or he stops them. Do not invent a fifth example wizard to look complete.

### 11.1 Honest as-built

**Floor is real** (`0.70.1` + `0.70.2`):

- `palm.kits.authoring`: `land(host)` / `commit(body)` → `create_flow`.
- Present `start(catalog_id, by_id=True)` on the same embedded host.
- No Assist. No Design. No land verbs on present.

**Job leaf is real** (`0.70.5`):

- Pack waits on shape. Submit is a `FlowDefinition` mapping.
- Resource `authoring-commit` walks `bound().commit` (definitions bound by `land(host)`).
- Working provider name `authoring`. Duals the kit. José may rename.
- Hole named [SD-025](../../TECH-DEBT.md#sd-025). No `palm` `create_flow`. No invoker `if`.

**Still half-done** (`0.70.4` apply/snapshot):

- Pytest still `commit`s `authoring-apply` and `create_resource` for snapshots.
- Adapter still has one verb: create flow.
- Bind is process-global (SD-025 / SD-016 related).

### 11.2 What “more coherent” means

One session, embedded:

1. Present starts the pack. It waits.
2. A person or agent submits a **shape** (control flow + speak contracts).
3. A **leaf of that run** speaks the adapter. A catalog revision exists. Pytest is not the leaf.
4. Present starts the new apply by catalog id.
5. Apply speaks snapshot **data** (file is enough) and waits when unsure. Present drives.

Library one-shot `land` / `commit` without a pack job stays valid. It is the same adapter.

If a candidate needs a new pattern, a land verb on present, Design on `embedded()`, or an `if` to stay green: **stop** and tell José.

### 11.3 Direction (explore; do not stamp as law)

| Cut | Direction |
|-----|-----------|
| **Job leaf** | ✅ `0.70.5` — resource walks `bound().commit`. Remaining: names, bind ambient, adapter resource verb. |
| **Shape is the apply** | ✅ Pack submit is the `FlowDefinition` body (`0.70.5`). `AUTHORING_APPLY_FLOW` remains a pytest fixture for snapshot dogfood. |
| **Resource land** | If the loop lands a snapshot, the adapter (or a resource that walks it) is the door. Raw `create_resource` in the test is a bypass. |
| **Revise** | Walk `update_flow` / validate only when the loop edits. Create-only can stay honest. |
| **`palm` catalog write** | Named hole. Do not add a provider action only to paint the test green. Adapter stays the door until the walk needs a speak from a resource/provider **and** that door is the smaller truth. |
| **Names** | Pack id, handle, Protocol, `land`, provider `authoring`. Lock when the door is tired. Working names are not product. |

Do **not** open as this theme: MCP / CLI / Flutter authoring, Assist / `design_entry` compost, YAML-in-core, Design impact on embedded, handle rename as a season.

### 11.4 Resume

Read this file §11 + §2 + ADR-038 D1–D8 + [SD-025](../../TECH-DEBT.md#sd-025). Code: `src/palm/kits/authoring/`, `src/palm/providers/authoring/`, `examples/definitions/authoring_pack.py`. Job leaf is `0.70.5`. Do not add `palm` `create_flow`. José exits.

*Purpose is a definition. The adapter only lands. Present only drives.*
