# Release checklist — 0.21.x (Assistant Expansion)

**Theme:** Human-native surfaces (CLI, Explorer) consume 0.20 assistant envelope; `actions` block; flows `format=assistant` opt-in.

## Pre-ship (0.21.0–0.21.6)

- [x] Design spec — `docs/superpowers/specs/2026-07-01-assistant-expansion-design.md`
- [x] CLI `assist *` commands + `render_assistant_panel`
- [x] Explorer `/explorer/assist` catalog + HTMX workspace + handoff
- [x] `actions` block + production enrichers + REST `catalog/flows`
- [x] Flows `format=assistant` opt-in (REST/MCP)
- [x] `MIGRATION-0.21.md` · `docs/MCP.md` · `docs/llms.txt` · `AGENTS.md`
- [x] Version **0.21.6** · `just docs-check` · `just guard-common`

## Verify

```bash
uv run pytest tests/test_cli_assist.py tests/test_explorer_assist_ssr.py \
  tests/test_assistant_view.py tests/test_assist_service.py \
  tests/test_flows_assistant_format.py -v
just docs-check
just guard-common
```

## Tag

```bash
git tag -a v0.21.6 -m "Palm Engine 0.21.6 — assistant expansion (human surfaces + envelope depth)"
```