# Release checklist — 0.22.1 (Mutation envelope protocol)

**Theme:** `mutation` block on inspect views; inspect vs drive agent rules; conversation replay harness.

**Builds on:** [0.22.0](RELEASE-0.22.0.md) · **Plan:** [docs/superpowers/plans/2026-07-03-0.22.1-mutation-guard.md](docs/superpowers/plans/2026-07-03-0.22.1-mutation-guard.md)

## Pre-ship

- [x] `palm/common/operator/mutation_gate.py` — `build_mutation_envelope()`
- [x] Assistant + powertool views expose `mutation` block
- [x] `docs/mcp.txt` §11 + skill updates
- [x] `tests/test_conversation_replay_inspect_guard.py`
- [x] Version **0.22.1**

## Verify

```bash
uv run pytest tests/test_mutation_gate.py tests/test_mutation_envelope_views.py \
  tests/test_conversation_replay_inspect_guard.py tests/test_palm_assist_tool.py -v
just docs-check
just guard-common
```

## Tag

```bash
git tag -a v0.22.1 -m "Palm Engine 0.22.1 — mutation envelope protocol"
```