# VISION — Navigator (operator-guidance definition · presentation adapter)

**Status:** 📋 **Queue seed** — named **2026-08-19** (José: **navigator**). Not an open minor.  
**Language:** Law uses computer-science terms. Spoken teaching words are marked once. They are not types.  
**Map:** [PALM.md](../PALM.md) · [WRITING.md](../WRITING.md) (talk vs law)  
**Compost:** [VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md) (old Assist / CLI / Portal)  
**Session law:** [VISION-0.58](closed/VISION-0.58.md) (**closed**) · [ADR-027](../adr/027-session-plane.md)  
**Doc cleanup:** [TECH-DEBT.md](../../TECH-DEBT.md) **SD-022**  
**North star:** [VISION-GROVE](VISION-GROVE.md)

---

## 1. Why this note exists

Assist captured a real need: a client that does not already know a definition id still needs a **walk** that selects work.

That need became a **product domain** (`AssistService`) and a fat surface stack (MCP operator path, CLI command forest, Portal). The idea is still right. The home is wrong.

This seed records the **intended split** so later work can grow a thin adapter and treat operator guidance as **catalog definitions**. It does not open a theme.

---

## 2. Spoken words vs law

Talk with José is analogical. Docs must not treat those words as types.

| Spoken (teaching only) | Law term |
|------------------------|----------|
| Rails / Terminal | **Presentation adapter** (intended: a **kit**, not a product service) |
| Navigator / master flow | **Operator-guidance definition** (a catalog definition) |
| Next | Continue the current run (wait plane) |
| Invert | Move operator guidance out of a product service into definitions |
| Palm is the tool; the product is the client | Palm is the **orchestration engine**. Applications are **clients**. |

Use the left column only to teach. Use the right column in PALM, ADRs, and architecture law.

---

## 3. Intent

**Palm** coordinates work: definition → job → instance.  
An **application** (human UI, agent, another system) is a **client** of that engine.

**Surfaces** map a protocol (HTTP, WebSocket, stdio, MCP) onto product doors. They stay thin.

A **presentation adapter** is shared support for those surfaces. It does not own business rules. It:

1. Binds a session (`SessionService` / `BoundSurface`).
2. Presents the current turn (question, choices, actions, value).
3. Submits input.
4. Starts work (work plane) or continues a waiting run (wait plane).
5. Changes continue **focus** among instances the session owns.

**Purpose** is not the adapter:

- The client already knows the work → it **names a definition id**.
- The client does not know → it **starts an operator-guidance definition**.

An **operator-guidance definition** is a normal flow or process in the catalog. It may list, select, and start other definitions (resource steps / Palm invoke). **Many** such definitions are allowed. None is the engine’s `main()`. `examples/definitions/operator_entry.py` is one. A later application replaces the pack.

**Constraint (thinness):** the adapter **consumes runs**. Other operations go through **definitions and their leaves** (resource steps to Palm or to other systems). Do not grow catalog, design, or doctor as adapter verbs. Bind, focus, and continue are adapter **geometry**. They are not purpose.

**Birth, then delete.** Build the adapter and new surfaces **beside** Assist, the CLI forest, and Portal. Do not migrate those packages in place. Compost is [VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md).

---

## 4. Assist (as-built)

[ADR-006](../adr/006-assist-domain.md) made Assist a product domain so operator conversation had a home. Catalog flows already hold part of that home (`operator-entry`).

| As-built | Intended |
|----------|----------|
| `AssistService` + catalog + aliases | Operator-guidance **definitions** |
| Assist present / profiles | Presentation **adapter** (kit) |
| MCP `dispatch_operator_path` into every prefix | Surface calls product doors; purpose stays definitions |
| CLI command forest + dual slots | New thin stdio surface on the adapter + `BoundSurface` |
| Portal as Assist chat (pre-session) | New thin WebSocket surface; session bind first |

### As-built (2026-09-15)

No `BotService` in `src/`. Identity is Assist plus the MCP/Portal operator path stacked on it.

| Fact | Why it is this seed |
|------|---------------------|
| `AssistService.dispatch` is a second spine (list/start/inspect, instance verbs, doctor/top/vitality, discover/menu/open). | Purpose lives in a product path table, not in a **definition**. |
| Root menu and discover starters are Python lists. `inspect_catalog` returns a synthetic turn with no **job**. | Open-coded menu. Tests freeze coconut/design CTAs. |
| `palm-operator-entry` is a wizard that ends. Chat profile then auto-starts `todo-builder` / `coconut-npc` (`CHAT_AUTO_START_INTENTS`, default `auto_start=True`). | The guidance **definition** does not start the work it named. Product owns start after complete. |
| Bare `palm_assist()` → alias `operator-entry/start`. Settings `load_example_definitions` default True. | Example pack is the operator door. Entry chooser is still open (§5). |
| Coconut is the MCP card “run a flow.” | Dogfood entitled as product identity. Replace the pack; do not compost Palm to lose the NPC. |

Fat MCP catalog, CLI REPL-as-chat, Portal FAB/paint, and `session_id` on walk handles are [VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md). Empty host/docs costume is [VISION-0.68](VISION-0.68.md). Do not invert guidance in 0.68.

---

## 5. Open (not locked)

These remain questions. They are not architecture law.

- **Process isolation:** a surface may be a separate OS process that consumes a running Palm. That is scale of the **client**, not a second catalog. Two clients that share one catalog and one job path share one engine process.
- **Visibility:** which definitions a session may list or start. Not identity/IAM. Not admission (organism ready). If a fail-closed gate is required later, publish it as a **system interface**. Do not put the filter on the adapter or the surface.
- **Kit package:** intended home is `palm.kits` (or equivalent). José locks the name when a theme opens.
- **Entry chooser:** how this process names a default operator-guidance definition (seed / catalog tag). Not a skin playlist.

---

## 6. Non-goals (until a theme opens)

- Open a minor or accept an ADR.
- A `GatewayService` or `TerminalService` product domain.
- Stretch admission into authorization.
- Encode application menus in structure definition (DNA ≠ catalog).
- Rewrite Assist / CLI / Portal in place.

---

## 7. Related debt

| ID | Role |
|----|------|
| **SD-022** | Law docs treat talk/metaphor as types — clean when touched |
| **SD-010** | STE density rewrite (different care) |
| **SU-*** / **SI-002** | Surface compost — [VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md) |
| [VISION-0.68](VISION-0.68.md) | Costume compost (open). Not the invert. |
| [VISION-TINY-LLM](VISION-TINY-LLM.md) | Model as resource · context as flow. **Not** this seed’s floor. A guidance pack may include a translator child after the invert is real. |

*Guidance is a definition. The adapter only walks.*
