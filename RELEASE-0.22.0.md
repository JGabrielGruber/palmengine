# Release checklist — 0.22.0 (Agent skill + Docker stack)

**Theme:** Portable agent skill as MCP resources, operator guide split (`docs/mcp.txt`), Docker documentation, weak-LLM tool descriptions.

**Builds on:** [0.21.12](RELEASE-0.21.12.md) · **Migration:** [MIGRATION-0.22.md](MIGRATION-0.22.md)

## Pre-ship

- [x] `docs/mcp.txt` — focused MCP operator guide (`palm://agent/guide`)
- [x] `docs/skills/palm/` — portable skill + references
- [x] MCP resources — `palm://agent/skill`, `palm://agent/references/*`
- [x] `palm.runtimes.mcp.descriptions.tool_description()` — enriched key tool docstrings
- [x] `docs/DOCKER.md` — compose stack, volumes, MCP against container, troubleshooting
- [x] Docker — `PALM_SKILL_DIR`, `PALM_LLMS_TXT` in image + compose
- [x] `just docs-check` — bundled mcp.txt, skill assets, Grok mirror sync
- [x] Version **0.22.0**

## Verify

```bash
just docs-check
just guard-common
uv run pytest tests/test_mcp_agent_guide.py tests/test_mcp_agent_skill_resources.py \
  tests/test_mcp_agent_assets.py tests/test_mcp_descriptions.py tests/test_mcp_in_process.py -v
just docker-build
just docker-up
curl -sf http://127.0.0.1:8080/health
just docker-down
```

## Tag

```bash
git tag -a v0.22.0 -m "Palm Engine 0.22.0 — agent skill MCP resources, operator guide split, Docker docs"
```