# Migration — 0.69 Navigator

**Theme:** [VISION-0.69](../vision/closed/VISION-0.69.md) (**closed**) · **ADR:** [037](../adr/037-navigator-invert.md) **Accepted**  
**Map:** [PALM.md](../PALM.md)  
**Seed:** [VISION-NAVIGATOR](../vision/VISION-NAVIGATOR.md)

Palm is pre-1.0. José closed **0.69** (2026-09-17). Package stamp stays `0.68.0` (no embedded release). Floor: one embedded walk without Assist.

## Prefer

| Goal | Use |
|------|-----|
| Empty-handed walk | Present kit `start()` with kit-owned `guidance_definition_id`. Unset refuses. Set to **`navigator`** for the staying chooser. Assign after bind until constructor / env is locked |
| Return to guidance | `focus(guidance_instance_id)` on the bound session |
| Attach after start | `SessionService.attach_after_start`. Do **not** set `session_id` on the job |
| Spawn a sibling without nested park | `FlowExecutionService.spawn_sibling`. Parent stays `WAITING_FOR_INPUT`. No `WaitInterest` on the sibling |
| Present a waiting run | `palm.kits.present` present → `JobInspectable` / wait plane |
| Walk bind / submit / start / attach / focus | `palm.kits.present.bind(host)`. Handle class unnamed. Start reuses `spawn_sibling` |
| Stamp / replace Home | Present kit after attach. Kit owns `GUIDANCE_INSTANCE_ID`. `SessionService.stamp` / `replace` write that named key. Titles cannot become Home |

## As-built (closed)

| Was | Now |
|-----|-----|
| `AssistService.dispatch` as the empty-handed door | Still as-built Assist. Library door: `palm.kits.present` on embedded. Empty-handed start: kit `guidance_definition_id` |
| `operator-entry` ends, then product auto-starts | Catalog wizard **`navigator`** beside it. Floor spawn: `spawn_sibling`; instance stays `WAITING_FOR_INPUT`. Leftover `operator_entry` still ends |
| Nested park (`until_input`) as Home | Leftover. Floor spawn does not wait on child terminal |
| `SessionOwnershipHook` / job metadata `session_id` | Leftover. Floor attach is `SessionService.attach_after_start` |
| No `guidance_instance_id` | Session metadata key owned by the present kit. Generic `SessionService.stamp` / `replace`. Kit is the stamp/replace caller |
| Core `PalmSettings` as every kit knob | Present kit owns `guidance_definition_id`. Unset default. Not flattened onto core settings |

## Unchanged in this theme

- Assist REST / MCP / Portal / CLI forest (compost later).  
- [ADR-006](../adr/006-assist-domain.md) Accepted.  
- [SD-023](../../TECH-DEBT.md#sd-023) / [SD-024](../../TECH-DEBT.md#sd-024).  
- User plane. Admission. Structure definition menus.  
- Protocol types, kit handle class, walk-write interface type, env spelling.

## Surfaces

No MCP / REST field rename. First consumer is in-process Python.
