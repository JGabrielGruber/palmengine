# VISION 0.33 — Assist modularity (tool vs chat, small files)

**Status:** in progress (0.33.0–0.33.1 scaffolded)  
**Depends on:** 0.32 WebSocket Assist / Portal  
**Goal:** Split Assist like Execution — façade + subdomains + **tool** / **chat** profiles. Prefer many small modules over god files.

---

## Principles

1. **Execution-shaped** — thin façade, leaf services own work.
2. **One brain** — same `path` / `alias` / `params` → domain result.
3. **Two profiles** — `tool` (MCP/agents) vs `chat` (Portal/WS humans) only change **presentation + policy**.
4. **Small files** — target ≤ ~250 LOC per module; split when a concern grows.
5. **Runtimes stay thin** — MCP/WS map transport → service; no product policy in Portal JS or WS forever.

---

## Package map (`palm/services/assist/`)

```text
assist/
  __init__.py                 # AssistService, AssistSession
  service.py                  # THIN façade (like ExecutionService)
  grammar.py                  # path parse (shared)
  registry.py                 # scenarios, aliases, enrichers (may split later)
  schemas.py                  # AssistSessionContext
  session.py                  # AssistSession handle (thin)

  scenarios/                  # subdomain: operator / design entry
    __init__.py
    service.py                # start / describe / inspect catalog

  sessions/                   # subdomain: drive an instance
    __init__.py
    service.py                # session lookup, input/back/resume/cancel
    handoff.py                # handoff resolution

  catalog/                    # subdomain: discover / doctor / lists
    __init__.py
    service.py                # doctor, list_flows, waiting, discover

  present/                    # presentation pipeline (shared)
    __init__.py
    format.py                 # resolve_view_format, registration
    pipeline.py               # build_assistant_view entry
    flatten.py                # flat inspect + snapshot merge
    input_schema.py           # Portal input widgets
    humanize.py               # question / hint / choices / compose / terminal
    actions.py                # default + session + resource actions
    design_actions.py         # design CTAs / prioritize
    status.py                 # human_status helpers

  profiles/                   # tool vs chat
    __init__.py
    base.py                   # AssistProfile enum + RenderOptions
    tool.py                   # lean turns, no input schema default
    chat.py                   # input schema, action filter, auto-policy hooks
    policy.py                 # auto_start, auto_continue_intro (moved from WS over time)

  _params.py                  # include_input_schema, wizard body strip
  _view_meta.py               # flow_id / scenario / answers from inspect
```

### Runtime layout (next steps, same spirit)

```text
runtimes/mcp/assist/
  dispatch.py                 # thin: normalize → path → service → present(tool)
  shape/                      # split from mega-dispatch
    session.py
    catalog.py
    design.py
    flow_create.py
  routes.py
  tools.py

runtimes/server/surfaces/websocket/
  session.py                  # frames + bind only (policy → profiles/chat)
  policy_bridge.py            # temporary until policy fully in assist.profiles
  static/                     # portal dogfood (UI only)
```

---

## Profiles

| Profile | Consumers | Defaults |
|---------|-----------|----------|
| **tool** | MCP `palm_assist`, powertool | `include_input_schema=False`, full agent actions |
| **chat** | WS Portal, human REST | `include_input_schema=True`, filtered actions, auto-start / intro |

```python
assist.dispatch(path, params, profile="chat")  # explicit later
# today: include_input_schema flag + WS-side policy → migrate into profile
```

---

## Migration ladder

| Step | Work | Status |
|------|------|--------|
| 0.33.0 | File map + VISION; split `present/` from `views.py` | ✅ |
| 0.33.1 | Façade leafs: scenarios / sessions / catalog | ✅ |
| 0.33.2 | Move chat auto-policy out of WS into `profiles/` | ✅ |
| 0.33.3 | Split MCP `dispatch` into `shape/*` | |
| 0.33.4 | Optional Bot façade only if product needs persona/LLM | optional |

**Compat:** `palm.services.assist.views` re-exports present public API.

---

## Non-goals

- New Bot service before Assist is modular
- Second dispatch language for chat
- Putting LLM prompts in core or websocket transport

---

## Success metrics

- No single assist file ≫ 300 LOC without a clear reason
- WS session.py loses product auto-policy
- MCP dispatch.py under ~300 LOC after shape split
- Tests unchanged at import surface (`views`, `AssistService`, registry)
