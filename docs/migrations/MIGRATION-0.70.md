# Migration — 0.70 Authoring

**Theme:** [VISION-0.70](../vision/VISION-0.70.md) (**open**) · **ADR:** [038](../adr/038-authoring-adapter.md) **Proposed**  
**Map:** [PALM.md](../PALM.md)  
**Seed:** [VISION-AUTHORING](../vision/VISION-AUTHORING.md)

Palm is pre-1.0. José opened **0.70** (2026-09-19). Package stamp stays `0.68.0` (no embedded release). Adapter as-built `0.70.1`: `palm.kits.authoring`. Present start as-built `0.70.2`. Pack as-built `0.70.3`. Thin apply as-built `0.70.4`. Job leaf as-built `0.70.5`. Resource land as-built `0.70.6`.

## Prefer

| Goal | Use |
|------|-----|
| Hold Palm | `ApplicationHost` + `CompositionProfile` |
| Drive a waiting run | `palm.kits.present` (bind / present / submit / start / attach / focus) |
| Land a shape on embedded | `palm.kits.authoring.land(host)` then `commit(body)` (walks catalog `kind`) |
| Land a shape from a job leaf | Pack resource `authoring-commit` (provider working name `authoring`) walks `bound().commit` (`0.70.5`; [SD-025](../../TECH-DEBT.md#sd-025)) |
| Land a resource on embedded | `commit(body)` with `kind: resource` (`0.70.6`). `0.70.4` still calls `create_resource` |
| Land with impact / migrate | `DesignService` on **fat** phenotypes |
| Rules / thresholds / books | Resource **snapshot** (data), not a flow-tree policy |

## As-built (open plan)

| Was | Now (intent) |
|-----|----------------|
| Python `examples/` + fat `DesignService` as the only land | Floor: adapter on `CompositionProfile.embedded()` via `host.definitions` |
| No in-process land kit | `palm.kits.authoring` (`0.70.1`). Handle class unnamed. Door `land(host)` |
| Assist `design_entry` as discovery | Leftover. Not the authoring pack |
| Present drives fixtures | Present drives a landed catalog id after `0.70.2` (`start(..., by_id=True)`) |
| No authoring pack | Catalog wizard landed via adapter (`0.70.3`). As-built id `authoring-pack`. Pack id unnamed. Not `design_entry` |
| Fixtures only after pack wait | Dogfood (`0.70.4`): pytest `commit` of apply → present starts apply → file snapshot resource → confirm wait → present submit |
| Pytest as the only leaf | Job leaf (`0.70.5`): pack submit is the shape; resource walks the adapter |
| Snapshot via `create_resource` | Resource land (`0.70.6`): pack submit of a `ResourceDefinition` mapping |

## Unchanged in this theme

- `palm.kits.present` consume walk ([ADR-037](../adr/037-navigator-invert.md) Accepted).  
- [ADR-008](../adr/008-design-service.md) Design overlay on fat phenotypes.  
- Assist REST / MCP / Portal / CLI forest (compost later).  
- [SD-023](../../TECH-DEBT.md#sd-023) / [SD-024](../../TECH-DEBT.md#sd-024).  
- Handle class, Protocol types, pack id, env spelling — unnamed until José locks them. Package `palm.kits.authoring` locked.

## Surfaces

No MCP / REST field rename. First consumer is in-process Python.
