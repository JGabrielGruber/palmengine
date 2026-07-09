# WebSocket Assist Runtime & Portal Backend Design

| Field | Value |
|-------|--------|
| **Document** | Design specification + protocol draft + open ladder |
| **Date** | 2026-07-09 |
| **Status** | **Draft for 0.32 track** (0.32.0 docs foundation) |
| **Target track** | **0.32 WebSocket Assist + Portal backend** |
| **Depends on** | Assist 0.18–0.30, MCP dispatch 0.19–0.31, ServerRuntime surfaces |
| **Vision** | [docs/VISION-0.32.md](../../VISION-0.32.md) |
| **Plan** | [docs/superpowers/plans/2026-07-09-websocket-assist-portal-0.32.md](../plans/2026-07-09-websocket-assist-portal-0.32.md) |
| **ADR** | Required before Portal polish — freeze frame schema |

---

## 1. Overview

This design specifies how Palm grows **beyond MCP** for interactive humans:

1. **WebSocket runtime surface** — real-time duplex transport on `ServerRuntime`.
2. **Assist channel first** — chat turns using the same meta-dispatch as `palm_assist`.
3. **Portal-ready protocol** — stable JSON frames so a lightweight PWA (and later Android) can be pure clients.

It intentionally dumps architectural context so implementers do not rediscover decisions already made in 0.18–0.31.

---

## 2. Background & Motivation

### 2.1 What Palm already has

```
                    ┌─────────────────┐
   Coding agents ──►│  MCP (stdio/HTTP)│──► palm_assist tool
                    └────────┬────────┘
                             │  normalize + dispatch + shape
                    ┌────────▼────────┐
   Integrators  ───►│  REST /v1/api/*  │──► same services
                    └────────┬────────┘
                             │
   Humans (today) ─►│  Explorer SSR   │──► forms/HTMX (not chat)
                    └─────────────────┘

   Humans (target) ►│  WebSocket      │──► same dispatch, assistant turns
                    └─────────────────┘
                             │
                    ┌────────▼────────┐
                    │  services/*     │  Assist, Design, Flows, System
                    │  common + core  │
                    └─────────────────┘
```

**Key code anchors (do not reinvent):**

| Piece | Path | Notes |
|-------|------|--------|
| Assist domain | `palm/services/assist/` | `dispatch`, scenarios, handoff, doctor, catalog, discover |
| MCP assist proxy | `palm/runtimes/mcp/assist/dispatch.py` | `normalize_assist_dispatch_args`, `dispatch_operator_path`, `shape_dispatch_result` |
| MCP slim surface | `palm/runtimes/mcp/surface.py` | `PALM_MCP_SURFACE=assist` — one tool philosophy |
| Progressive docs | `palm://agent/card`, `docs/mcp-card.txt` | L0/L1/L2 |
| REST assist | `runtimes/server/surfaces/rest/assist/` | HTTP projection of assist paths |
| WS stub | `runtimes/server/surfaces/websocket/surface.py` | 501 placeholder; `mount_prefix=/ws` |
| HTTP transport | `runtimes/server/transport/stdlib.py` | Threading `BaseHTTPRequestHandler` — **no WS upgrade today** |
| Surfaces registry | `default_surfaces()` includes `WebSocketSurface` | Ready to flesh out |

### 2.2 Historical intent

- **VISION-0.13 / 0.15 / 0.16:** WebSocket live streaming deferred post-service remount.
- **VISION-0.18-ASSIST:** “WebSocket live assist stream (binds to execution/flows after WebSocket, if shipped).”
- **STATUS / weak-LLM deferred:** WebSocket assist stream listed for years.
- **ARCHITECTURE.md:** WebSocket = planned; optional Starlette for async REST + WS.

### 2.3 Product motivation (this session)

| Horizon | Product | Backend need |
|---------|---------|--------------|
| Near | **Portal** — lightweight PWA, floating web chat | Stable WS assist protocol |
| Medium | Installable PWA, theming, multi-session | Reconnect + auth |
| Far | **Android digital assistant** | Same protocol (WebView → native) |

MCP remains the **coding-agent** path. Portal is the **human chat** path. Both must call the same services.

### 2.4 Pain if we skip WebSocket

| Approach | Problem for Portal |
|----------|-------------------|
| Poll REST every N ms | Latency, battery, ugly UX |
| SSE only server→client | Awkward for chat inputs; still need POST |
| Reuse Explorer HTMX | Not a floating assistant; heavy |
| Client embeds MCP over stdio | Impossible in browser |
| New “PortalService” | Duplicates Assist — violates SRP |

**WebSocket duplex** is the natural browser-native backend for chat.

---

## 3. Goals & Non-Goals

### Goals

