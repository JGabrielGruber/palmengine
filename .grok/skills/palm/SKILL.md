---
name: palm
description: Palm MCP integration — flows, sessions, design (create/improve flows), operator-entry, palm_assist, palm:// resources, tool description patterns, and wizard driving. Use when the user mentions Palm, MCP tools, starting flows, designing flows, session state, or updating agent/MCP descriptions.
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
- **Catalog writes (0.25+)** — create or change flow definitions with `palm_design_*` (propose → impact → commit). Do **not** use `palm_definitions_*` create/update unless an integrator doc requires it. Load `palm://agent/references/design-flows` first.
- **Mutation guard (0.22.1+)** — check `mutation.mutations_allowed` on every inspect; never send `value`/`input` when false; never auto-confirm at `mutation.confirm_step`.
- **input_token (0.23.0+)** — when `PALM_MCP_REQUIRE_INPUT_TOKEN=1`, pass `mutation.input_token` with every write; re-inspect after each input.
- **inspect-only (0.23.1+)** — use `operator-entry/inspect` for read-only catalog; menu item 3 stays at catalog until `exit`, never auto-confirms summary.

## Reference resources (load when relevant)

| Topic | MCP resource |
|-------|----------------|
| This skill (full) | `palm://agent/skill` |
| Mental model + rules | `palm://agent/references/agent-guide` |
| Updating MCP tool docstrings | `palm://agent/references/mcp-patterns` |
| Session driving | `palm://agent/references/session-management` |
| Common flows | `palm://agent/references/common-flows` |
| Create/improve flows | `palm://agent/references/design-flows` |
| Branching / hub menus | `palm://agent/references/branching-flows` |

On-disk copies (for manual adoption): `docs/skills/palm/references/`.

## Operator loop

```
design (optional) → create session → inspect → input → wait on children → resume
```

**Design loop** (when user asks to create or change a flow): `palm_design_propose_flow` → `palm_design_impact` → `palm_design_commit` → `palm_flows_describe` to verify. See `palm://agent/references/design-flows`.

## Quick commands

| Action | Call |
|--------|------|
| Fresh start | `palm_assist()` |
| List flows | `palm_flows_list` |
| Inspect session | `palm_flows_session(session_id, format="assistant")` |
| Continue session | `palm_assist(params={session_id, flow_id, value})` |
| Health | `palm_system_doctor` |
| Routes catalog | read `palm://assist/routes` |
| Propose flow | `palm_design_propose_flow(body={...})` |
| Publish flow | `palm_design_impact` → `palm_design_commit` |
| Propose resource | `palm_design_propose_resource(body={...})` |
| Run custom flow | `palm_flows_create_session(flow_id="my-flow")` |

## When editing Palm MCP code

Follow `references/mcp-patterns.md` and use `palm.runtimes.mcp.descriptions.tool_description()` for new or updated tool docstrings.