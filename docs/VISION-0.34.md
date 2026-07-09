# VISION 0.34 — Assist operator remote (menu + open + chat L0)

**Status:** 0.34.0–0.34.5 shipped  
**Depends on:** 0.33 Assist modularity (tool vs chat, leaf services)  
**Non-goal:** Bot / LLM pilot (deferred). Assist is the remote; Portal/MCP are clients.

---

## Problem

Dogfood showed:

1. **Demo flows** work end-to-end on Portal (auto-start, intro, skip).
2. **Design intents** (`improve-flow`, …) complete triage then dead-end (`handoff_ready` + agent-only hints).
3. **Confirm** steps lack Yes/No chips.
4. **Catalog** is list/discover only — not a navigable menu with search/page/open for *any* flow.

## North star

```text
Human (Portal) / Agent (MCP)
        │
   Assist (operator remote)
     ├── scenarios   curated entry
     ├── sessions    drive instance
     ├── catalog     menu / search / page / open / discover
     ├── present     tool | chat profiles
     └── profiles    continuity (auto-start, intro, design chain)
        │
  Execution · Design · Definitions · System
```

**Assist = remote control + TV guide.**  
No Bot package until menus and open targets are complete.

---

## Ladder

| Step | Deliverable |
|------|-------------|
| **0.34.0** | This vision + STATUS/CHANGELOG |
| **0.34.1** | Chat L0: design auto-start → design-entry; handoff CTAs; confirm Yes/No |
| **0.34.2** | Menu protocol: `assist/menu`, search, cursor page, actionable items |
| **0.34.3** | `assist/open` — flow / scenario / session / alias; wire grammar + shape + aliases |
| **0.34.4** | Portal menu shell (Menu, search, open tokens); Browse CTAs; waiting labels |
| **0.34.5** | Typeahead debounce; waiting resume chips; open session polish |

## Menu turn shape (chat + tool)

```json
{
  "status": "ok",
  "question": "Flows (page 1)",
  "hint": "Pick a row or search.",
  "choices": [{"n": 1, "label": "Todo Builder", "value": "open:flow:todo-builder"}],
  "input": {
    "widget": "menu",
    "kind": "menu",
    "section": "flows",
    "query": "",
    "cursor": "0",
    "next_cursor": "12",
    "has_more": true,
    "items": [{"id": "todo-builder", "kind": "flow", "label": "…", "open": {"kind": "flow", "id": "todo-builder"}}]
  },
  "actions": [
    {"label": "Show more", "alias": "assist/menu", "params": {"section": "flows", "cursor": "12"}},
    {"label": "Search", "alias": "assist/menu", "params": {"section": "flows"}}
  ]
}
```

Open:

```text
assist/open  params: {kind: flow|scenario|session|alias, id: "…"}
```

## Continuity (chat profile)

| Intent class | Auto behavior |
|--------------|----------------|
| Demo flows (`todo-builder`, …) | create flow session (0.32+) |
| Design (`create-flow`, `improve-flow`, `propose-resource`) | start **design-entry** + pre-answer intent |
| Confirm widget | always Yes/No choices |

Opt out: `auto_start=false`.

## Principles

1. **One brain** — path/alias/params only.  
2. **Catalog owns navigation data**; present owns chips; Portal only paints.  
3. **Small files** under `assist/catalog/` and `profiles/`.  
4. **Tool profile** stays lean (no input schema by default).  
5. **No Bot** in 0.34.

## Success criteria

- Portal: Improve Flow → lands in design-entry (name/base prompt), not “Finished. Answers: intent=…”.  
- `palm_assist(alias="assist/menu", params={section:"flows"})` returns paged choices.  
- `assist/open` starts any listed flow.  
- Confirm steps expose Yes/No without Portal inventing them.
