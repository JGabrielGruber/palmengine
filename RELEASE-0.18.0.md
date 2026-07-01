# Release checklist — 0.18.0

**Theme:** Assist domain MVP — fifth service (`palm/services/assist/`), REST `/v1/api/assist/…`, `host.assist`, `palm-operator-entry` scenario.

## Pre-ship

- [x] `palm/services/assist/` — `AssistService`, `AssistSession`, `registry.py`, `grammar.py`
- [x] `host.assist` on `ApplicationHost` / `ServerContext`
- [x] REST `/v1/api/assist/…` mounted via `service_routes.py`
- [x] OpenAPI **Assist** group in `openapi_registry.py`
- [x] `examples/definitions/operator_entry.py` + assist contributor registration
- [x] `palm/app/assist_registry.py` for app-level contributors
- [x] Tests: registry, service, REST routes, operator-entry integration
- [x] `MIGRATION-0.18.md` · ADR-006 accepted
- [x] Version **0.18.0** · `just docs-check` · `just guard-common`

## Verify

```bash
uv run pytest tests/test_assist_registry.py tests/test_assist_service.py \
  tests/test_assist_service_routes.py tests/test_operator_entry_flow.py \
  tests/test_assist_app_registry.py tests/test_openapi_registry.py -v
just docs-check
just guard-common
```

## Visual check

1. `just palm-server` → `http://127.0.0.1:8080`
2. `/v1/docs` — **Assist** group with scenario start + session handoff
3. `/v1/openapi.json` — `/v1/api/assist/scenarios/{scenario_id}/start`
4. `/health` — version `0.18.0`

## Tag

```bash
git commit -m "feat(0.18.0): assist domain MVP"
git tag -a v0.18.0 -m "Palm Engine 0.18.0 — Assist domain MVP"
```