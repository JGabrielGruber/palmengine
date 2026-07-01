# Provider Apps — How Palm Providers Work

**Version:** 0.13.0 · **Audience:** contributors, integrators, AI agents

Palm providers are **Django-style apps** under `palm/providers/<name>/`. Each provider adapts an external system (REST, Postgres, GraphQL) or, in the case of **`palm`**, dogfoods Palm itself for compositional orchestration.

---

## Mental model

Three layers inside every mature provider:

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **Provider class** | `provider.py` | `BaseProvider` subclass — `invoke()`, `describe()`, `health()` |
| **Bindings** | `bindings/` | Wire Palm subsystems: resource contract, orchestration, runtimes, recursion |
| **Flow** | `flow/` | Provider-specific coordination not generic enough for `palm.common` |

The resource engine in **`palm.core.resource`** resolves providers via `provider_registry`. Provider apps register at the edge; core never imports `palm.providers`.

```
ResourceDefinition (definitions/)
        ↓
core/resource/engine.py  →  provider_registry.get("palm")
        ↓
providers/<name>/provider.py  →  invoke(action, params)
        ↓
bindings/ + flow/  →  external system or Palm runtime delegation
```

---

## ProviderApp manifest

Every provider ships an `app.py` subclassing `ProviderApp`:

```python
from palm.common.providers.app import ProviderApp

class PalmProviderApp(ProviderApp):
    name = "palm"
    label = "Compositional Palm orchestration"
    palm_layers = ("core.resource", "core.orchestration", …)
    actions = ("submit_flow", "submit_process", "invoke_resource", "fetch")
    registry_hooks = ("provider_registry", "runtime_binding")

    def ready(self) -> None:
        register_runtime_binding(bind_palm_runtime, unbind=clear_palm_runtime)

palm_app = PalmProviderApp()
```

| Field | Purpose |
|-------|---------|
| `name` | Registry key — must match `provider_registry.register("palm", …)` |
| `label` | Human-readable name for docs and `palm doctor` |
| `palm_layers` | Which Palm subsystems this provider dogfoods (documentation + review aid) |
| `actions` | Named actions exposed via `describe()` and `invoke()` |
| `depends_on` | Other provider apps (reserved for cross-provider wiring) |
| `registry_hooks` | Which `providers/_registry.py` hooks the provider uses |
| `ready()` | Side-effect registration: runtime binding, compensation, CQRS |

`registry.py` calls `provider_registry.register()` then `*_app.register()`.

---

## Bindings layout

Bindings map provider code onto Palm layers. Not every provider needs every folder — grow into the layout as complexity demands.

```
providers/<name>/
├── provider.py          # BaseProvider — always at package root
├── app.py               # ProviderApp manifest — READ THIS FIRST
├── registry.py          # provider_registry + app.register()
├── exceptions.py        # provider-local error taxonomy
├── bindings/
│   ├── resource/        # describe(), invoke adapter, health
│   ├── orchestration/   # job payloads, local invoker, wait helpers (palm)
│   ├── runtimes/        # in-process runtime binding (palm)
│   └── recursion/       # compositional depth/cycle guard (palm)
└── flow/
    ├── coordinator.py   # mode dispatch (local vs remote)
    ├── params.py        # typed invoke parameters
    ├── target.py        # resource_id / param target DSL
    └── remote/          # HTTP client + remote invoker (palm)
```

### Current maturity (June 2026)

| Provider | `bindings/` | `flow/` | `ProviderApp` hooks |
|----------|-------------|---------|---------------------|
| **palm** | resource, orchestration, runtimes, recursion | coordinator, params, target, remote | provider_registry, runtime_binding |
| **rest** | resource, transport | params | provider_registry |
| **graphql** | — (stub) | — | provider_registry |
| **postgres** | — (stub) | — | provider_registry |

---

## Registry hooks (`providers/_registry.py`)

Providers extend the host without editing `palm.app` internals:

| Hook | Register via | Consumed by |
|------|--------------|-------------|
| `provider_registry` | `registry.py` | `core/resource/engine.py` |
| `register_runtime_binding` | `ready()` | `common/runtimes/base.py` on `start()` / `stop()` |

Future hooks (reserved): compensation handlers, CQRS projections for resource invocations.

---

## The `palm` provider (reference)

**Read [`app.py`](../src/palm/providers/palm/app.py) first** to see which Palm layers the compositional provider dogfoods.

| Binding | Palm layer | Role |
|---------|------------|------|
| `bindings/resource` | `core.resource` | Provider contract, parent-job correlation |
| `bindings/orchestration` | `core.orchestration` | Child job payloads, local wait |
| `bindings/runtimes` | `common.runtimes` | `bind_palm_runtime()` for embedded mode |
| `bindings/recursion` | `core.utils.recursion` | Depth and cycle guardrails |
| `flow/remote` | `runtimes.server` HTTP | Out-of-process Palm via service-domain REST (0.17.2+) |

**Remote HTTP paths** (`flow/remote/client.py`):

| Action | Method | Path |
|--------|--------|------|
| `submit_flow` | `POST` | `/v1/api/flows/{flow_id}/create` |
| `submit_process` | `POST` | `/v1/api/processes/{process_id}/prepare` then `/v1/api/processes/submit` |
| `fetch` (job status) | `GET` | `/v1/api/system/jobs/{job_id}` |
| `invoke_resource` | `POST` | `/v1/api/providers/{provider}/{resource}/invoke` |

Create responses may return `session_id`; `remote_job_payload` maps it to `instance_id` for wait metadata.

Actions: `submit_flow`, `submit_process`, `invoke_resource`, `fetch`.

---

## `palm.common` boundary (strict)

**`palm.common` coordinates; it does not own provider semantics.**

| Belongs in `palm.common` | Belongs in `palm.providers.<name>` |
|--------------------------|-------------------------------------|
| Generic child-wait primitives | Provider-specific invoke adapters |
| `providers._registry` accessor hooks | `bindings/`, `flow/`, typed params |
| Resource catalog / resolver wiring | HTTP transport, remote clients |

`palm.common` may import `palm.providers._registry` only — never `palm.providers.<name>.bindings` or `flow`. Enforced by `tests/test_provider_boundary.py` and `just guard-common`.

---

## Adding a new provider

1. Create `palm/providers/<name>/` with `provider.py`, `app.py`, `registry.py`, `__init__.py`.
2. Subclass `BaseProvider`; implement `connect`, `fetch`, `disconnect`; override `invoke` / `describe` as needed.
3. Register in `registry.py`:
   - `provider_registry.register("<name>", MyProvider)`
   - `<name>_app.register()`
4. Add `"<name>"` to `INSTALLED_PROVIDERS` in `providers/_apps.py`.
5. As complexity grows, move code into `bindings/` and `flow/` — do not park provider logic in `palm.common`.
6. Add tests; run `just guard-common` before merge.

See [PATTERN-APPS.md](PATTERN-APPS.md) for the parallel pattern-app model and [AGENTS.md](../AGENTS.md) for architectural rules.

---

## Related documents

| Document | Topic |
|----------|-------|
| [docs/adr/003-provider-apps.md](adr/003-provider-apps.md) | ADR for ProviderApp layout |
| [docs/adr/001-compositional-power-resources.md](adr/001-compositional-power-resources.md) | Resource engine + palm provider design |
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Resource execution path |
| [AGENTS.md](../AGENTS.md) | Constitution and review checklist |