# Agent Skills (portable)

Skills in this folder are **versioned, platform-neutral** instructions for coding agents working with Palm. Copy or adapt them into any agent host — Cursor rules, Claude `CLAUDE.md`, custom MCP clients, etc.

| Skill | Path | Purpose |
|-------|------|---------|
| **palm** | [`palm/SKILL.md`](palm/SKILL.md) | MCP operator loop, session driving, tool description patterns |

**Related docs (not skills):**

| Doc | Purpose |
|-----|---------|
| [`docs/mcp.txt`](../mcp.txt) | MCP operator guide → `palm://agent/guide` |
| `palm://agent/skill` | Portable agent skill (MCP resource) |
| `palm://agent/references/*` | Skill references (session, patterns, flows) |
| [`docs/llms.txt`](../llms.txt) | Broader project / architecture context |
| [`docs/MCP.md`](../MCP.md) | Full tool inventory and workflows |

## Grok Build (this repo)

Grok auto-loads from `.grok/skills/palm/`, kept in sync with `docs/skills/palm/` via `just docs-check`.

## Other agents

See [`palm/README.md`](palm/README.md) for manual adoption steps.