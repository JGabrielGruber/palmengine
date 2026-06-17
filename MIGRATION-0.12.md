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