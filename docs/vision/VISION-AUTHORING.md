# VISION — Authoring adapter (land a shape · definition pack)

**Status:** 📋 **Law seed** (executed as [**0.70** Authoring](closed/VISION-0.70.md), **closed** 2026-09-19). Named **2026-09-19** (José: **authoring adapter**; floor **A**).  
**Locks (José 2026-09-19):** law word **authoring adapter**; floor phenotype **A** (`host.definitions` on `CompositionProfile.embedded()`); Design overlay on fat phenotypes; package **`palm.kits.authoring`**; no `INTENTION_KITS` parking. Theme plan: [VISION-0.70](closed/VISION-0.70.md) (**closed**). ADR [038](../adr/038-authoring-adapter.md) **Accepted**. Handle class unnamed. As-built: `land(host)` / `commit(body)` / `bound()`.  
**Language:** Law uses computer-science terms. Spoken teaching words are marked once. They are not types.  
**Map:** [PALM.md](../PALM.md) · [WRITING.md](../WRITING.md) (talk vs law) · [VERSIONING.md](../VERSIONING.md)  
**Walk:** [VISION-NAVIGATOR](VISION-NAVIGATOR.md) (operator-guidance definition · presentation adapter) · closed [VISION-0.69](closed/VISION-0.69.md) · [ADR-037](../adr/037-navigator-invert.md) **Accepted**  
**Catalog:** `DefinitionService` (`host.definitions`) · Design overlay [ADR-008](../adr/008-design-service.md) (fat phenotypes only)  
**Surface compost:** [VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md)  
**North star:** [VISION-GROVE](VISION-GROVE.md)

This seed records **law**. Theme plan: [VISION-0.70](closed/VISION-0.70.md) (**closed**).

---

## 1. Why this note exists

[VISION-NAVIGATOR](VISION-NAVIGATOR.md) inverted consume: guidance is a **definition**; **`palm.kits.present`** walks session + execution.

Consume has nothing to walk until a shape **lands** in the catalog. Today land is Python in `examples/` plus `DesignService` on fat compositions. `CompositionProfile.embedded()` has **definitions** and **no** Design. Agents cannot publish a flow without compiling Palm JSON. Dogfoods stay shallow because authoring is hard.

Teaching (once): **control kit**. Law: **authoring adapter**. José locked the law word **2026-09-19**. Do not stamp `INTENTION_KITS` until a package exists.

A family-farm OS conversation (Workspace as office, Flutter as capture, Palm as rules engine) motivated the need. That product is **not** this seed. This seed is the **land** walk so present can consume a real apply flow.

---

## 2. Spoken words vs law

Talk with José is analogical. Docs must not treat those words as types.

| Spoken (teaching only) | Law term |
|------------------------|----------|
| Control kit | **Authoring adapter** — kit-as-composition that walks catalog doors |
| Control (hold Palm) | **Host** + `CompositionProfile` — not this adapter |
| Control (drive a run) | Presentation adapter **`palm.kits.present`** |
| Meta-tool inside Palm | **Authoring definition pack** — catalog definition present may start |
| Land a shape | Catalog **create / revise** of a flow or resource definition |
| Rules on the fly | **Resource snapshot** (data). Not a definition revision |
| YAML / Mermaid as the engine | Agent-friendly **draft**. Catalog truth stays `FlowDefinition` |
| `from palm.core import Sequence` | **Refuse.** Core is not an authoring product |

Use the left column only to teach. Use the right column in PALM, ADRs, and architecture law.

---

## 3. Intent

Palm coordinates work: definition → job → instance.

Three client jobs stay split:

| Job | Meaning | Home |
|-----|---------|------|
| **Hold** | Declare a phenotype. Boot. Hold seats. | `ApplicationHost` + `CompositionProfile` |
| **Land** | A flow or resource becomes catalog truth | **This seed:** authoring adapter + authoring **definition pack** |
| **Drive** | Bind, present, submit, start, attach, focus | **`palm.kits.present`** |

Without land, present drives fixtures.  
Without drive, a landed shape does not run.  
Hold already exists.

```text
authoring definition pack (purpose)
        │
        ▼
authoring adapter (geometry)  — draft / validate / commit on host.definitions
        │
        ▼
catalog revision
        │
        ▼
present starts the new definition (drive)
```

One-shot publish without a wizard is the **same adapter** without a job.

**Floor phenotype (José 2026-09-19 — A):** walk `host.definitions` on `CompositionProfile.embedded()`.  
Services on that phenotype: inspect, session, definitions, execution.  
No Assist. No Design seat. No HTTP / MCP / CLI surfaces as this seed’s floor.

**Design overlay:** `DesignService` (propose → validate → impact → commit) stays on **fat** phenotypes (`cli`, `mcp`, `server`, `all_in_one`). It is not the embedded floor.

---

## 4. Split of homes (needs)

Later themes must **leave room**. They must not grow a costume that blocks these homes.

| Need | Home | Must not |
|------|------|----------|
| Drive a waiting run | [VISION-NAVIGATOR](VISION-NAVIGATOR.md) — `palm.kits.present` | Land verbs on present (`draft` / `commit` / catalog menu) |
| Hold / boot | Host + `CompositionProfile` | A second assembler as a kit |
| Land a shape (library) | **Authoring adapter** — one host-held object; walks `host.definitions` | `AuthoringService` / `ControlService` / `DesignKit` product domain |
| Land a shape (job) | **Authoring definition pack** — present starts it | Assist `design_entry` as the land door |
| Catalog write from a leaf | Adapter door (or resource that walks it) | Assume `palm` provider `create_flow` (it does not exist) |
| Agent-safe impact / migrate | `DesignService` on fat phenotypes | Require Design on `embedded()` |
| Rule thresholds, books, keywords | **Resource** snapshot (data) | Inline policy in the flow tree |
| Sheet / Drive digest | Outside Palm (Workspace / GCP automation) | A second Palm whose only job is digest |
| HTTP protocol | `palm.kits.server` | Merge server and authoring kinds |
| Doctor / inspect report | Product **Inspect** | Doctor as adapter verbs |
| Consume surfaces (MCP / CLI / Portal / Flutter) | Later transport of **present** | Birth of this seed; extra present surfaces before a landed shape |

