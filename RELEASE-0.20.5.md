# Release checklist — 0.20.x (Assistant vs Powertool)

**Theme:** Human-first assistant views on assist surfaces; powertool unchanged on flows/system.

## Pre-ship (0.20.0–0.20.5)

- [x] Design spec — `docs/superpowers/specs/2026-07-01-assistant-powertool-views-design.md`
- [x] `view_registry.py` — thin format dispatch in common
- [x] `assist/views.py` — compose + humanize pipeline
- [x] Assist session defaults; `start_scenario` first turn
- [x] `palm_assist` `format=assistant` default on assist paths
- [x] `MIGRATION-0.20.md` · `docs/MCP.md` · `docs/llms.txt` · `AGENTS.md`
- [x] Version **0.20.5** · `just docs-check` · `just guard-common`

## Verify

```bash
uv run pytest tests/test_operator_view_registry.py tests/test_assistant_view.py \
  tests/test_assist_service.py tests/test_shape_dispatch_result.py \
  tests/test_compact_dispatch_result.py tests/test_palm_assist_tool.py -v
just docs-check
just guard-common
```

## Tag

```bash
git tag -a v0.20.5 -m "Palm Engine 0.20.5 — assistant vs powertool operator views"
```