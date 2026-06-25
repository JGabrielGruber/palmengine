# ADR-002: Pattern Apps and `palm.common` Boundaries

## Status

**Accepted** — June 2026 (wizard Phase 3 + pattern alignment)

## Context

Palm patterns (`wizard`, `parallel`, `pipeline`, `dag`, `etl`) were originally flat packages (`builder.py`, `config.py`, … at the package root). Wizard-specific code had leaked into `palm.common` (wizard runtime, child-wait bridges, CQRS projection types), making the middle layer harder to reason about and violating single-responsibility at scale.

Contributors and AI agents needed a **single canonical story** for:
- Where pattern-specific logic lives
- How patterns register with the host (projections, CQRS, resume)
- What `palm.common` may and may not contain

## Decision

1. **`PatternApp`** — Every pattern subpackage declares a manifest in `app.py` (`name`, `label`, `palm_layers`, `registry_hooks`, optional `ready()`). Registration flows through `register_pattern_app()` in `patterns/_registry.py`.

2. **`bindings/` + `flow/` layout** — Pattern code maps onto Palm layers:
   - `bindings/definitions` — materialize `FlowDefinition` options
   - `bindings/instances` — persistence and submission metadata
   - `bindings/context` — state key conventions
   - `bindings/behavior_tree` — tree construction
   - `bindings/cqrs`, `read_model`, `compensation`, … — as needed (wizard reference)
   - `flow/` — pattern-specific coordination not generic enough for `palm.common`

3. **`palm.common` boundary** — Pattern-specific identifiers, CQRS types, and read models **must not** live in `palm.common`. Generic coordination (buses, hooks, `build_pattern()`, interactive runtime loop, child-wait primitives) stays in common. Pattern apps register contributors at the edge.

4. **Host wiring stays registry-driven** — `ApplicationHost` and `cqrs_wiring.py` dispatch via `iter_cqrs_contributors()` and `register_projection_factory()`; no wizard-specific branches in common.

5. **Enforcement** — `tests/test_common_boundary.py` (AST scan for wizard imports/identifiers in common), `tests/test_modular_apps.py` (PatternApp autoload), `just guard-common` in the default `just check` recipe, and stale-path bans in `scripts/docs_check.py`.

### Alignment status (June 2026)

| Pattern | Structure | Notes |
|---------|-----------|-------|
| wizard | Full `bindings/` + `flow/` + phases | Reference implementation |
| parallel | Full `bindings/` + `flow/` | Richest non-wizard pattern |
| pipeline | `bindings/definitions` + `bindings/behavior_tree` | Transform sequence |
| dag, etl | `bindings/definitions` + `flow/` scaffold | Placeholder execution |

## Consequences

### Positive

- Clear ownership: pattern semantics at the edge, coordination in common
- `app.py` manifests document dogfooding and registry hooks for review
- AST boundary tests prevent regression of wizard leakage into common
- Consistent onboarding path for new patterns ([docs/PATTERN-APPS.md](../PATTERN-APPS.md))

### Negative / trade-offs

- More directories per pattern (mitigated by incremental adoption — stubs are honest)
- Import paths change during migration (public `__init__.py` re-exports preserve stable APIs where needed)
- CQRS per pattern requires `ready()` wiring — slightly more boilerplate than a monolithic common handler

## References

- [docs/PATTERN-APPS.md](../PATTERN-APPS.md) — canonical contributor guide
- [src/palm/patterns/wizard/MIGRATION-WIZARD-PHASES.md](../../src/palm/patterns/wizard/MIGRATION-WIZARD-PHASES.md) — wizard extraction history
- [AGENTS.md](../../AGENTS.md) — constitution and review checklist