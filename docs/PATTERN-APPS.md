# Pattern Apps — How Palm Patterns Work

**Version:** 0.13.0 · **Audience:** contributors, integrators, AI agents

Palm patterns are **Django-style apps** under `palm/patterns/<name>/`. Each pattern is a self-contained package that dogfoods Palm's own engines (behavior trees, context, orchestration, transforms) while keeping **pattern-specific logic out of `palm.common`**.

---

## Mental model

Three layers inside every mature pattern:

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **Pattern class** | `pattern.py` | `BasePattern` subclass — tick/reset, step inspection, input handling |
| **Bindings** | `bindings/` | Wire Palm subsystems: definitions, instances, context, behavior tree, CQRS, compensation |
| **Flow** | `flow/` | Pattern-specific coordination that is not generic enough for `palm.common` |

Shared materialization lives in **`palm.common.patterns`** — it resolves `FlowDefinition` via `pattern_registry` and `register_builder()`, but never owns wizard/parallel/pipeline semantics.

```
FlowDefinition (definitions/)
        ↓
common/patterns/builder.py  →  pattern_registry + register_builder()
        ↓
patterns/<name>/bindings/definitions/builder.py  →  ParallelPattern | WizardPattern | …
        ↓
pattern.py tick()  →  behavior tree + flow coordination
```

---

## PatternApp manifest

Every pattern ships an `app.py` subclassing `PatternApp`:

```python
from palm.common.patterns.app import PatternApp

class ParallelApp(PatternApp):
    name = "parallel"
    label = "Parallel branch execution"
    palm_layers = ("core.behavior_tree", "core.context", …)
    registry_hooks = ("builder", "instance_sync", "submission_metadata")

    def ready(self) -> None:
        # Optional: register_projection_factory, register_cqrs_contributor, bridges, …
        pass

parallel_app = ParallelApp()
```

| Field | Purpose |
|-------|---------|
| `name` | Registry key — must match `pattern_registry.register("parallel", …)` |
| `label` | Human-readable name for docs and `palm doctor` |
| `palm_layers` | Which Palm subsystems this pattern dogfoods (documentation + review aid) |
| `depends_on` | Other pattern apps (reserved for cross-pattern wiring) |
| `registry_hooks` | Which `patterns/_registry.py` hooks the pattern uses |
| `ready()` | Side-effect registration: projections, CQRS, bridges, read models |

`registry.py` imports the app and calls `*_app.register()` after wiring builders and instance sync.

---

## Bindings layout

Bindings map pattern code onto Palm layers. Not every pattern needs every folder — grow into the layout as complexity demands.

```
patterns/<name>/
├── pattern.py          # BasePattern — always at package root
├── app.py              # PatternApp manifest
├── registry.py         # pattern_registry + register_builder + app.register()
├── bindings/
│   ├── definitions/    # build(), config dataclasses, options parsing
│   ├── instances/      # persistence fields, resume, submission metadata
│   ├── context/        # state keys, scoped conventions
│   ├── behavior_tree/  # tree construction, custom leaves/nodes
│   ├── resource/       # child-wait, external resource hooks (wizard)
│   ├── events/         # pattern-specific event types
│   ├── compensation/   # commit/undo handlers (wizard)
│   ├── read_model.py   # REST/SSR view assembly (wizard)
│   └── cqrs/           # commands, queries, handlers, projection (wizard)
└── flow/               # pattern-specific coordination (not common)
```

### Current maturity (June 2026)

| Pattern | `bindings/` | `flow/` | `PatternApp` hooks |
|---------|-------------|---------|-------------------|
| **wizard** | Full (definitions, instances, context, BT, resource, events, compensation, CQRS, read model) | `flow/collection/`, `flow/extensions/`, `phases/` | builder, instance_sync, submission_metadata, interactive_runtime, child_wait, read_model_builder, projection_factory, cqrs_contributor |
| **parallel** | definitions, instances, context, behavior_tree | branch, scope, merge | builder, instance_sync, submission_metadata |
| **pipeline** | definitions, behavior_tree | — | builder |
| **dag** | definitions (placeholder builder) | scaffold | builder |
| **etl** | definitions (placeholder builder) | scaffold | builder |

