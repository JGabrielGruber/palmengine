# Release checklist — 0.17.3

**Theme:** OpenAPI and HTML docs generated from per-service route registries — full `/v1/api/…` surface documented.

## Pre-ship

- [x] `openapi_registry.py` aggregates definitions, flows, processes, providers, system `ROUTES`
- [x] `rest_routes()` feeds OpenAPI, `/v1/docs`, and `doc_examples`
- [x] Meta-only runtime registration (`routes.py`); service routes via `service_routes.py`
- [x] `tests/test_openapi_registry.py`
- [x] `MIGRATION-0.17.md` section 0.17.3
- [x] Version **0.17.3** · `just docs-check` · `just guard-common`

## 0.17 cycle complete

| Phase | Deliverable |
|-------|-------------|
| 0.17.0 | System REST parity |
| 0.17.1 | Process execution service |
| 0.17.2 | Palm provider remote alignment |
| 0.17.3 | OpenAPI from service registries |

## Verify

```bash
uv run pytest tests/test_openapi_registry.py tests/test_service_registries.py \
  tests/test_system_service_routes.py tests/test_process_execution_service.py \
  tests/test_rest_process_routes.py tests/test_palm_provider_refactor.py \
  tests/test_server_rest.py tests/test_server_docs.py -v
just docs-check && just guard-common
```

## Tag

```bash
git commit -m "feat(0.17.3): OpenAPI from per-service route registries"
git tag -a v0.17.3 -m "Palm Engine 0.17.3 — OpenAPI from service registries; 0.17 complete"
```