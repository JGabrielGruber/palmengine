---
name: palm
description: Palm MCP integration — flows, sessions, design (create/improve flows), operator-entry, palm_assist, palm:// resources, tool description patterns, and wizard driving. Use when the user mentions Palm, MCP tools, starting flows, designing flows, session state, or updating agent/MCP descriptions.
---

# Palm Skill

Portable copy: `docs/skills/palm/` (adopt manually into any agent host — see `README.md` in this folder).

You operate Palm through MCP — **prefer `palm_assist` only** (required when `PALM_MCP_SURFACE=assist`).

## Progressive context (0.31.3) — do not preload everything

| Layer | When | Resource |
|-------|------|----------|
| **L0** | Always (tool description) | Short examples on `palm_assist` |
| **L1** | Session start / first stuck | **`palm://agent/card`** |
| **L2** | Deep dive only | `palm://agent/guide`, `palm://agent/skill`, `references/*` |

**Do not** load full guide + all references unless needed.

## Session ≠ instance (0.58 law)

| Term | Meaning |
|------|---------|
| **`session_id`** | System subject only (`sess-…` / `sess-svc-…`). Outside owner; multi-instance capable. |
| **`instance_id`** | Product continue handle (one run / wizard walk). |
| **Path segment** | Prefer **`instance`** in product paths. Legacy segment `session` may still parse. |
| **System journey** | `system/session/{id}/…` stays system (not renamed to instance). |
| **Product door** | **SessionService** / **BoundSurface** via kit `resolve_session_service`. |
| **Continue** | Wait plane only. No dual-own. Active = focus among owned instances. |

Prefer `instance_id` for continue params. Legacy `session_id` in tool params may fill the continue handle when the value is **not** a system `sess-…` id.

Detail: `references/session-management.md` · map [PALM.md](../../../PALM.md) session plane · [VISION-0.58](../../vision/closed/VISION-0.58.md).

## Core principles

- **Stateful** — re-inspect after every input; follow returned `question` / `actions`.
- **Start** with `palm_assist()` or `params={flow_id}`.
- **Plain strings** — `value` / `input` as yes, choice slugs, text.
- **Publish** — `palm_assist(params={body})` or `alias=design/publish` (prefer one-shot; not multi-step design tools unless inspecting impact).
- **Mutation guard** — respect `mutations_allowed` / `confirm_step` / `input_token` when present.

## Reference resources (load when relevant)

| Topic | MCP resource |
|-------|----------------|
| **Operator card (start here)** | `palm://agent/card` |
| Full guide | `palm://agent/guide` |
| This skill (full) | `palm://agent/skill` |
| Design playbook | `palm://agent/references/design-flows` |
| Session driving | `palm://agent/references/session-management` |
| Common flows | `palm://agent/references/common-flows` |
| Branching | `palm://agent/references/branching-flows` |
| Routes | `palm://assist/routes` |

## Quick commands (`palm_assist` only)

| Action | Call |
|--------|------|
| Fresh start | `palm_assist()` |
| Discover | `alias=assist/discover` + optional `query` |
| Run a flow | `params={flow_id: "coconut-npc"}` then `value` |
| Continue | `params={instance_id, flow_id, value}` (legacy `session_id` ok if not `sess-…`) |
| List flows | `alias=assist/catalog/flows` |
| Waiting | `alias=assist/catalog/waiting` |
| Doctor | `alias=assist/doctor` |
| Resume resource | `alias=flows/instance-resume` (legacy `flows/session-resume`) + instance_id, flow_id |
| Publish flow | `params={body: {…}}` or `alias=design/publish` |
| Publish resource | `alias=design/publish-resource` |
| System session view | path/alias under `system/session/{session_id}` |

## When editing Palm MCP code

Follow `references/mcp-patterns.md` and use `palm.runtimes.mcp.descriptions.tool_description()` for new or updated tool docstrings.
