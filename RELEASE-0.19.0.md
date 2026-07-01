# Release checklist — 0.19.0

**Theme:** Stable `palm_assist` MCP dispatch proxy + contributor path aliases.

## Pre-ship

- [x] `palm/runtimes/mcp/assist/dispatch.py` — path resolver + service delegation
- [x] `palm/runtimes/mcp/assist/tools.py` — `palm_assist` tool
- [x] MCP resource `palm://assist/routes`
- [x] `assist_dispatch` on in-process + REST backends
- [x] Contributor `mcp_aliases` on `AssistContributor`
- [x] `operator-entry/start` and `operator-entry/handoff` aliases
- [x] `MIGRATION-0.19.md`
- [x] Version **0.19.0** · `just docs-check` · `just guard-common`

## Verify

```bash
uv run pytest tests/test_assist_registry.py tests/test_assist_service.py \
  tests/test_assist_service_routes.py tests/test_operator_entry_flow.py \
  tests/test_palm_assist_tool.py tests/test_mcp_in_process.py -v
just docs-check
just guard-common
rg 'palm/services/palm' src/   # expect no matches
```

## Tag

```bash
git commit -m "feat(0.19.0): palm_assist stable MCP dispatch proxy"
git tag -a v0.19.0 -m "Palm Engine 0.19.0 — palm_assist MCP proxy"
```