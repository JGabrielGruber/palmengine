---
name: palm
description: Palm MCP integration — flows, sessions, operator-entry, palm_assist, palm:// resources, tool description patterns, and wizard driving (todo-builder, approval, collection steps). Use when the user mentions Palm, MCP tools, starting flows, session state, or updating agent/MCP descriptions.
---

# Palm Skill

Portable copy: `docs/skills/palm/` (adopt manually into any agent host — see `README.md` in this folder).

You operate Palm (the connected workflow engine) through MCP — primarily `palm_assist` and domain tools via `CallMcpTool` / `call_connected_tool`.

## Load context first

1. Read MCP resource `palm://agent/guide` (served from `docs/mcp.txt`).
2. For full project architecture → `docs/llms.txt`.
3. For tool inventory and workflows → `docs/MCP.md`.

## Core principles

- **Stateful session machine** — never guess state; re-inspect after every input.
- **Start interactive work** with `palm_assist()` or `palm_assist(alias="operator-entry/start")`.
- **Assistant view for humans** — `format=assistant` on inspect and assist paths.
- **Plain strings** — `input="yes"`, choice slugs, text (not JSON answer blobs).
- **Read vs write** — `palm://…` resources for catalogs; tools for create/input/resume.

## Reference resources (load when relevant)

| Topic | MCP resource |
|-------|----------------|
| This skill (full) | `palm://agent/skill` |
| Mental model + rules | `palm://agent/references/agent-guide` |
| Updating MCP tool docstrings | `palm://agent/references/mcp-patterns` |
| Session driving | `palm://agent/references/session-management` |
| Common flows | `palm://agent/references/common-flows` |

On-disk copies (for manual adoption): `docs/skills/palm/references/`.

## Operator loop

```
definitions → create session → inspect → input → wait on children → resume
```

## Quick commands

| Action | Call |
|--------|------|
| Fresh start | `palm_assist()` |
| List flows | `palm_flows_list` |
| Inspect session | `palm_flows_session(session_id, format="assistant")` |
| Continue session | `palm_assist(params={session_id, flow_id, value})` |
| Health | `palm_system_doctor` |
| Routes catalog | read `palm://assist/routes` |

## When editing Palm MCP code

Follow `references/mcp-patterns.md` and use `palm.runtimes.mcp.descriptions.tool_description()` for new or updated tool docstrings.