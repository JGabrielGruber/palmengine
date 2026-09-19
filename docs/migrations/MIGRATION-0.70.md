# Migration — 0.70 Authoring

**Theme:** [VISION-0.70](../vision/VISION-0.70.md) (**open**) · **ADR:** [038](../adr/038-authoring-adapter.md) **Proposed**  
**Map:** [PALM.md](../PALM.md)  
**Seed:** [VISION-AUTHORING](../vision/VISION-AUTHORING.md)

Palm is pre-1.0. José opened **0.70** (2026-09-19). Package stamp stays `0.68.0` (no embedded release). Adapter as-built `0.70.1`: `palm.kits.authoring`.

## Prefer

| Goal | Use |
|------|-----|
| Hold Palm | `ApplicationHost` + `CompositionProfile` |
| Drive a waiting run | `palm.kits.present` (bind / present / submit / start / attach / focus) |
| Land a shape on embedded | `palm.kits.authoring.land(host)` then `commit(body)` (walks `host.definitions.create_flow`) |
| Land with impact / migrate | `DesignService` on **fat** phenotypes |
| Rules / thresholds / books | Resource **snapshot** (data), not a flow-tree policy |

## As-built (open plan)

| Was | Now (intent) |
|-----|----------------|
| Python `examples/` + fat `DesignService` as the only land | Floor: adapter on `CompositionProfile.embedded()` via `host.definitions` |
| No in-process land kit | `palm.kits.authoring` (`0.70.1`). Handle class unnamed. Door `land(host)` |
| Assist `design_entry` as discovery | Leftover. Not the authoring pack |
| Present drives fixtures | Present drives a landed definition after `0.70.1+` |

## Unchanged in this theme

- `palm.kits.present` consume walk ([ADR-037](../adr/037-navigator-invert.md) Accepted).  
- [ADR-008](../adr/008-design-service.md) Design overlay on fat phenotypes.  
- Assist REST / MCP / Portal / CLI forest (compost later).  
- [SD-023](../../TECH-DEBT.md#sd-023) / [SD-024](../../TECH-DEBT.md#sd-024).  
- Handle class, Protocol types, pack id, env spelling — unnamed until José locks them. Package `palm.kits.authoring` locked.

## Surfaces

No MCP / REST field rename. First consumer is in-process Python.
