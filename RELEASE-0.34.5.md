# Release checklist — 0.34.5 (bundled: Assist modularity + operator remote)

**Theme:** Execution-shaped **Assist** (tool vs chat profiles, small modules) plus the **operator remote** — menu, open any flow, design chat L0, Portal menu shell. No Bot package.

**PyPI version:** **0.34.5**  
**Previous cut:** **0.32.10**  
**Bundles:** 0.33.0–0.33.3 · 0.34.0–0.34.5 (+ open first-turn fix)

| Track | Docs |
|-------|------|
| Assist modularity | [VISION-0.33](docs/VISION-0.33.md) |
| Operator remote | [VISION-0.34](docs/VISION-0.34.md) |
| Prior WS/Portal | [VISION-0.32](docs/VISION-0.32.md) · [RELEASE-0.32.10](RELEASE-0.32.10.md) |

## What lands (summary)

### 0.33 — Assist modularity
- `present/` presentation pipeline; `profiles/` tool vs chat
- Façade leafs: `scenarios` · `sessions` · `catalog`
- Chat policy (auto-start demos, intro continue) out of WebSocket transport
- MCP `dispatch` split into normalize / operator / shape/*

### 0.34 — Operator remote (no Bot)
- Design intents auto-start **design-entry**; confirm **Yes/No** chips
- `assist/menu` browse / search / page; `assist/open` + `open:kind:id`
- Portal: **Menu**, typeahead debounce, Browse all flows, Resume waiting chips
- Open flow re-inspects first turn (question + input, not raw `WAITING_FOR_INPUT`)

## Pre-ship

- [x] Version **0.34.5**
- [x] CHANGELOG `[0.34.5]`
- [x] RELEASE checklist
- [ ] Tag `v0.34.5`
- [ ] Push + GitHub release
- [ ] Optional PyPI: `just publish`

## Verify

```bash
uv run pytest \
  tests/test_assist_menu_open.py \
  tests/test_assist_service.py \
  tests/test_websocket_assist_transport.py \
  tests/test_assistant_view.py \
  tests/test_palm_assist_tool.py \
  tests/test_assist_complete_paths.py \
  -q

# Manual dogfood
just palm-server
# http://127.0.0.1:8080/portal/?open=1
# Menu → Flows → open a flow → first prompt (not blank)
```

## Tag

```bash
git tag -a v0.34.5 -m "Palm Engine 0.34.5 — Assist modularity and operator remote"
```

## Upgrade notes

- **Non-breaking** for MCP / REST / existing flows.
- New aliases: `assist/menu`, `assist/open` (plus existing assist catalog aliases).
- Chat profile continuity (auto-start design/demo) is default on WebSocket; opt out with `auto_start=false`.
- Portal remains **dogfood** (open auth, not production PWA).
- Hello / `palm.__version__` now report **0.34.5**.
