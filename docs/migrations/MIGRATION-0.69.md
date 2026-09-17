# Migration — 0.69 Navigator

**Theme:** [VISION-0.69](../vision/VISION-0.69.md) (**open**) · **ADR:** [037](../adr/037-navigator-invert.md) **Proposed**  
**Map:** [PALM.md](../PALM.md)  
**Seed:** [VISION-NAVIGATOR](../vision/VISION-NAVIGATOR.md)

Palm is pre-1.0. Package stamp stays `0.68.0` until an embedded release. This file names contract motion as execute lands.

## Prefer

| Goal | Use |
|------|-----|
| Empty-handed walk | Present kit `start()` with kit-owned `guidance_definition_id` (`0.69.5`). Unset refuses. Set to **`navigator`** for the staying chooser (`0.69.6`). Dogfood `0.69.7` assigns that key after bind on embedded / test. Constructor override and env spelling stay later. |
| Return to guidance | `focus(guidance_instance_id)` on the bound session |
| Attach after start | `SessionService.attach_after_start` (`0.69.2`). Do **not** set `session_id` on the job |
| Spawn a sibling without nested park | `FlowExecutionService.spawn_sibling` (`0.69.3`). Parent stays `WAITING_FOR_INPUT`. No `WaitInterest` on the sibling |
| Present a waiting run | `palm.kits.present` present → `JobInspectable` / wait plane (`0.69.4`) |
| Walk bind / submit / start / attach / focus | `palm.kits.present.bind(host)` (`0.69.4`). Handle class unnamed. Start reuses `spawn_sibling` |
| Stamp / replace Home | Present kit after attach (`0.69.5`). `SessionService` writes. Titles cannot become Home |

## Behavior / names that may change

Execute will name the cut. Likely:

| Was | May become |
|-----|------------|
| `AssistService.dispatch` as the empty-handed door | Still as-built. Library door: `palm.kits.present` on embedded (`0.69.4`). Empty-handed start: kit `guidance_definition_id` (`0.69.5`) |
| `operator-entry` ends, then product auto-starts | Catalog wizard **`navigator`** beside it (`0.69.6`). Floor spawn: `spawn_sibling` (`0.69.3`); instance stays `WAITING_FOR_INPUT`. Leftover `operator_entry` still ends |
| Nested park (`until_input`) as Home | Leftover. Floor spawn does not wait on child terminal |
| `SessionOwnershipHook` / job metadata `session_id` | Leftover. Floor attach is `SessionService.attach_after_start` (`0.69.2`) |
| No `guidance_instance_id` | Session metadata key. `0.69.1`: stamp/replace via `SessionService`. `0.69.5`: kit is the stamp/replace caller |
| Core `PalmSettings` as every kit knob | Present kit owns `guidance_definition_id` (`0.69.5`). Unset default. Not flattened onto core settings |

## Unchanged in this theme

- Assist REST / MCP / Portal / CLI forest (compost later).  
- [ADR-006](../adr/006-assist-domain.md) Accepted.  
- [SD-023](../../TECH-DEBT.md#sd-023) / [SD-024](../../TECH-DEBT.md#sd-024).  
- User plane. Admission. Structure definition menus.

## Surfaces

No MCP / REST field rename in the floor. First consumer is in-process Python.
