# VISION — Surface deflation (queue seed)

**Status:** 📋 **Named at 0.58 theme exit** — not an open minor yet.  
**Language:** ASD-STE100 (practical).  
**Map:** [PALM.md](../PALM.md) · session law [VISION-0.58](closed/VISION-0.58.md) (**closed**) · [ADR-027](../adr/027-session-plane.md)  
**Debt:** [TECH-DEBT.md](../../TECH-DEBT.md) **SU-*** · **SI-002** / **SI-006** / **SI-010** · **SI-016** residual  
**Grow (not compost):** [VISION-NAVIGATOR](VISION-NAVIGATOR.md) — operator-guidance definition + presentation adapter.  
**Closed costume (not this pile):** [VISION-0.68](closed/VISION-0.68.md) — empty work, unread duals, living doc lies in host/docs. Residual [SD-023](../../TECH-DEBT.md#sd-023).  
**North star:** [VISION-GROVE](VISION-GROVE.md)

**Split:** 0.68 does not deflate surfaces. Navigator does not rewrite Assist in place. This file owns surface identity, fat catalogs, and era handles.

---

## 1. Why this note exists

Session plane is **live**. Vocabulary law is taught.  
Surfaces and product handles still carry **pre-plane Palm**.

They are not worthless. They **taught** Palm what it needed:

| Scaffold | What it discovered |
|----------|-------------------|
| Early MCP domain tools | Agents can operate Palm without curl recipes |
| Assist | Conversation envelope, handoff, operator entry |
| Portal + WS | Need for bind, and later **subscribe under a subject** |
| Explorer + system inspect | Need to see and poke running Palm |
| `FlowSession` / `AssistSession` | Need for **product verbs** on one durable run |

They **served that purpose**. Palm redefined itself on the lessons (planes, SessionService, BoundSurface, wait law, assist-first MCP).

**Now** many of those shapes are **outdated weight**: they still work for testing and dogfood, but they keep old pain as permanent furniture.

This file **names the wisdom** so a later theme can trim without amnesia.  
It does **not** open a purge slice. Value delivery and other named dogfoods may come first.

---

## 2. Law we already have (floor)

Do not re-litigate session in a surface theme.

| Term | Meaning |
|------|---------|
| **`session_id`** | System outside subject (`sess-…` / `sess-svc-…`) |
| **`instance_id`** | Product continue handle (one run) |
| **BoundSurface** | Surface bind: session + continue focus |
| **SessionService** | Product door (not resume law) |
| **Wait plane** | Only continue path |
| **Surface** | Thin transport + bind proof — **not** a second identity model |

**Rule:** Session (BoundSurface) leads **authority and subscription scope**.  
**Rule:** Surface still **answers** request/response under that bind.  
**Rule:** Do not invent private resume or dual-own for admin UX.

---

## 3. Surfaces — intent and impact (not a code map)

Precision of file paths is not the point. **Intent** and **drag** are.

### 3.1 MCP

| | |
|--|--|
| **Intent** | Let coding agents operate Palm (flows, design, doctor) without inventing HTTP. |
| **Discovery** | One parametric door (`palm_assist`) beats many domain tools for weak models. Progressive docs (card → guide → skill). |
| **Impact if left heavy** | Dual mental model (assist meta + fat domain catalog); agents re-learn old `session ≡ instance`; SU-003 style bulk resists thin-surface law. |
| **Dogfood today** | Prefer `palm_assist` + SessionService bind; vocabulary taught in skill/MCP.md (0.58.20). |
| **As-built (2026-09-15)** | Default `PALM_MCP_SURFACE=full` registers domain packs beside `palm_assist`. FastMCP title is `Palm Operator`. Profile `experimental` is the same group set as `full`. In-process MCP constructs `ServerRuntime` (a composition root), not a wire to a running host. `build_assist_routes_catalog` copies product command paths onto `palm://assist/routes`. L0 continue still teaches `{session_id, flow_id, value}` with example `inst-1` (skill already says `instance_id`). Card “Run a flow” names `coconut-npc`. |
| **Later** | Deflate domain tools or gate them; keep assist-first as law, not fashion. Trim L0 copy that calls the continue handle a session (living lie; 0.68 may cut the sentence). Do not rename FastMCP kwargs in 0.68. |

### 3.2 Assist (product)

| | |
|--|--|
| **Intent** | Operator conversation: entry, question/choices, handoff into business flows. |
| **Discovery** | Surfaces need an **envelope**, not only raw flow inspect. |
| **Impact** | Product handles still named “session” for **instance** (SI-002). Still useful; still a vocabulary trap. |
| **Dogfood today** | Assist walks under BoundSurface; system session is owner. |
| **As-built (2026-09-15)** | `AssistSession.session_id` is still the instance id (SI-002). Bare `palm_assist()` and Portal hello default to `operator-entry/start`. Command table, fake catalog turns, and chat auto-start after the guidance definition ends are the **invert** — [VISION-NAVIGATOR](VISION-NAVIGATOR.md) as-built. This file only composts the fat surface stack around Assist. |
| **Later** | Thin **AssistWalk** (instance-true) or cut handle layer and rebuild from SessionService + instance verbs. Intended split: [VISION-NAVIGATOR](VISION-NAVIGATOR.md). Birth adapter beside Assist; do not migrate the package in place. |

### 3.3 CLI / REPL

| | |
|--|--|
| **Intent** | Human operator on a terminal; track “what am I driving.” |
| **Discovery** | Need active focus and bind; dual slots (`system` + `assist`) grew before BoundSurface. |
| **Impact** | SI-006: instance-shaped “session” slot names; mirrors next to BoundSurface (SI-016 partial). |
| **As-built (2026-09-15)** | Empty argv is REPL. Non-command lines become `assist input`. Banner teaches `assist start operator-entry`. `CliContext` keeps BoundSurface plus mirrors `active_system_session_id` / `active_assist_session_id` / `active_instance_id`. README one-shot `palm resource *` was a living lie; **0.68.16** trimmed it. Not a CLI rewrite. |
| **Later** | One BoundSurface truth; drop dual mirrors; alias forest (SU-005) only if still needed. New thin stdio surface on the presentation adapter — [VISION-NAVIGATOR](VISION-NAVIGATOR.md). |

### 3.4 WebSocket + Portal

| | |
|--|--|
| **Intent** | Live channel for assist-like ops; portal was a **test shell** for WS. |
| **Discovery** | Bind alone is not enough — **subscribe** needs a session subject; multi-instance walk needs focus. |
| **Impact** | Portal can look like product identity; WS can answer clients without session-led scope (SU-007). |
| **Law split** | Surface: frames, hello/ping, dispatch **answers**. Session: bind authority + **subscription/filter** scope. Wait plane: real continue. |
| **As-built (2026-09-15)** | `GET /portal/` is a branded landing titled “Palm Portal — Assist”: empty page, language cards, FAB, hidden chat, PWA name `Palm Portal`. Two JS slots (`sessionId` / `instanceId`) are honest **session** vs **instance** packaging — keep. Hello auto-starts `operator-entry/start` without a human act — costume (the surface owns the walk). `skins.js` pt-BR `synonyms` rewrite typed answers before dispatch — utterance policy on the surface, not paint. Tests freeze landing + FAB + paint map. |
| **Later** | Drop product identity (title, FAB, PWA, empty face). Keep two slots. Move synonym/policy off the static skin. Portal v2 (or delete demo shell): session-subscription-first; dispatch always under BoundSurface. Do not compost this pile in 0.68. |

### 3.5 Explorer (SSR) + REST operator UI

| | |
|--|--|
| **Intent** | Inspect Palm and drive wizards in a browser. |
| **Discovery** | Operators need HTMX workspaces, catalogs, job/instance views. |
| **Impact** | Bare instance drive without bind (SI-010); bulk/god files (SU-001/002); weight vs thin-adapter law (SU-008). |
| **Still useful** | Testing and human dogfood of the engine. |
| **As-built (2026-09-15)** | Explorer nav puts Assist first after Home as “Guided entry” / conversational operator guidance. That is Assist-as-king furniture on an inspect **surface**. |
| **Later** | Bind cookie / BoundSurface on entry; trim bypass; do not treat explorer as second product spine. |

### 3.6 System / host inspect product

| | |
|--|--|
| **Intent** | Doctor, waiting, job inspect — truth about the running system. |
| **Discovery** | Surfaces must not own engines; ports and product services do. |
| **Impact** | Healthy when thin; hurtful when surfaces re-open engine fields (SD-005 residual spirit). |
| **Later** | Keep as product/port path; never grow a second operate stack on the surface. |

### 3.7 Product walk handles (`FlowSession` / `AssistSession`)

| | |
|--|--|
| **Intent (original)** | Stateful API: inspect / input / backtrack / resume / cancel for one durable run. |
| **Era** | Before system session; “session” meant the run. |
| **Intent (still real)** | Product **verbs on one instance** — still needed. |
| **Impact** | Class fields still say `session_id` for continue id (SI-002). Agents and new code re-learn the lie. |
| **As-built (2026-09-15)** | `FlowSession.session_id` stores the instance and copies it to `instance_id` in views. `inspect_session` aliases `inspect_instance`. REST samples pin `session_id` to `inst-abc123`. Living README / ARCHITECTURE still teach flow session ≡ instance. BoundSurface two-slot is honest; these handles are not. |
| **Not the goal** | Multi-instance ownership, subscription, system identity — those are plane + BoundSurface. |
| **Later options** | **Collapse** to honest `FlowWalk` / `AssistWalk` under BoundSurface, **or** **cut** handle classes and rebuild when APIs/SDKs land. Do not polish the lie forever. Trim living copy in 0.68 when it is a doc lie; do not rename product fields in 0.68. |

---

## 4. Wisdom (do not debunk)

1. **Scaffolds that discover law are compost, not permanent architecture.** Harvest the lesson; remove the mass when ready.  
2. **Useful for testing ≠ entitled to define Palm.** Explorer and portal may stay until a redo pays; they must not set vocabulary or ownership.  
3. **Trim when you can deliver value without them — or when they block value.** Full surface redo takes time; other dogfoods and API/SDK docs may come first.  
4. **Clean surfaces to discover dead code** is a valid urge. Prefer delete/demote with **intention rows** over dual-path shims.  
5. **One dogfood path after a cut** beats five half-alive ones (`palm_assist` + SessionService + instance continue).  
6. **Named later is not amnesia** — STUBS / TECH-DEBT / this vision hold the seed until a minor opens.

---

## 5. Target shape (when a theme opens)

```text
Outside client
    │
    ▼
Surface (MCP / WS / HTTP / CLI)     ← transport only
    │  bind proof → BoundSurface
    ▼
SessionService                      ← product door
    │
    ├─ Session plane                ← own, focus, watch scope
    ├─ Walk verbs (instance)        ← inspect/input/… (honest name)
    └─ Wait / work / workload       ← start & continue law unchanged
```

**Grow beside this compost:** presentation adapter + operator-guidance definitions — [VISION-NAVIGATOR](VISION-NAVIGATOR.md).

**Out of scope for surface deflation:** full user plane, Grove mesh, shared plane-store framework (SI-014).  
**Boot phases (SD-014)** are paid under **[VISION-0.59](closed/VISION-0.59.md)** (**closed**) — do not mix surface compost into boot slices.  
**0.68** composts empty host/docs costume — do not mix FAB, MCP catalog, or CLI forest into that theme.

---

## 6. Suggested later work (unordered seeds)

Not a committed patch list. Chew when a theme owns them.

| Seed | Spirit |
|------|--------|
| **Walk handles** | SI-002 — honest instance fields or cut + rebuild |
| **CLI slots** | SI-006 / SI-016 — BoundSurface only; empty argv is not a chatbot |
| **Explorer bind** | SI-010 + SU-001 — no bare instance as law; Assist is not the first identity tile |
| **MCP deflate** | SU-003 — assist-first; domain tools optional/gated; drop `experimental` as a second `full`; in-process MCP is not a second composition root |
| **Portal / WS** | SU-007 — subscription led by session; surface answers under bind |
| **Portal identity** | Drop title / FAB / PWA / empty face as Palm’s product name. Keep two session/instance slots. Move synonym rewrite off the static skin. |
| **Hello auto-start** | Do not start `operator-entry` because the socket said hello. Entry chooser is Navigator, not Portal JS. |
| **Surface weight** | SU-008 — metric + “no new engine bypass” |
| **APIs / SDKs docs** | Public contracts that make walk + session dogfood without era handles |
| **Named product dogfoods** | Coconut as MCP “run a flow”, default `load_example_definitions` — entitled dogfood. Prefer [VISION-NAVIGATOR](VISION-NAVIGATOR.md) pack replace over 0.68 delete. |

---

## 7. Relation to 0.58 exit

| 0.58 closed | This note |
|-------------|-----------|
| Session plane home + law | Assumes that floor |
| Vocabulary + skill | Surfaces must not re-teach the lie |
| Residual SI/SU listed | This note **explains impact** for later chew |
| SD-008 closed | Structure live; surface compost is **not** SD-008 |

**Do not** block other progress waiting for a full surface purge.

---

## 8. Exit criteria for a future surface-deflation theme (draft)

When someone opens a minor on this seed:

1. [ ] Intent of each kept surface is one sentence in STATUS/VISION.  
2. [ ] Deleted or demoted era demos leave **intention** rows, not silent gaps.  
3. [ ] Product walk verbs are honest (walk/instance) or rebuilt behind SessionService.  
4. [ ] Dogfood path remains testable without dual identity.  
5. [ ] SU-* / SI-002 family residual updated or closed.

---

*Surfaces discover Palm. Session glues Palm. Do not let the discovery layer own the glue forever.* 🌴
