# ADR-038 — Authoring adapter (land a shape · definition pack)

**Status:** Proposed  
**Date:** 2026-09-19  
**Theme:** [VISION-0.70](../vision/VISION-0.70.md) (**open**)  
**Seed:** [VISION-AUTHORING](../vision/VISION-AUTHORING.md)  
**Map:** [PALM.md](../PALM.md)  
**Related:** [ADR-037](037-navigator-invert.md) **Accepted** (consume — present kit) · [ADR-008](008-design-service.md) **Accepted** (Design overlay — **not** superseded) · [ADR-007](007-definition-revisioning.md) **Accepted** (catalog revision)

José opened theme **0.70** (2026-09-19). This ADR stays **Proposed** until theme exit. Package stamp stays `0.68.0`. José locked package **`palm.kits.authoring`** (2026-09-19). Handle class stays unnamed.

---

## Context

1. [ADR-037](037-navigator-invert.md) inverted consume: guidance is a catalog definition; `palm.kits.present` walks session + execution.  
2. Consume has nothing to walk until a shape lands in the catalog.  
3. Land today is Python in `examples/` plus `DesignService` (`propose` → `validate` → `impact` → `commit`) on fat compositions ([ADR-008](008-design-service.md)).  
4. `CompositionProfile.embedded()` has `definitions` and **no** Design seat. Agents cannot publish a flow without compiling Palm JSON. Dogfood stays shallow.  
5. The `palm` provider can submit / list / inspect. It cannot write a catalog flow (`create_flow` is a named hole).  
6. José named the law word **authoring adapter** (2026-09-19). Floor phenotype **A**: walk `host.definitions` on `embedded()`. Teaching word **control kit** is not a type.

## Decision

### D1 — Hold / land / drive stay split

| Job | Home |
|-----|------|
| **Hold** | `ApplicationHost` + `CompositionProfile` — not a kit |
| **Land** | Authoring adapter + authoring **definition pack** |
| **Drive** | `palm.kits.present` — no land verbs |

Do not merge present + design + doctor into one costume. Do not grow `draft` / `commit` onto present.

### D2 — Authoring adapter is kit-as-composition

One library object. Host holds it. Walks **existing** doors: `host.definitions` (`create_flow` / `update_flow` / validate as today).

Not an `AuthoringService`. Not a `ControlService`. Not a `DesignKit`. Not a `GatewayService`.

**Turn invert (copy present law, not present verbs):** the adapter walks the catalog. It does not become a product domain. It does not switch on pattern.

Kit-contributed settings stay on the kit object. Do not flatten them onto core `PalmSettings`.

Package **`palm.kits.authoring`** (José 2026-09-19). As-built `0.70.1`: in `INSTALLED_KITS`. Library door `land(host)`; `commit(body)` walks `create_flow`. Keep `INTENTION_KITS` empty.

Handle class, Protocol types, env spelling stay unnamed until José locks them. Constructor spelling is as-built `land`; José may rename.

### D3 — Floor phenotype is embedded

First proof runs on `CompositionProfile.embedded()`. Services on that phenotype: inspect, session, definitions, execution.

No Assist. No Design seat. No HTTP / MCP / CLI / Flutter surfaces as this theme’s floor.

One-shot commit through `host.definitions` is enough for the floor. Present must be able to start the landed definition.

### D4 — Design stays overlay on fat phenotypes

[ADR-008](008-design-service.md) stays **Accepted**. `DesignService` remains on fat compositions (`cli`, `mcp`, `server`, `all_in_one`) for propose → validate → impact → commit.

This theme does not delete Design. Embedded must not pretend the seat exists. Do not require Design on `embedded()`.

### D5 — Purpose lives in a definition pack

An **authoring definition pack** is a normal catalog flow. Present may start it. The instance waits. A person or an agent submits a shape. A leaf speaks the catalog through the adapter door. A revision exists. Present may then start the new apply flow.

`examples/definitions/design_entry.py` is leftover Assist discovery. It is not this pack.

Pack id stays unnamed (`author` is spoken only).

### D6 — Catalog truth is FlowDefinition / ResourceDefinition

Compile target stays today’s catalog types. A shallower map (YAML, diagram) may feed the adapter later. It is not core. It is not this theme’s floor.

Refuse a public BT factory (`from palm.core import Sequence`) as the authoring product.

### D7 — Body law

The draft is control flow and speak contracts (steps, waits, `resource_ref` to a snapshot).

The draft is **not** thresholds, book names as policy, or keyword lists. Those are snapshot rows (data). A resource snapshot is not a definition revision.

### D8 — Named hole: provider catalog write

Provider `palm` actions include submit / list / inspect. They do **not** include catalog create / revise. The adapter is that door until José locks a provider action or a resource that walks the adapter.

## Consequences

### Positive

- Embedded land no longer requires a fat Design seat.  
- Present can consume a shape that landed in-process.  
- Design overlay remains for impact / migrate on fat phenotypes.  
- Hold / land / drive stay three jobs.

### Negative / residual

- Handle class, Protocol types, pack id, and env spelling stay unnamed until José locks them. Package is `palm.kits.authoring`. Library door as-built `land(host)`.  
- Two land paths until a later decision: adapter `definitions` write vs Design commit on fat.  
- Provider `create_flow` remains a hole.  
- Assist / CLI / Portal stay until [VISION-SURFACE-DEFLATION](../vision/VISION-SURFACE-DEFLATION.md).

### Forbidden

- `AuthoringService` / `ControlService` / `DesignKit` / `GatewayService`.  
- Land verbs on `palm.kits.present`.  
- `INTENTION_KITS` name without a package.  
- YAML-in-core or public BT factory as the floor.  
- Require Design on `embedded()`.  
- New MCP / CLI / Portal / Flutter surfaces as this invert’s floor.

## Alternatives considered

- **Grow land onto `palm.kits.present`** — rejected. Present is consume. Land would re-grow Assist.  
- **Require Design on embedded** — rejected. Floor phenotype **A** is definitions-only.  
- **DesignKit as a service** — rejected. Design is already a product service on fat hosts. The honest sibling is land-only kit-as-composition.  
- **YAML / Sequence DSL as the engine** — rejected. Catalog truth stays `FlowDefinition`. Gemini’s core Sequence API does not exist and must not become the kit API.  
- **Park `INTENTION_KITS` before a package** — rejected. Install list stays honest.  
- **MCP / Flutter as first adapter** — rejected. Embedded library surface is first (same as Navigator).

## Links

- [VISION-0.70](../vision/VISION-0.70.md)  
- [VISION-AUTHORING](../vision/VISION-AUTHORING.md)  
- [VISION-NAVIGATOR](../vision/VISION-NAVIGATOR.md)  
- [ADR-037](037-navigator-invert.md)  
- [ADR-008](008-design-service.md)  
- [ADR-007](007-definition-revisioning.md)
