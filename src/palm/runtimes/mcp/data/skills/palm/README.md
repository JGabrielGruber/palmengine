# Palm Agent Skill — Manual Adoption

Portable skill for any coding agent that uses Palm MCP. Canonical files live in this directory.

## What to load

1. **`palm://agent/guide`** — operator protocol (`docs/mcp.txt`).
2. **`palm://agent/skill`** — core skill (this folder's `SKILL.md`).
3. **`palm://agent/references/*`** — on-demand references (session management, design flows, MCP patterns, common flows).
4. **`docs/MCP.md`** — full tool inventory when you need specifics.

On-disk copies in this folder are for manual paste into non-MCP agent hosts.

## Adoption by platform

### Cursor / Claude Desktop (MCP stdio)

```bash
uv sync --extra mcp
PALM_MCP_IN_PROCESS=1 PALM_LLMS_TXT=docs/mcp.txt uv run --extra mcp palm-mcp
```

Add MCP server in IDE config, then paste `SKILL.md` into project rules or `AGENTS.md`.

### Claude Code / custom hosts

- Copy `SKILL.md` frontmatter + body into a project skill or `CLAUDE.md` section.
- Point `PALM_LLMS_TXT` at `docs/mcp.txt` for `palm://agent/guide`.

### Grok Build

No manual step — `.grok/skills/palm/` mirrors this folder (synced by `docs-check`).

### Generic / roll-your-own

At minimum, instruct the agent to:

1. Read `palm://agent/guide` (or `docs/mcp.txt`) before operating flows.
2. Start with `palm_assist()` unless continuing a known `session_id`.
3. Re-inspect with `format=assistant` after every wizard input.

## Maintaining this skill

Edit files under **`docs/skills/palm/`** only. Run `just docs-check` to verify `.grok/skills/palm/` stays in sync.