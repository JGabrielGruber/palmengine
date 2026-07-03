# Release checklist — 0.23.1 (inspect-only catalog)

**Theme:** Non-terminal `inspect-only` path on operator-entry; read alias `operator-entry/inspect`.

**Builds on:** [0.23.0](RELEASE-0.23.0.md) · **Plan:** [docs/superpowers/plans/2026-07-03-0.22.1-mutation-guard.md](docs/superpowers/plans/2026-07-03-0.22.1-mutation-guard.md)

## Pre-ship

- [x] Wizard `route_on_answer` / `complete_on` step params
- [x] Operator-entry `catalog` step + intent routing
- [x] `operator_mode: inspect` in instance metadata
- [x] `AssistService.inspect_catalog()` + `operator-entry/inspect` alias
- [x] Choice menu number coercion on assist input path
- [x] Tests: `test_operator_entry_inspect_only.py`, replay catalog path
- [x] Version **0.23.1**

## Verify

```bash
uv run pytest tests/test_operator_entry_inspect_only.py tests/test_wizard_step_routing.py \
  tests/test_conversation_replay_inspect_guard.py tests/test_operator_entry_flow.py -v
just docs-check
just guard-common
```

## Tag

```bash
git tag -a v0.23.1 -m "Palm Engine 0.23.1 — inspect-only non-terminal catalog mode"
```