1. Define a **frame protocol** (client/server JSON) for Assist over WebSocket.
2. Map frames to **existing** assist dispatch (path / alias / params).
3. Default **assistant** view shape for Portal rendering.
4. Plan a **transport strategy** (stdlib upgrade vs thin async mount).
5. Stage **Portal** as a client after protocol dogfood.
6. Keep the ladder **open-ended** for mobile and event streaming.

### Non-goals (0.32 track baseline)

| Non-goal | Rationale |
|----------|-----------|
| Replace MCP or REST | Sibling transports |
| Full job event firehose as MVP | Scope creep; chat first |
| Multi-user collaborative rooms | Later product |
| Offline-first mobile | Later |
| New service package `palm/services/portal` | Client concern |
| Perfect browser polyfills for all WS edge cases | Ship MVP; document limits |

---

## 4. Proposed Architecture

### 4.1 Layering (normative)

```
Portal PWA / dogfood HTML / Android WebView
        │  wss://host/ws/v1/assist   (or /ws/assist — freeze in ADR)
        ▼
WebSocketSurface (thin)
  - accept connection
  - parse frames
  - auth (optional bearer)
  - call shared dispatch
  - write turn/error frames
        ▼
Shared dispatch (today: mcp.assist.dispatch; optionally extract)
  normalize_assist_dispatch_args
  resolve_dispatch_path
  dispatch_operator_path(ctx, path, params)
  shape_dispatch_result(..., format=assistant)
        ▼
ServerContext → host.assist / design / execution / system
```

**Invariant:** WebSocket handlers import **services and shared dispatch**, not pattern engines.

### 4.2 Relationship to MCP meta-surface (0.31)

| MCP lesson | WebSocket application |
|------------|------------------------|
| One meta-tool | One **channel** + dispatch frames (no 39 client tools) |
| Progressive docs | Portal loads card copy or embeds L1; full guide optional |
| Aliases | Same alias strings (`assist/doctor`, `design/publish`, …) |
| Surfaces | WS is a **runtime surface**, not an MCP surface profile |

### 4.3 Transport stack decision (to resolve in 0.32.1)

| Option | Pros | Cons |
|--------|------|------|
| **A. Extend stdlib** ThreadingHTTPServer with manual WS upgrade | Zero new deps | Painful WS framing, TLS, scale |
| **B. Thin Starlette/uvicorn mount** alongside or instead of stdlib for server | Proper ASGI WS, widely used | New extra; dual-stack risk |
| **C. websockets library + custom loop** | Focused | Still need HTTP for REST/Explorer |

**Recommendation (design default):**  
- **0.32.1 research spike** (1–2 days max) to prove stdlib upgrade **or** document failure and pick **B** with `palmengine[server-ws]` extra.  
- Do **not** rewrite REST/SSR onto Starlette in the same phase. Prefer **side-by-side** WS server on same host/port if possible, or documented dual-port for MVP.

**ADR-013 (proposed title):** WebSocket Assist transport and frame protocol.

### 4.4 Auth sketch

| Mode | Behavior |
|------|----------|
| Dev (default) | Open or same `PALM_SUBJECT` as MCP |
| Bearer | `Authorization: Bearer …` on HTTP upgrade; optional first `hello` frame with token |
| Cookie | Portal same-origin cookie later |

Auth must not block 0.32.1–0.32.2 dogfood; document security clearly for production Portal.

---

## 5. Protocol draft (freeze candidate)

Version field on hello so clients can evolve.

### 5.1 Connection lifecycle

1. Client opens WebSocket to configured URL.
2. Server may send `{ "op": "hello", "protocol": 1, "server": "palm", "version": "<palm.__version__>" }`.
3. Client sends `{ "op": "hello", "protocol": 1, "client": "portal"| "dogfood" | "…" }` (optional).
4. Client sends `dispatch` frames; server replies with `turn` or `error` correlating `id`.
5. Either side may send `{ "op": "ping" }` / `{ "op": "pong" }`.

### 5.2 Client → server: `dispatch`

```json
{
  "op": "dispatch",
  "id": "req-uuid-or-counter",
  "path": null,
  "alias": "operator-entry/start",
  "params": {},
  "format": "assistant"
}
```

| Field | Required | Meaning |
|-------|----------|---------|
| `op` | yes | `"dispatch"` |
| `id` | yes | Correlation id for response |
| `path` | no | Same as MCP `path` array |
| `alias` | no | Same as MCP `alias` |
| `params` | no | Same as MCP `params` (body, flow_id, session_id, value, query, …) |
| `format` | no | Default **`assistant`** on this channel |

**Inference rules:** identical to MCP `normalize_assist_dispatch_args` (bare start → operator-entry; `flow_id` → create; `body` → design/publish; `session_id`+`value` → input; etc.).

### 5.3 Server → client: `turn`

