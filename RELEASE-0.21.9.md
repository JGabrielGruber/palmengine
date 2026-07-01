# Release checklist — 0.21.9 (Assistant on flows mutations)

**Theme:** Opt-in `format=assistant` on flows session input and collection mutations.

**Builds on:** [0.21.8](RELEASE-0.21.8.md)

## Pre-ship

- [x] `palm_flows_session_input(format="assistant")`
- [x] `palm_wizard_collection_action(format="assistant")`
- [x] `build_collection_assistant_actions` + merge in `build_assistant_view`
- [x] REST `POST …/input?format=assistant`
- [x] Version **0.21.9** · `just docs-check` · `just guard-common`

## Verify

```bash
uv run pytest tests/test_flows_assistant_format.py tests/test_assistant_view.py \
  tests/test_collection_actions.py tests/test_mcp_phase3.py -v
just docs-check
just guard-common
```

## Tag

```bash
git tag -a v0.21.9 -m "Palm Engine 0.21.9 — assistant envelope on flows mutations"
```