# Release checklist — 0.32.10 (bundled: WebSocket Assist + Portal)

**Theme:** Real-time **human** Assist transport (WebSocket) over the same meta-dispatch spine as MCP, plus a **Portal dogfood** chat shell for floating UI / future PWA.

**PyPI version:** **0.32.10**  
**Previous cut:** **0.31.5**  
**Bundles:** 0.32.0 · 0.32.1 · 0.32.2 · 0.32.3 · 0.32.4 · 0.32.5 · 0.32.6 · 0.32.7 · 0.32.8 · 0.32.9 · 0.32.10

| Track | Docs |
|-------|------|
| WebSocket + Portal | [VISION-0.32](docs/VISION-0.32.md) · [design](docs/superpowers/specs/2026-07-09-websocket-assist-portal-design.md) · [plan](docs/superpowers/plans/2026-07-09-websocket-assist-portal-0.32.md) |
| Prior MCP surface | [VISION-0.31](docs/VISION-0.31.md) · [RELEASE-0.31.5](RELEASE-0.31.5.md) |

## What lands (summary)

### Transport (0.32.0–0.32.3)
- Vision + protocol for Assist-first WebSocket (no new service domain)
- Pure-Python RFC6455 on stdlib HTTP: `GET /ws/v1/assist`
- Ops: `hello`, `ping`/`pong`, `dispatch` → `turn`, `bind`
- Portal `input` schema on WS only; MCP omits for tokens

### Portal dogfood (0.32.4–0.32.10)
- `GET /portal/` FAB chat shell
- Auto-open operator-entry; auto-start demo flows; intro auto-continue
- Optional **Skip**; correct flow bind after handoff
- Split intro/menu bubbles; themed scroll; pending indicator

## Pre-ship

- [x] Version **0.32.10**
- [x] CHANGELOG `[0.32.10]`
- [x] RELEASE checklist
- [ ] Tag `v0.32.10`
- [ ] Push + GitHub release
- [ ] Optional PyPI: `just publish`

## Verify

```bash
uv run pytest \
  tests/test_websocket_assist_transport.py \
  tests/test_assist_service.py \
  tests/test_assistant_view.py \
  tests/test_palm_assist_tool.py \
  tests/test_operator_entry_inspect_only.py \
  -q

# Manual dogfood
just palm-server
# http://127.0.0.1:8080/portal/?open=1
# websocat ws://127.0.0.1:8080/ws/v1/assist
```

## Tag

```bash
git tag -a v0.32.10 -m "Palm Engine 0.32.10 — WebSocket Assist and Portal dogfood"
```

## Upgrade notes

- **Non-breaking** for MCP/REST clients; WS surface goes from placeholder → live.
- MCP still defaults to no `input` schema; set `include_input_schema` only where needed (WS does this automatically).
- Portal is **dogfood**, not production auth/PWA.
