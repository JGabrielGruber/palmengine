# Migration — 0.69 Navigator

**Theme:** [VISION-0.69](../vision/VISION-0.69.md) (**open**) · **ADR:** [037](../adr/037-navigator-invert.md) **Proposed**  
**Map:** [PALM.md](../PALM.md)  
**Seed:** [VISION-NAVIGATOR](../vision/VISION-NAVIGATOR.md)

Palm is pre-1.0. Package stamp stays `0.68.0` until an embedded release. This file names contract motion as execute lands.

## Prefer

| Goal | Use |
|------|-----|
| Empty-handed walk | Present kit `start()` with `guidance_definition_id` |
| Return to guidance | `focus(guidance_instance_id)` on the bound session |
| Attach after start | `SessionService.attach_after_start` (`0.69.2`). Do **not** set `session_id` on the job |
| Present a waiting run | Kit present → `JobInspectable` / wait plane (turn invert) |

## Behavior / names that may change

Execute will name the cut. Likely:

| Was | May become |
|-----|------------|
| `AssistService.dispatch` as the empty-handed door | Still as-built. New door: `palm.kits.present` on embedded |
| `operator-entry` ends, then product auto-starts | New wizard pack **beside** it; instance stays `WAITING_FOR_INPUT` |
| `SessionOwnershipHook` / job metadata `session_id` | Leftover. Floor attach is `SessionService.attach_after_start` (`0.69.2`) |
| No `guidance_instance_id` | Session metadata key. `0.69.1`: stamp/replace via `SessionService` (kit caller later) |
| Core `PalmSettings` as every kit knob | Present kit owns `guidance_definition_id` |

## Unchanged in this theme

- Assist REST / MCP / Portal / CLI forest (compost later).  
- [ADR-006](../adr/006-assist-domain.md) Accepted.  
- [SD-023](../../TECH-DEBT.md#sd-023) / [SD-024](../../TECH-DEBT.md#sd-024).  
- User plane. Admission. Structure definition menus.

## Surfaces

No MCP / REST field rename in the floor. First consumer is in-process Python.
