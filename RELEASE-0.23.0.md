# Release checklist — 0.23.0 (input_token strict mode)

**Theme:** CSRF-style `input_token` on wizard mutations; opt-in strict enforcement via `PALM_MCP_REQUIRE_INPUT_TOKEN`.

**Builds on:** [0.22.1](RELEASE-0.22.1.md) · **Plan:** [docs/superpowers/plans/2026-07-03-0.22.1-mutation-guard.md](docs/superpowers/plans/2026-07-03-0.22.1-mutation-guard.md)

## Pre-ship

- [x] `issue_input_token` / `validate_input_token` / `require_mutation_token`
- [x] `mutation.input_token` on inspect views; gate persisted in instance metadata
- [x] Validation at `apply_flows_session_input` and `FlowSession.input`
- [x] MCP `input_token` param on `palm_flows_session_input`
- [x] `PALM_MUTATION_SECRET` + `PALM_MCP_REQUIRE_INPUT_TOKEN` in `.env.example`
- [x] Replay test passes in strict mode (tc4 blocked)
- [x] Version **0.23.0**

## Verify

```bash
uv run pytest tests/test_mutation_gate.py tests/test_mutation_gate_token.py \
  tests/test_mutation_envelope_views.py tests/test_flows_session_input.py \
  tests/test_conversation_replay_inspect_guard.py -v
PALM_MCP_REQUIRE_INPUT_TOKEN=1 uv run pytest tests/test_mcp_in_process.py -v
just docs-check
just guard-common
```

## Tag

```bash
git tag -a v0.23.0 -m "Palm Engine 0.23.0 — input_token mutation gate"
```