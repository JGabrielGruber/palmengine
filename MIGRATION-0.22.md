# Migration — 0.22.0 (Agent skill + MCP operator docs)

**From:** 0.21.x · **Theme:** Portable agent skill, MCP resource references, operator guide split, Docker stack docs.

No breaking API changes for flows, REST, or existing MCP tools.

---

## What changed

### Agent documentation split

| Before (0.21) | After (0.22) |
|---------------|--------------|
| `docs/llms.txt` served as `palm://agent/guide` | **`docs/mcp.txt`** is the default operator guide (`palm://agent/guide`) |
| Skill lived only in suggestions / Grok | **`docs/skills/palm/`** — portable skill + references |
| — | **`palm://agent/skill`** and **`palm://agent/references/*`** MCP resources |

`docs/llms.txt` remains — broader project context (architecture, extension patterns).

### New MCP resources

| URI | Source |
|-----|--------|
| `palm://agent/skill` | `docs/skills/palm/SKILL.md` |
| `palm://agent/references/agent-guide` | Mental model + rules |
| `palm://agent/references/mcp-patterns` | Tool description patterns |
| `palm://agent/references/session-management` | Session driving |
| `palm://agent/references/common-flows` | Todo-builder, approval, etc. |

### New / updated env vars

| Variable | Default (this repo) | Purpose |
|----------|---------------------|---------|
| `PALM_LLMS_TXT` | `docs/mcp.txt` | `palm://agent/guide` |
| `PALM_SKILL_DIR` | `docs/skills/palm` | Skill + reference resources |

Docker image and compose set both (see [docs/DOCKER.md](docs/DOCKER.md)).

### MCP tool descriptions

Key tools (`palm_assist`, `palm_flows_session`, …) now lead with `call_connected_tool(tool_name="palm___…")` via `palm.runtimes.mcp.descriptions.tool_description()`.

---

## Agent config updates

### Grok Build

[`.grok/config.toml`](.grok/config.toml) — `PALM_LLMS_TXT=docs/mcp.txt`, skill at `.grok/skills/palm/` (mirrors `docs/skills/palm/`).

### Cursor / Claude / custom

1. MCP stdio: `PALM_MCP_IN_PROCESS=1 PALM_LLMS_TXT=docs/mcp.txt PALM_SKILL_DIR=docs/skills/palm palm-mcp`
2. Read `palm://agent/guide` + `palm://agent/skill` at session start.
3. Or copy [`docs/skills/palm/SKILL.md`](docs/skills/palm/SKILL.md) into project rules.

### Docker + remote MCP

```bash
PALM_MCP_IN_PROCESS=0 PALM_BASE_URL=http://127.0.0.1:8080 palm-mcp
```

---

## Contributor checklist

- [ ] Edit skill under **`docs/skills/palm/`** only; run `just docs-check` (syncs `.grok/` + bundled `data/skills/palm/`).
- [ ] Edit operator guide in **`docs/mcp.txt`**; sync bundled `src/palm/runtimes/mcp/data/mcp.txt`.
- [ ] New MCP tools: use `tool_description()` — see `docs/skills/palm/references/mcp-patterns.md`.

---

## Still deferred (not 0.22)

- `palm-compose-guide` scenario
- Process handoff extensions
- `create_params` mapping
- WebSocket assist stream

See [docs/superpowers/specs/2026-07-01-assistant-weak-llm-improvements-design.md](docs/superpowers/specs/2026-07-01-assistant-weak-llm-improvements-design.md).