# Migration Guide — 0.12 Compositional Power

## Wizard resource steps (breaking change)

0.12 removes legacy wizard `step_kind: action` steps that invoked resources via
`resource_provider` + `resource_id`. Use declarative resource steps instead.

### Before (removed)

```python
{
    "slug": "verify_source",
    "step_kind": "action",
    "field_type": "confirm",
    "resource_provider": "rest",
    "resource_id": "health/check",
}
```

### After (required)

1. Register a `ResourceDefinition`:

```python
ResourceDefinition(
    name="rest-health",
    provider="rest",
    action="fetch",
    resource_id="health/check",
)
```

2. Reference it from the wizard step:

```python
{
    "slug": "verify_source",
    "step_kind": "resource",
    "resource_ref": "rest-health",
    "output_key": "verify_source",
}
```

### Removed APIs

- `WizardActionLeaf` and `step_kind: "action"`
- `resource_leaf_from_legacy_action()` in `palm.common.resource`
- `WizardStepConfig.resource_provider` / `resource_id` fields
- `wizard.resource.invoked` and `wizard.action.executed` events

### Observability

Resource invocations emit `resource.invoked`, `resource.completed`, and
`resource.failed` from `ResourceEngine`. Completed/failed payloads may include
`invoke_depth`, `invoke_chain`, `parent_job_id`, and `mode` for compositional
(`palm` provider) calls.

Wizard resource steps additionally emit `wizard.step.completed` with
`resource_ref` context (not a duplicate resource invoke event).

## Compensation for mutating invokes

0.12 tracks mutating resource invocations during wizard execution. If commit
fails after a mutating invoke, `CompensationCoordinator` runs registered undo
handlers via `register_for_resource()`.

```python
from palm.common.compensation import register_for_resource

register_for_resource(
    "submit-ingest-etl",
    undo=lambda ctx, record: host.cancel_job(record["job_id"]),
)
```

Successful undo emits `resource.compensated`. Register handlers during
definition bootstrap (same pattern as flow/process compensation).

## Caching (`PalmSettings` / env)

| Setting | Default | Purpose |
|---------|---------|---------|
| `resource_cache_definitions` | `True` | TTL cache for resolved `ResourceDefinition` |
| `resource_cache_results` | `False` | TTL cache for idempotent read results |
| `resource_cache_ttl_seconds` | `60` | Shared TTL |

Env overrides: `PALM_RESOURCE_CACHE_DEFINITIONS`, `PALM_RESOURCE_CACHE_RESULTS`,
`PALM_RESOURCE_CACHE_TTL_SECONDS`.

**Guidance:** keep definition caching on. Enable result caching only for
idempotent `fetch` actions — never for mutating `invoke` paths.

## Explorer resources hub

Server deployments expose resource introspection at `/explorer/resources`:

- **Catalog** — filters, provider badges, usage counts, keyboard `/` focus
- **Detail** — definition JSON, provider action catalog, related flows/jobs
- **Try Invoke** — `GET/POST /explorer/resources/{ref}/invoke` with param/state forms

Instance and job pages show resource invocation timelines when
`ResourceInvocationProjection` is wired (full `ApplicationHost`; standalone
`ServerRuntime` may return empty rows).

## Compositional `palm` provider

Parent flows invoke child flows via a `ResourceDefinition` backed by the
`palm` provider:

```python
ResourceDefinition(
    name="submit-ingest-etl",
    provider="palm",
    action="submit_flow",
    params={"flow_id": "ingest-etl", "wait": True},
)
```

- **Local mode** — bound at `BaseRuntime.start()`; uses hosting runtime
- **Remote mode** — set `remote_url` / `remote_token` on provider config
- **Guardrails** — depth limit (default 8), cycle detection, `__palm:*` metadata on child jobs

See `examples/definitions/compositional_demo.py` and `tests/test_palm_provider.py`.