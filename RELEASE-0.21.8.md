# Release checklist — 0.21.8 (Collection one-shot add)

**Theme:** `action=add` + `value` succeeds at collection menu phase in one MCP call.

**Builds on:** [0.21.7](RELEASE-0.21.7.md)

## Pre-ship

- [x] `drive_collection_add` in `palm/common/operator/collection_drive.py`
- [x] `palm_wizard_collection_action(action=add, value=…)` one-shot
- [x] `palm_flows_session_input(input="add", value=…)` one-shot
- [x] Tests: `test_collection_drive.py`, `test_mcp_phase3.py`, `test_operator_input_coercion.py`
- [x] Version **0.21.8** · `just docs-check` · `just guard-common`

## Verify

```bash
uv run pytest tests/test_collection_drive.py tests/test_mcp_phase3.py \
  tests/test_operator_input_coercion.py tests/test_operator_collection_input.py -v
just docs-check
just guard-common
```

## Tag

```bash
git tag -a v0.21.8 -m "Palm Engine 0.21.8 — collection add+value one-shot"
```