```json
{
  "op": "turn",
  "id": "req-uuid-or-counter",
  "payload": {
    "path": ["flows", "coconut-npc", "session", "inst-…"],
    "session_id": "inst-…",
    "status": "waiting",
    "question": "What name do you give?",
    "hint": "Reply with your answer.",
    "choices": [],
    "actions": [{"label": "Send answer", "tool": "palm_assist", "params": {…}}],
    "mutation": { "mutations_allowed": true, … },
    "compose": { … },
    "refs": { … }
  }
}
```

`payload` is exactly (or a strict subset of) what MCP `palm_assist` returns after shaping — **Portal must not depend on MCP tool names** in `actions`; prefer `alias` / `params` that the client can re-dispatch over WS.

**Portal action handling rule:**

- If action has `alias` or `params` suitable for dispatch → send new `dispatch` frame.
- If action only has foreign `tool` like `palm_flows_*` → treat as bug (0.31.2–0.31.3 cleanup); WS should rewrite to assist-shaped actions in shaper for this channel if needed.

### 5.4 Server → client: `error`

```json
{
  "op": "error",
  "id": "req-…",
  "error": {
    "code": "unknown_alias" | "validation" | "internal" | "unauthorized",
    "message": "human readable"
  }
}
```

### 5.5 Optional later: `event` (not MVP)

```json
{
  "op": "event",
  "topic": "session.updated",
  "session_id": "inst-…",
  "payload": { "status": "WAITING_FOR_INPUT" }
}
```

Requires subscription model and runtime hooks — **post 0.32.2**.

### 5.6 Endpoint path (recommendation)

| Path | Purpose |
|------|---------|
| `GET /ws/v1/assist` | Assist chat channel (primary) |
| `GET /v1/surfaces/websocket` | Keep/info for discovery (upgrade from 501 to live status) |

Exact path freeze in ADR.

---

## 6. Portal (client) implications

### 6.1 MVP dogfood UI (before full PWA)

- Single HTML page + minimal JS.
- Connect WS, show `question`, render `choices` as buttons, free-text input for `value`.
- Store `session_id` + `flow_id` from last turn.
- “Action” buttons re-dispatch alias/params.

### 6.2 Portal PWA (later phase)

| Concern | Approach |
|---------|----------|
| Floating panel | CSS fixed / PiP-like shell |
| Installability | `manifest.webmanifest`, service worker optional |
| State | sessionStorage / localStorage for last session |
| Theming | CSS variables; Palm branding optional |
| Offline | Explicit non-goal until protocol stable |

### 6.3 Android (far)

1. WebView hosting Portal.  
2. Native chat UI implementing the same frame schema.  
3. No second Palm backend.

---

## 7. Implementation sketch by phase

### 0.32.1 — Transport MVP

- Replace 501 with connection acceptance **or** document dual-stack.
- Integration test: open WS, hello, close.
- Config: enable flag if needed (`PALM_WS=1`).

### 0.32.2 — Assist channel

- Frame parse/validate (strict ops).
- Wire to shared dispatch with `ServerContext`.
- Dogfood HTML in `examples/` or `docs/` static.
- Tests: dispatch operator-entry start → turn has `question`.

### 0.32.3 — Continuity

- Reconnect with `session_id` resume (inspect then continue).
- Optional server-side connection registry (weak refs).
- Rate limiting / max message size.

### 0.32.4 — Portal shell

- Lightweight chat UI package (location TBD: `portal/` or `examples/portal/`).
- Build story: static files served by Palm server or separate dev server.

### 0.32.5+ — Open field

- Server-push events  
- Cookie session auth  
- Multi-tab presence  
- Android wrapper  
- Align with MCP inventory for “chat surface”  
- Extract dispatch from `runtimes/mcp` to `common/operator` if import edges hurt  

---

## 8. Key Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| **KD-1** | 0.32.0 is **docs + protocol draft** only | Same discipline as 0.30/0.31 foundations |
| **KD-2** | **Assist-first**, not job-stream-first | Portal chat product needs turns, not logs |
| **KD-3** | **Reuse MCP dispatch spine** | One brain; less drift |
| **KD-4** | Default **assistant** format on WS | Human chat |
| **KD-5** | **No new service domain** for Portal | Thin surface |
| **KD-6** | Protocol versioned (`protocol: 1`) | Client evolution |
| **KD-7** | Transport stack **spike then ADR** | Avoid premature Starlette rewrite |
| **KD-8** | Portal is a **client** after dogfood protocol | Protocol > pixels |
| **KD-9** | Open ladder beyond 0.32.4 | Mobile and events without scope freeze |

---

## 9. Alternatives considered

