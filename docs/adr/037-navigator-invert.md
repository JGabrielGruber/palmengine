# ADR-037 — Navigator invert (operator-guidance definition · presentation kit)

**Status:** Accepted  
**Date:** 2026-09-17 · **Accepted:** 2026-09-17  
**Theme:** [VISION-0.69](../vision/closed/VISION-0.69.md) (**closed**)  
**Seed:** [VISION-NAVIGATOR](../vision/VISION-NAVIGATOR.md)  
**Map:** [PALM.md](../PALM.md)  
**Related:** [ADR-006](006-assist-domain.md) **Accepted** (as-built Assist — **not** superseded) · [ADR-027](027-session-plane.md) **Accepted**

José accepted (2026-09-17). Theme closed. Floor: one embedded walk without Assist. Package stamp stays `0.68.0`. Compost of Assist is [VISION-SURFACE-DEFLATION](../vision/VISION-SURFACE-DEFLATION.md).

---

## Context

1. [ADR-006](006-assist-domain.md) put the “client does not know a definition id” walk in `AssistService` (routes, catalog aliases, handoff). The need was right. The home went wrong.  
2. MCP, CLI, and Portal grew around Assist as if Assist were the product.  
3. Catalog already has `operator-entry`, but that wizard **ends**. Product then auto-starts other work.  
4. Session is a system plane ([ADR-027](027-session-plane.md)). One session may own many instances. Continue focus is `active_instance_id`.  
5. Harvest (2026-09-16) named three engine holes: session-side attach after start; spawn without nested park; stamp `guidance_instance_id`.  
6. José named theme **0.69** for this invert. Surface compost is a later seed.

## Decision

### D1 — Guidance is a catalog definition

An **operator-guidance definition** is a normal flow in the catalog. Many are allowed. None is the engine `main()`.

The guidance **instance stays** attached when it starts other work. It does not complete as a handoff. Named work is a **sibling instance** on the same session. Return is `focus` of session metadata `guidance_instance_id`.

**Dashboard model:** the guidance job is an operator-wait chooser. It does not open `WaitInterest` on siblings. The session attach list is the process list.

### D2 — Presentation is a kit, not a product service

Package **`palm.kits.present`**. One library object holds **one** `BoundSurface` and walks existing doors: bind, present, submit, start, **attach** (session side), focus.

Not a `PresentService`. Not `palm.kits.server`. Not a dispatch table. Not pattern verbs on the adapter.

**Turn invert:** the kit walks. The pattern fills `JobInspectable` / `InputCapable`. The kit does not switch on `pattern`.

**Kit-contributed settings:** the present kit owns `guidance_definition_id` (`str | None`). Unset → no empty-handed start. Do not flatten the key onto core `PalmSettings`.

### D3 — Job is session-ignorant

The job does not know the walk. Session owns instances. Orchestration owns jobs.

Attach is a **session** write after start. Do not copy `session_id` onto the job as attach law. Continue uses owner gate + focus.

### D4 — Walk writes go through a system interface

Named session-metadata keys (stamp / replace `guidance_instance_id`; later grants) go through a **system interface**. `SessionService` is the product door. The plane stores.

Floor: degenerate allow (owner + attached instance). User plane may install later.

**Stamp caller:** the present kit asks after session-side attach, if the started definition id equals `guidance_definition_id`.  
**Replace predicate:** kit asks; instance already attached; definition id equals `guidance_definition_id`. Titles cannot become Home.

Attach list, `active_instance_id`, `focus`, and owner check stay **geometry**. They are not walk-write verbs.

### D5 — First adapter is the embedded library surface

In-process Python calls the kit. Phenotype `CompositionProfile.embedded()`. **`EmbeddedRuntime` is the engine**, not the adapter.

MCP, CLI, and WebSocket may call the same kit later. They are not this invert’s floor.

### D6 — Grow beside Assist

Do not migrate `AssistService` in place. Do not compost MCP / CLI / Portal in this theme.

[ADR-006](006-assist-domain.md) stays Accepted until a later compost theme supersedes it.

## Consequences

### Positive

- Empty-handed walk uses the job path.  
- Session multi-instance (ADR-027 D9–D10) is the dashboard.  
- Surfaces can share one kit later.  
- Assist remains dogfood until compost.

### Negative / residual

- Two operator spines until surface deflation.  
- Protocol type names, kit handle class, walk-write interface type, and env spelling stay unnamed until José locks them.  
- `SessionOwnershipHook` / job `session_id` inherit is leftover, not floor.  
- Nested `until_input` park and leftover `operator_entry` (still ends) stay.

### Forbidden

- `GatewayService` / `TerminalService` / `PresentService` / `BotService`.  
- `session_id` on the job as attach law.  
- Pattern `if` in the kit.  
- Menus in structure definition.  
- Admission as catalog ACL.  
- Paying [SD-024](../../TECH-DEBT.md#sd-024) by growing the kit on host wizard flats.

## Alternatives considered

- **Rewrite Assist in place** — rejected. Birth, then delete. Compost is [VISION-SURFACE-DEFLATION](../vision/VISION-SURFACE-DEFLATION.md).  
- **Nested BT child as Home** — rejected as required home. Nested park is optional composition. Dashboard is operator-wait + session attach.  
- **User plane first** — rejected. Floor is one anonymous outside subject.  
- **MCP as first adapter** — rejected. Embedded library surface is first.  
- **Supersede ADR-006 now** — rejected. Assist still ships. Supersede when compost deletes the domain.

## Links

- [VISION-0.69](../vision/closed/VISION-0.69.md)  
- [VISION-NAVIGATOR](../vision/VISION-NAVIGATOR.md)  
- [VISION-SURFACE-DEFLATION](../vision/VISION-SURFACE-DEFLATION.md)  
- [ADR-006](006-assist-domain.md)  
- [ADR-027](027-session-plane.md)
