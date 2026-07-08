# Release checklist — 0.31.5 (bundled: post-0.30.7 MCP meta-surface)

**Theme:** Token-efficient MCP for weak LLMs — **progressive disclosure**, **`PALM_MCP_SURFACE=assist`**, assist-complete aliases, and progressive docs (`palm://agent/card`).

**PyPI version:** **0.31.5**  
**Previous cut:** **0.30.7**  
**Bundles:** 0.30.8 · 0.31.0–0.31.4

| Track | Docs |
|-------|------|
| MCP meta-surface | [VISION-0.31](docs/VISION-0.31.md) · [design](docs/superpowers/specs/2026-07-08-mcp-meta-surface-design.md) · [plan](docs/superpowers/plans/2026-07-08-mcp-meta-surface-0.31.md) |
| Assist design entry | [VISION-0.30](docs/VISION-0.30.md) · [MIGRATION-0.30](MIGRATION-0.30.md) |

## What lands (summary)

### 0.30.8 — Terminal polish
- Complete turns: “Finished. Answers: …” blurb
- Waiting: single **Send answer** CTA → `palm_assist`
- Complete: **Run again** + operator-entry

### 0.31.0–0.31.4 — Meta-surface
- Vision + open ladder for progressive disclosure
- **`PALM_MCP_SURFACE`**: `full` (default) · **`assist`** (1 tool) · `core` · `experimental`
- **`just mcp-inventory`** / `scripts/mcp_catalog_inventory.py`
- Assist-complete aliases: doctor, catalog flows/waiting, session-resume, design/publish
- **`palm://agent/card`** L1 guide; short L0 tool description
- **`assist/discover`** query routes without a second MCP tool
- AGENTS/README/llms/skill refreshed for assist-first

## Pre-ship

- [x] Version **0.31.5**
- [x] CHANGELOG `[0.31.5]`
- [x] RELEASE checklist
- [ ] Tag `v0.31.5`
- [ ] Push + GitHub release
- [ ] Optional PyPI: `just publish`

## Verify

```bash
uv run --extra mcp pytest \
  tests/test_mcp_surface.py \
  tests/test_assist_complete_paths.py \
  tests/test_assistant_view.py \
  tests/test_palm_assist_tool.py \
  tests/test_mcp_agent_skill_resources.py \
  tests/test_mcp_design_in_process.py \
  -q

just mcp-inventory surface=assist
just mcp-inventory surface=full
```

## Tag

```bash
git tag -a v0.31.5 -m "Palm Engine 0.31.5 — MCP meta-surface and progressive disclosure"
```