---

## Registry hooks (`patterns/_registry.py`)

Patterns extend the host without editing `palm.app` internals:

| Hook | Register via | Consumed by |
|------|--------------|-------------|
| `register_builder` | `registry.py` | `common/patterns/builder.py` |
| `register_instance_sync` | `registry.py` | `InstancePersistenceHook`, resume |
| `register_submission_metadata` | `registry.py` | Job metadata enrichment |
| `register_interactive_runtime` | `ready()` | Interactive CLI/SSR flows |
| `register_child_wait_hooks` | `ready()` | Parent jobs waiting on child wizards |
| `register_read_model_builder` | `ready()` | `build_pattern_read_model()` |
| `register_projection_factory` | `ready()` | `ApplicationHost` CQRS projections |
| `register_cqrs_contributor` | `ready()` | `cqrs_wiring.py` command/query dispatch |

Wizard is the reference implementation for projection and CQRS hooks. Other patterns add hooks as they gain REST/dashboard surfaces.

---

## `palm.common` boundary (strict)

**`palm.common` coordinates; it does not own pattern semantics.**

| Belongs in `palm.common` | Belongs in `palm.patterns.<name>` |
|--------------------------|-----------------------------------|
| `PatternBuildContext`, generic `build_pattern()` | `build()` for a specific pattern's flow options |
| `interactive_runtime.py` (generic wait/input loop) | Wizard-specific prompt/read-model assembly |
| `child_wait.py` (generic parent/child job wait) | Wizard child-wizard bridge wiring |
| `pattern_read_model.py` (dispatch by pattern name) | `build_wizard_view()`, wizard CQRS types |
| CQRS buses, projection rebuild policy | `SubmitWizardCommand`, `WizardProgressProjection` |
| `InstancePersistenceHook` (generic) | `extract_instance_fields_from_job` per pattern |

Enforced by `tests/test_common_boundary.py` and `just guard-common`.

---

## Adding a new pattern

1. Create `palm/patterns/<name>/` with `pattern.py`, `app.py`, `registry.py`, `__init__.py`.
2. Add `bindings/definitions/builder.py` with `build(flow, context, pattern_cls)`.
3. Register in `registry.py`:
   - `pattern_registry.register("<name>", MyPattern)`
   - `register_builder("<name>", build)`
   - `<name>_app.register()`
4. Add `"<name>"` to `INSTALLED_PATTERNS` in `patterns/_apps.py`.
5. As complexity grows, move code into `bindings/` and `flow/` — do not park pattern logic in `palm.common`.
6. Add tests; run `just guard-common` before merge.

See [DEVELOPMENT.md](../DEVELOPMENT.md) for contributor setup and [AGENTS.md](../AGENTS.md) for architectural rules.

---

## Field naming: `current_step_slug`

Durable instance position uses **`current_step_slug`** on `ProcessInstance` and `StateSnapshot`. Readers accept the legacy pre-0.13 step-slug field in persisted JSON. Pattern-specific step inspection implements `current_step_slug(state)` on `StepInspectable` patterns.

---

## Related documents

| Document | Topic |
|----------|-------|
| [docs/adr/002-pattern-apps-and-common-boundaries.md](adr/002-pattern-apps-and-common-boundaries.md) | ADR for PatternApp + common boundary |
| [src/palm/patterns/wizard/MIGRATION-WIZARD-PHASES.md](../src/palm/patterns/wizard/MIGRATION-WIZARD-PHASES.md) | Wizard phase refactor history |
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Full layer diagram and CQRS |
| [AGENTS.md](../AGENTS.md) | Constitution and review checklist |