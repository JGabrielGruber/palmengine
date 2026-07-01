# Release checklist — 0.21.7 (Weak-LLM MCP hotfixes)

**Theme:** MCP boot fix, null param coercion, human-first `palm_assist` defaults.

**Builds on:** [0.21.6](RELEASE-0.21.6.md) · **Plan:** [docs/superpowers/plans/2026-07-01-0.21.7-weak-llm-mcp.md](docs/superpowers/plans/2026-07-01-0.21.7-weak-llm-mcp.md)

## Pre-ship

- [x] `shape_flow_session_view` in `palm/common/operator/flow_session_view.py` (no REST → MCP import)
- [x] `palm_assist` null `action`/`format` coercion
- [x] Bare `palm_assist()` → `operator-entry/start`; session continuation inference
- [x] `MIGRATION-0.21.md` § 0.21.7 weak-LLM defaults
- [x] `docs/MCP.md` · `docs/llms.txt` · `AGENTS.md` · `STATUS.md`
- [x] Version **0.21.7** · `just docs-check` · `just guard-common`

## Verify

```bash
uv run pytest tests/test_palm_assist_tool.py tests/test_flows_assistant_format.py -v
just docs-check
just guard-common
```

## Tag

```bash
git tag -a v0.21.7 -m "Palm Engine 0.21.7 — weak-LLM MCP hotfixes"
```