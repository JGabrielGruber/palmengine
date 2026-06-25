# ADR-003: Provider Apps and Django-Style Layout

## Status

**Accepted** — June 2026

## Context

The built-in `palm` compositional provider (`palm/providers/palm/`) grew as a flat 11-file package while patterns gained `PatternApp`, `bindings/`, `flow/`, and enforcement via `docs/PATTERN-APPS.md`. Contributors opening the palm provider could not immediately see which Palm subsystems it dogfoods — unlike patterns where `app.py` declares `palm_layers`.

Providers are external-system adapters; the `palm` provider is the meta-case (Palm calling Palm) and should dogfood Palm architecture the same way `wizard` does for patterns.

## Decision

1. **`ProviderApp`** — Every provider subpackage declares a manifest in `app.py` (`name`, `label`, `palm_layers`, `actions`, `registry_hooks`, optional `ready()`). Registration flows through `register_provider_app()` in `providers/_registry.py`.

2. **`bindings/` + `flow/` layout** — Provider code maps onto Palm layers:
   - `bindings/resource` — `BaseProvider` contract surface
   - `bindings/orchestration` — job payloads, local invoker (palm)
   - `bindings/runtimes` — in-process runtime binding (palm)
   - `bindings/recursion` — compositional guardrails (palm)
   - `flow/` — coordinator dispatch, params, target DSL, remote HTTP

3. **Runtime binding via registry** — `PalmProviderApp.ready()` registers `bind_palm_runtime` / `clear_palm_runtime` through `register_runtime_binding()`. `BaseRuntime.start()` / `stop()` dispatch via `get_runtime_binding()` instead of hard-importing provider modules.

4. **Stub provider manifests** — `rest`, `graphql`, and `postgres` ship minimal `app.py` files so `INSTALLED_PROVIDERS` is homogeneous.

5. **Enforcement** — `tests/test_modular_apps.py` asserts every installed provider has a `ProviderApp` instance.

### Alignment status (June 2026)

| Provider | Structure | Notes |
|----------|-----------|-------|
| palm | Full `bindings/` + `flow/` | Reference implementation |
| rest, graphql, postgres | `app.py` only | Stubs; grow bindings as drivers mature |

## Consequences

### Positive

- Opening `providers/palm/app.py` answers "what Palm does this use?"
- Consistent onboarding with patterns ([docs/PROVIDER-APPS.md](../PROVIDER-APPS.md))
- Runtime binding is an explicit registry hook, testable and documented

### Negative / trade-offs

- More directories for the palm provider (mitigated by incremental adoption for stub providers)
- Import paths change during migration (public `__init__.py` re-exports preserve stable APIs)
- `common` and `wizard` still lazy-import `bindings/runtimes/wiring` for child-wait — acceptable edge coupling until a generic runtime accessor exists

## References

- [docs/PROVIDER-APPS.md](../PROVIDER-APPS.md) — canonical contributor guide
- [docs/adr/002-pattern-apps-and-common-boundaries.md](002-pattern-apps-and-common-boundaries.md) — parallel PatternApp ADR
- [docs/adr/001-compositional-power-resources.md](001-compositional-power-resources.md) — resource engine design