| Alternative | Why not primary |
|-------------|-----------------|
| SSE + REST POST | Two channels; harder than WS for chat |
| Long-poll REST only | Feels laggy for assistant UX |
| GraphQL subscriptions | Heavy; new stack |
| WebRTC data channel | Overkill for JSON chat |
| Put chat logic in Studio frontend only | Couples product to Studio; not embeddable |
| New PortalService with its own session model | Duplicates Assist |

---

## 10. Security & privacy

| Topic | Stance |
|-------|--------|
| Dev open WS | OK with loud docs |
| Production | Require auth before Portal ships broadly |
| Message size | Cap JSON size (e.g. 256KiB) |
| Origin | CORS/origin checks for browser clients |
| Secrets | Never log full mutation tokens; same rules as MCP |

---

## 11. Observability

| Signal | Use |
|--------|-----|
| Connection count | Ops |
| Frames in/out | Debug |
| Dispatch latency | Perf |
| Error codes | Client UX |
| Optional size log | Align with 0.31 inventory mindset |

---

## 12. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Stdlib cannot host WS cleanly | High | Spike early; fall back to ASGI side-car |
| Dispatch lives under `mcp` package | Medium | Allow WS to import; extract later if needed |
| Action buttons reference missing tools | Medium | Assist-shaped actions only on WS shaper |
| Portal scope swallows backend | High | Protocol dogfood before PWA polish |
| Auth deferred too long | Medium | ADR section + production checklist |

---

## 13. Open questions

| # | Question | Lean |
|---|----------|------|
| OQ-1 | Stdlib vs Starlette for WS? | Spike in 0.32.1 |
| OQ-2 | Single port with REST or dual port MVP? | Prefer single if easy |
| OQ-3 | Extract dispatch to `common/operator` in 0.32.2? | Only if imports hurt |
| OQ-4 | Where does Portal live in monorepo? | `examples/portal` first |
| OQ-5 | Should bare WS connection auto-start operator-entry? | Optional client choice |
| OQ-6 | Android track version? | After Portal dogfood, not in 0.32 critical path |

---

## 14. Testing strategy

| Phase | Tests |
|-------|--------|
| 0.32.0 | Doc consistency only |
| 0.32.1 | Connection unit/integration (if feasible without flaky ports) |
| 0.32.2 | Frame round-trip: start scenario → `question` present |
| 0.32.3 | Reconnect with session_id |
| 0.32.4 | Manual dogfood checklist + optional Playwright later |

---

## 15. References

- [VISION-0.32.md](../../VISION-0.32.md)
- [VISION-0.18-ASSIST.md](../../VISION-0.18-ASSIST.md)
- [VISION-0.31.md](../../VISION-0.31.md)
- [ADR-006](../../adr/006-assist-domain.md)
- ARCHITECTURE.md runtimes table
- `WebSocketSurface` stub
- MCP assist dispatch module
- Session product learnings: assist-only dogfood (0.31.2–0.31.3), progressive docs (0.31.3), meta-tool token feedback

---

## Appendix A — Context dump: why this is the right “backend for Portal”

From the 0.30–0.31 operator work:

1. **Assist is already the chat API** — assistant envelopes are the UI model.
2. **Meta-tool efficiency** taught us clients should not load 39 tools; a WS client loads **zero tools** and only a frame schema.
3. **Aliases** (`assist/doctor`, `design/publish`, …) are the right vocabulary for Portal buttons.
4. **Publish + run** works through one meta path — Portal can offer “create flow” later without a design IDE.
5. **Resources (KV, coconut)** already work in flow sessions; Portal just drives sessions.

---

## Appendix B — Sample conversation on WS

```text
C→S  {"op":"dispatch","id":"1","params":{}}
S→C  {"op":"turn","id":"1","payload":{"question":"What would you like…","choices":[…]}}

C→S  {"op":"dispatch","id":"2","params":{"session_id":"inst-a","value":"coconut-npc"}}
S→C  {"op":"turn","id":"2","payload":{"handoff_ready":true,…}}  // or complete design path

C→S  {"op":"dispatch","id":"3","params":{"flow_id":"coconut-npc"}}
S→C  {"op":"turn","id":"3","payload":{"question":"What name do you give?",…}}

C→S  {"op":"dispatch","id":"4","params":{"session_id":"inst-b","flow_id":"coconut-npc","value":"Ada"}}
S→C  {"op":"turn","id":"4","payload":{"question":"… friend, stranger, or trouble?", "choices":[…]}}
```

---

## Appendix C — Mapping MCP → WS for Portal implementers

| MCP | WebSocket |
|-----|-----------|
| Tool `palm_assist` arguments | `dispatch` frame fields |
| Tool result JSON | `turn.payload` |
| `search_tool` / tool list | Unnecessary; use `assist/discover` over WS or static card |
| MCP resources | Optional HTTP GET same URIs; or later `op: "resource"` |
| `PALM_MCP_SURFACE=assist` | Always “assist semantics” on this channel |

*End of design document.*