**Kit-as-composition (copy present law, not present verbs):**

- Named package **`palm.kits.authoring`** (José 2026-09-19). As-built `0.70.1`.  
- One library object. Host holds it. Walks **existing** doors.  
- Kit-owned settings. Do not flatten onto core `PalmSettings`.  
- Handle class, Protocol types, constructor/env spelling stay **unnamed** until José locks them.  
- `INSTALLED_KITS` lists the package only when it exists. Keep `INTENTION_KITS` empty until then.

**Do not copy from present:** `bind` / `present` / `submit` / `start` / `attach` / `focus`; `guidance_definition_id`; stamp Home; pattern inspect. If land needs a session, **import present** or use `host.session`.

---

## 5. Authoring pack (meta-tool)

Purpose lives in a **definition**, as Navigator does.

Present binds a session and **starts** the authoring pack. The instance waits. A person or an agent submits a shape. A leaf **speaks** the catalog through the adapter door. A revision exists. Present may then start the new apply flow.

That is Palm authoring Palm. It is the dogfood current examples do not give.

`examples/definitions/design_entry.py` is leftover Assist discovery. It does **not** call the catalog. Do not treat it as this pack.

**Named hole:** provider `palm` actions include `submit_flow`, `list_flows`, inspect. They do **not** include catalog create/revise. A leaf that lands a shape needs that speak. The adapter is that door until a resource walks it.

**Body law:** the draft is control flow and speak contracts (steps, waits, `resource_ref` to a snapshot).  
The draft is **not** thresholds, book names as policy, or keyword lists. Those are snapshot rows.

**Compile target:** catalog truth is `FlowDefinition` / `ResourceDefinition` as today.  
A shallower map (YAML, diagram) may **feed** the adapter later. It is not core. It is not this seed’s floor.

---

## 6. First proof (theme floor)

Theme [VISION-0.70](closed/VISION-0.70.md) executed this floor. Named so we do not start with a language bet.

1. Host: `CompositionProfile.embedded()`.  
2. Authoring adapter walks `host.definitions` (one-shot commit is enough for the floor).  
3. Authoring pack is a wizard present can start; a leaf commits a **thin apply flow**.  
4. That apply flow **speaks** a snapshot resource (file is enough). It waits when unsure.  
5. Present drives the apply flow.  

If that loop is harder than `save_flow` in Python, the adapter is costume.

Farm-shaped numbers (diesel, VAT, Sheets) are **not** the first proof. They are a later pack on the same spine.

---

## 7. Relation to other seeds

```text
Navigator (present + guidance definition)   ← closed 0.69; consume exists
        │
        ▼
this seed (land)                            ← adapter + pack; **0.70 closed**
        │
        ▼
real dogfood on present                     ← apply flow that speaks a snapshot
        │
        ▼
Design overlay on fat phenotypes            ← impact / migrate when needed
        │
        ▼
surface deflation / SDK harvest             ← transports after a shape is real
```

**Navigator** stays consume. Do not grow land onto `palm.kits.present`.

**Design (0.25)** stays a product service on fat compositions. This seed does not delete it. Embedded must not pretend the seat exists.

**Surface deflation** composts Assist / CLI / Portal. It does not birth authoring MCP.

**Tiny LLM** fills a typed hole on continue. It is not the authoring pack.

**Grove** is many Palms. Authoring on one embedded process is not Grove.

---

## 8. Open (not locked)

These remain questions. They are not architecture law.

- Package name under `palm.kits.*` — **locked** `palm.kits.authoring` (José 2026-09-19). Library door as-built `land(host)` (`0.70.1`).  
- Whether catalog speak becomes a `palm` provider action or stays adapter-only.  
- Authoring pack id (`author` is spoken only until locked).  
- When a shallow draft language compiles into `FlowDefinition` (not a YAML-parser theme to have an adapter).  
- When fat phenotypes must use Design commit instead of `definitions` write.

---

## 9. Non-goals (not this theme’s subject)

- Put a name on `INTENTION_KITS`.  
- Implement YAML-in-core or a public BT factory (`Sequence` / `Selector` as product API).  
- Add land verbs to `palm.kits.present`.  
- New MCP / CLI / Portal / Flutter surfaces for present or for authoring.  
- Require Design on `embedded()`.  
- Hot-reload Drive as catalog truth.  
- Make Workspace, Flutter, or edge capture this seed’s subject.  
- A `ControlService`, `AuthoringService`, or `GatewayService`.

---

## 10. Related debt

| ID / seed | Role |
|-----------|------|
| [VISION-NAVIGATOR](VISION-NAVIGATOR.md) · [ADR-037](../adr/037-navigator-invert.md) | Consume walk — do not steal it |
| [ADR-008](../adr/008-design-service.md) | Design overlay on fat phenotypes |
| [VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md) | Do not birth new Assist-shaped surfaces |
| **SD-022** | Talk as types — clean when touched |

*Purpose is a definition. The adapter only lands. Present only drives.*
