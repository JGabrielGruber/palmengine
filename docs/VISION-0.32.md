# Vision 0.32 — WebSocket Assist Runtime & Portal Backend

**Theme:** Give Palm a **real-time human transport** for Assist — WebSocket as a thin surface over the same meta-dispatch spine as MCP — so we can build **Portal** (lightweight PWA chat) and, later, a digital assistant experience on mobile.

**Status:** **0.32.0**–**0.32.4** shipped · 0.32.5+ open field  

**Depends on:** Assist Service 0.18–0.30 ✅ · MCP meta-surface 0.31 ✅ · ServerRuntime + REST assist ✅  
**Design:** [websocket-assist-portal-design.md](superpowers/specs/2026-07-09-websocket-assist-portal-design.md)  
**Plan:** [websocket-assist-portal-0.32.md](superpowers/plans/2026-07-09-websocket-assist-portal-0.32.md)  
**ADR:** planned with protocol freeze (frame schema) before Portal polish  

---

## Why 0.32

Palm already has strong **operator brains**:

| Capability | Where it lives | Transports today |
|------------|----------------|------------------|
| Meta-orchestrate (path / alias / params) | `AssistService` + MCP assist dispatch | MCP stdio/HTTP, REST `/v1/api/assist/…` |
| Run flows, design publish, doctor, catalog | Same services via dispatch | MCP + REST |
| Progressive disclosure for agents | `PALM_MCP_SURFACE=assist`, `palm://agent/card` | MCP only |
| Human Explorer | SSR HTMX / Studio | Browser HTTP |
| **Live chat backend for a floating UI** | — | **Missing** |

Historical status (still true before 0.32):

- `WebSocketSurface` is a **placeholder** (`GET /v1/surfaces/websocket` → 501 “planned”).
- Docs since 0.13–0.18 deferred “WebSocket live assist stream”.
- Weak-LLM deferred list still mentions WebSocket assist stream.

**Product arc (this vision’s north star):**

```text
MCP (coding agents)
        ↘
         AssistService / services  ← single brain
        ↗
WebSocket (humans → Portal PWA → Android)
```

Without WebSocket (or equivalent), Portal would be forced into chatty REST polling or re-embedding Explorer — both wrong for a **floating assistant** UX.

---

## Goal

| Shift | From | To |
|-------|------|-----|
| Human real-time entry | Explorer forms / full page | **Chat turns** over WebSocket |
| Protocol | Ad-hoc REST per screen | **Same dispatch language as `palm_assist`** |
| Client | Heavy SSR or custom glue | **Thin Portal**: render `question` / `choices` / `actions`, send `value` |
| Runtime surface | Stub `WebSocketSurface` | **Real `/ws` channel**, assist-first |
| Future mobile | Unplanned | **Same frames** in WebView → native |

**Assist-first means:** phase 1 is **request/response chat** (dispatch → assistant turn), not a firehose of every job event. Event push is a later optional ladder step.

---

## Principles

1. **Thin surface, fat services** — WebSocket code must not reimplement Assist/Design/Flows.
2. **One meta-execute path** — frames map to existing `normalize_assist_dispatch_args` → `dispatch_operator_path` → `shape_dispatch_result` (or a shared extract if purity requires moving helpers).
3. **Assistant envelopes for humans** — default `format=assistant` on the channel (`question`, `choices`, `hint`, `actions`, `mutation`).
4. **Core purity / SRP** — no `palm.core` imports from runtimes beyond existing patterns; no pattern logic in `common`.
5. **MCP stays the agent path** — WebSocket is not a replacement for MCP; it is the **human** sibling.
6. **Portal is a client** — PWA is optional and staged; protocol must work with a minimal HTML dogfood first.
7. **Open ladder** — ship valuable slices; leave room for auth, multi-tab, push, Android without rewriting the protocol.

---

## Non-goals (track-wide, not forever)

- Replacing Explorer or Studio
- Full job/wizard event bus as MVP
- Multiplayer rooms / collaborative editing
- Offline-first mobile (later)
- Inventing a second operator domain (`palm/services/portal/`)

---

## Complexity ladder (open-ended)

| Phase | Theme | Behavior change? |
|-------|--------|------------------|
| **0.32.0** | Vision + design + protocol draft + plan | **No** (docs) |
| **0.32.1** | Transport MVP — real WebSocket upgrade/handler | **Yes** |
| **0.32.2** | Assist channel — dispatch frames ↔ turn frames | **Yes** |
| **0.32.3** | Continuity — reconnect, session_id binding, basic auth hook | **Yes** |
| **0.32.4** | Portal dogfood — lightweight chat shell (static or minimal PWA) | **Yes** ✅ |
| **0.32.5+** | Open — event push, cookies/auth polish, multi-tab, Android shell, job stream | Optional |

---

## Success criteria (track)

1. A browser (or `websocat`) can open a Palm WS endpoint, send a dispatch frame, and receive an assistant **turn** for operator-entry or a flow.
2. No new service domain is required for the happy path — only surface + protocol.
3. Frame schema is documented in an ADR and stable enough for a Portal client.
4. Assist-only *semantics* work: publish, run, doctor, catalog via the same aliases as MCP (where applicable over WS).

---

## Relationship to other tracks

| Track | Relationship |
|-------|----------------|
| **0.30 Assist design entry** | Provides operator UX content (choices, CTAs, publish) that Portal will render |
| **0.31 MCP meta-surface** | Same progressive-disclosure philosophy; WS clients don’t need 39 tools |
| **0.18–0.19 Assist** | Original “WebSocket live assist stream” deferred item — this track fulfills it productively |
| **Explorer SSR** | Parallel human surface; Portal is chat-shaped, not page-shaped |

---

## Long product arc

```text
0.32.x  WebSocket Assist + dogfood chat
   ↓
0.33?   Portal PWA (installable, floating panel, theming)
   ↓
Later   Android (WebView Portal → native chat)
```

Each step reuses the **frame protocol** and **AssistService** — not a new orchestration stack per client.

---

## References

- Stub: `src/palm/runtimes/server/surfaces/websocket/surface.py`
- Dispatch spine: `src/palm/runtimes/mcp/assist/dispatch.py`
- REST assist: `src/palm/runtimes/server/surfaces/rest/assist/`
- Transport today: `src/palm/runtimes/server/transport/stdlib.py` (HTTP only)
- [ADR-006](adr/006-assist-domain.md) · [VISION-0.18-ASSIST](VISION-0.18-ASSIST.md) · [VISION-0.31](VISION-0.31.md)
- STATUS deferred: WebSocket assist stream
