# Release checklist — 0.21.12 (Weak-LLM MCP ergonomics)

**Theme:** Bundled 0.21.10–0.21.12 — unified `palm_assist` flows, edit shortcuts, conversation replay.

**Builds on:** [0.21.9](RELEASE-0.21.9.md) · **Plan:** [docs/superpowers/plans/2026-07-01-0.21.7-weak-llm-mcp.md](docs/superpowers/plans/2026-07-01-0.21.7-weak-llm-mcp.md)

## Pre-ship (0.21.7–0.21.12)

- [x] 0.21.7 — MCP hotfixes (boot, null params, bare assist)
- [x] 0.21.8 — Collection `add` + `value` one-shot
- [x] 0.21.9 — `format=assistant` on flows mutations
- [x] 0.21.10 — Unified `palm_assist` flows path inference + aliases
- [x] 0.21.11 — Edit shortcut, fuzzy menu, priority intent
- [x] 0.21.12 — Replay harness + weak-LLM playbook docs
- [x] Version **0.21.12** · `just docs-check` · `just guard-common`

## Verify

```bash
uv run pytest tests/test_palm_assist_tool.py tests/test_flows_assistant_format.py \
  tests/test_operator_collection_input.py tests/test_operator_input_coercion.py \
  tests/test_mcp_phase3.py tests/test_collection_drive.py tests/test_collection_edit.py \
  tests/test_flows_session_input.py tests/test_conversation_replay_019f1e9c.py -v
just docs-check
just guard-common
```

## Tag

```bash
git tag -a v0.21.12 -m "Palm Engine 0.21.12 — weak-LLM MCP ergonomics"
```