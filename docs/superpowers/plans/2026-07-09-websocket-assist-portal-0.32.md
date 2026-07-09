# Plan: WebSocket Assist & Portal Backend (0.32) — open-ended

**Vision:** [docs/VISION-0.32.md](../../VISION-0.32.md)  
**Design:** [2026-07-09-websocket-assist-portal-design.md](../specs/2026-07-09-websocket-assist-portal-design.md)  
**Status:** 0.32.0–0.32.3 ✅ · 0.32.4 open  

Delivery: commit when good enough. **Insert phases freely** if dogfood demands it.

---

## Phase 0.32.0 — Foundation (this commit)

| Task | Done when |
|------|-----------|
| VISION-0.32 | Product arc MCP → WS → Portal → Android |
| Design spec | Protocol draft, KD table, transport options, context dump |
| This plan | Ladder + verify steps |
| STATUS / AGENTS / CHANGELOG | Point at 0.32 |

**Acceptance:** no runtime behavior change required. Stub WS may remain 501 until 0.32.1.

---

## Phase 0.32.1 — Transport MVP

**Intent:** Accept real WebSocket connections.

| Work item | Notes |
|-----------|--------|
| Spike stdlib upgrade vs Starlette sidecar | Time-box; document winner in ADR draft |
| Live endpoint | Prefer `/ws/v1/assist` |
| Update `WebSocketSurface` info route | 200 + protocol status instead of 501 |
| Config | Optional `PALM_WS_ENABLE=1` |
| Test | Connect / hello / close |

**Acceptance:** `websocat` or browser can open WS and receive `hello`.

---

## Phase 0.32.2 — Assist channel

**Intent:** Chat turns via dispatch.

| Work item | Notes |
|-----------|--------|
| Parse `dispatch` / emit `turn` / `error` | protocol v1 |
| Call shared dispatch with ServerContext | Reuse MCP helpers |
| Default format=assistant | Portal-ready |
| Rewrite foreign tool actions if needed | assist-shaped aliases |
| Dogfood HTML | Minimal chat page |
| Tests | operator-entry start → question |

**Acceptance:** Full operator-entry or coconut-npc turn loop over WS without REST polling.

---

## Phase 0.32.3 — Continuity

| Work item | Notes |
|-----------|--------|
| Reconnect + session_id | Inspect then continue |
| Message size limits | DoS hygiene |
| Optional bearer on upgrade | Dev still open |
| Connection metrics | Optional |

---

## Phase 0.32.4 — Portal dogfood shell

| Work item | Notes |
|-----------|--------|
| Lightweight UI | `examples/portal/` or similar |
| Floating panel CSS | Product feel without full app |
| manifest (optional) | PWA install later |
| Docs | How to run Portal against local server |

**Not required:** polished branding, offline SW, store listing.

---

## Phase 0.32.5+ — Open field

Candidates (unordered):

- Server-push `event` frames  
- Cookie auth for same-origin Portal  
- Multi-tab session coordination  
- Android WebView shell  
- Extract dispatch to `common/operator`  
- Job/wizard event bus (historical “stream everything”)  
- Align Explorer assist workspace with WS (optional)  
- Production hardening checklist  

---

## How to verify (future)

```bash
# After 0.32.1+
websocat ws://127.0.0.1:8080/ws/v1/assist
# send hello / dispatch JSON lines

# After 0.32.2
# open dogfood HTML, run operator-entry
```

---

## Risks & rollback

| Risk | Rollback |
|------|----------|
| Transport choice wrong | Keep protocol; swap transport adapter |
| Protocol churn | Bump `protocol` integer; support N-1 briefly |
| Portal overbuilt | Freeze frames; simplify UI |

---

## References

Design KD-1–KD-9 · VISION-0.32 · MCP assist dispatch · WebSocketSurface stub
