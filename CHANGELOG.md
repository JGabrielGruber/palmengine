# Changelog

All notable changes to Palm are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Docs — 0.71 present (theme open)

- Lock as-built names: method `adopt`, prefix `adopt:`, empty `runtime`, adopted rows stay `Workload`. Theme stays open. ADR-039 stays **Proposed**. Next: José exit judgment plus named place leftovers.
- After `0.71.19`: residual named (`workload_place` WorkloadHandle accept; `WorkloadEngine` argv-must-not-be-str; `place_spawn` os: getattr/isinstance). Paid: overlay gone; `.handles` / `__os_registry__` gone; bound seat reads registry `ready`; typed `workload_place` env Mapping; typed `WorkloadEngine` named runtime bind; typed seat `bind_structure`; StructureEngine `_places_ready` dual gone; stdlib settings + `dotenv` extra; embedded import isolation from server barrel; base wheel omits surface static / MCP data; ApplicationHost cold import (common→system rehydrate cycle cut). PALM pointer through `0.71.19`.

### 0.71.19 — ApplicationHost cold import

- Wait rehydrate lives in `palm.core.wait`. `instance_sync` no longer imports `palm.system` for it. Bare `from palm.app import ApplicationHost` succeeds cold without `ensure_core_plugins()`. Stamp stays `0.68.0`. Tests: `tests/test_application_host_cold_import_0_71_19.py`.

### 0.71.18 — Keep surface assets out of wheel

- Base `palmengine` wheel excludes SSR/Portal/Analytics `static/` and `palm/runtimes/mcp/data/`. Repo/sdist keep them. Hatch wheel `artifacts` no longer force those paths. Not a pip extra. Stamp stays `0.68.0`. Tests: `tests/test_wheel_surface_assets_0_71_18.py`.

### 0.71.17 — Isolate embedded from server import

- `palm.runtimes` package root no longer re-exports sibling surfaces. Embedded import / `PalmKernel` embedded start does not load `palm.runtimes.server` (or daemon/mcp). Tests: `tests/test_embedded_import_isolation_0_71_17.py`.

### 0.71.16 — Stdlib settings; extra dotenv

- Bare `palmengine` hard deps empty. `PalmSettings` is stdlib (`PALM_*` from `os.environ` only; no cwd `.env` auto-load).
- File load (`from_env_file` / `--config`) requires pip extra **`dotenv`**; missing extra fails closed. File overrides env; CLI flags still win.
- Stamp stays `0.68.0`. Tests: `tests/test_settings_stdlib_0_71_16.py`.

### 0.71.15 — Invert StructureEngine `_places_ready`

- Place readiness lives only behind the bound `ready(place_id)` hand. No second `_places_ready` set. Unbound hand fails closed. `RecordingEffectPort` owns a `ready` hand for auto-ack. Tests: `tests/test_places_ready_invert_0_71_15.py`.

### 0.71.14 — Typed seat bind_structure

- `StructureSeat.assemble` matches `StructureEffectPort` and calls `bind_structure`. No `getattr(self.effects, "bind_structure", None)`. Tests: `tests/test_seat_bind_structure_0_71_14.py`.

### 0.71.13 — Typed WorkloadEngine named runtime bind

- `_named_runtimes` accepts Mapping only; missing → empty; non-mapping / non-`WorkloadRuntime` fails closed. No `isinstance(bound, dict)` / `isinstance(runtime, WorkloadRuntime)` soup. Tests: `tests/test_runtime_bind_0_71_13.py`.

### 0.71.12 — Typed workload_place spec env

- `_env_from_payload` accepts Mapping only; missing → empty; non-mapping fails closed. No `isinstance(..., dict)` silent drop. Tests: `tests/test_workload_place_env_0_71_12.py`.

### 0.71.11 — Invert StructureEngine place observations

- Assemble / admission reads place-registry `ready(place_id)`. PLACE_READY does not accumulate a second body book when that hand is bound. Tests: `tests/test_place_observations_invert_0_71_11.py`.

### 0.71.10 — Invert RegisteredPlaceSpawn.handles

- Typed `register_body` / `body` / `forget_body` and typed `os_registry`. No `handles` bag. No `__os_registry__`. Tests: `tests/test_spawn_handles_invert_0_71_10.py`.

### 0.71.9 — Compost place-registry overlay

- No `overlay` dict beside the workload book. Bound places are book projection only; unbound bare / `os:` use one local register. Tests: `tests/test_place_overlay_compost_0_71_9.py`.

### 0.71.8 — Typed adopt payload handle

- `AdoptPlaceSpawn` takes typed `WorkloadHandle` only; no dict | `base_url` coercion at the place→engine boundary. Tests: `tests/test_handle_payload_invert_0_71_8.py`.

### 0.71.7 — Typed place_registry spawn bind

- `place_registry.engine_from_spawn` matches typed `RegisteredPlaceSpawn`; no Protocol `isinstance(spawn, BookBindPort)`. Tests: `tests/test_place_registry_typed_spawn_0_71_7.py`.

### 0.71.6 — Typed host_bind

- `host_bind` uses typed `WorkloadBearingShell` / `WorkloadEngine` / `StructureEffectPort`|`PlaceEffectPort` / `RegisteredPlaceSpawn.workload_bind`; no getattr or Protocol-isinstance duck nests. Tests: `tests/test_host_bind_typed_0_71_6.py`.

### 0.71.5 — Typed workload book row reads

- `place_registry` / `workload_place` read `Workload` / `WorkloadHandle` fields typed; they do not getattr duck-type book rows. Tests: `tests/test_workload_row_reads_0_71_5.py`.

### 0.71.4 — Typed book binds (spawn-hand discovery invert)

- `RegisteredPlaceSpawn.register_bind` / `BookBindPort`: host_bind and place_registry walk typed binds; they do not duck-walk `handles` for workload/adopt hands. Tests: `tests/test_spawn_bind_invert_0_71_4.py`.

### 0.71.3 — Compost extra place maps

- Spawn hands do not keep `place_id` → `workload_id`. Place id is the workload id. Overlay is not written for adopt/workload outcomes. Tests: `tests/test_place_maps_compost_0_71_3.py`.

### 0.71.2 — Structure registry projects the workload book

- `InProcessPlaceRegistry.places` reads adopted and `workload:` readiness from `WorkloadEngine`. Overlay stays for bare ids and failed ensures. Tests: `tests/test_place_registry_projection_0_71_2.py`.

### 0.71.1 — Adopt a named place into the workload book

- `WorkloadEngine.adopt` records an existing `WorkloadHandle.base_url` as ready. No runner `start`. Prefix `adopt:` on the structure spawn table. Tests: `tests/test_place_adopt_0_71_1.py`.

### 0.71.0 — Place registry (**theme open** · José 2026-09-20)

Vision: [VISION-0.71](docs/vision/VISION-0.71.md) · ADR [039](docs/adr/039-place-registry-adopt.md) **Proposed**

- Floor: **adopt** a named existing body. Spawn via `workload:` stays `0.63.16`.
- Package stamp stays `0.68.0`. No embedded release. Execute starts at `0.71.1`.

### 0.70 — Authoring (**theme closed** · José 2026-09-19)

Vision: [VISION-0.70](docs/vision/closed/VISION-0.70.md) · ADR [038](docs/adr/038-authoring-adapter.md) **Accepted** · Migration: [MIGRATION-0.70](docs/migrations/MIGRATION-0.70.md)

- Floor: one embedded land without Assist or Design (`0.70.1`–`0.70.2`). Last growth: `bound()` from the started host (`0.70.7`).
- Package stamp stays `0.68.0`. No embedded release.
- Residual named, not paid: working names; `LocalPalmInvoker` invert; historical `0.70.4` `create_resource`; [SD-025](TECH-DEBT.md#sd-025).

### 0.70.7 — bound() walks the started host

- `bound()` takes `DefinitionService` from the started host on the bound runtime. `land(host)` is the library door; it does not stash definitions in the kit.
- Job leaf still walks `bound().commit`. No `palm` `create_flow`. No land verbs on present.
- Tests: `tests/test_authoring_bind_ambient_0_70_7.py`.

### 0.70.6 — commit lands a resource; pack leaf publishes the snapshot

- `commit(body)` walks catalog `kind` (`flow` / `resource`). Pack submit of a `ResourceDefinition` mapping lands `authoring-snapshot`. Present starts apply; file write stays the file provider.
- No second provider action. No `palm` `create_flow`. No fifth wizard. `0.70.4` still calls `create_resource`.
- Tests: `tests/test_authoring_resource_land_0_70_6.py`.

### 0.70.5 — pack job leaf commits via the adapter

- Pack submit is a `FlowDefinition` mapping. Resource `authoring-commit` (working provider `authoring`) walks `bound().commit`. Present starts the new catalog id.
- Hole named [SD-025](TECH-DEBT.md#sd-025). No `palm` `create_flow`. No land verbs on present.
- Tests: `tests/test_authoring_job_leaf_0_70_5.py`.

### 0.70.4 — thin apply speaks a file snapshot

- Leaf commits apply via adapter (`land` / `commit` of as-built `authoring-apply`). Snapshot resource is `file` (`authoring-snapshot`); lands via `host.definitions.create_resource`.
- Apply wizard: resource step writes JSON data (`{"note": "rules-as-data"}`); confirm waits; present drives until apply `SUCCEEDED`. Pack stays waiting. Snapshot is not a `FlowDefinition` revision.
- Tests: `tests/test_authoring_apply_snapshot_0_70_4.py`.

### 0.70.3 — authoring pack

- Catalog wizard present can start and wait. Proof path: `land` / `commit` then present `start(..., by_id=True)`.
- Pack id unnamed. As-built catalog name `authoring-pack` (`examples/definitions/authoring_pack.py`). José may rename.
- Stays `WAITING_FOR_INPUT` after a text shape. No `__end__`. Not `design_entry`. No Assist contributor. Leaf apply / snapshot waits for `0.70.4`.
- Tests: `tests/test_authoring_pack_0_70_3.py`.

### 0.70.2 — present starts the committed definition

- Same embedded host: `land` / `commit` then `palm.kits.present` `start(..., by_id=True)` of the catalog id.
- No land verbs on present. Existing consume doors. `INTENTION_KITS` stays empty.
- Tests: `tests/test_authoring_present_start_0_70_2.py`.

### 0.70.1 — authoring kit (one-shot commit)

- Package **`palm.kits.authoring`** (José locked the name 2026-09-19). In `INSTALLED_KITS`.
- Library door `land(host)` holds `host.definitions`. `commit(body)` walks `create_flow`.
- Tests: `tests/test_authoring_kit_0_70_1.py` on `ApplicationHost.for_mode("test")` (embedded; no Assist; no Design).
- Handle class unnamed. `INTENTION_KITS` stays empty.

### 0.70.0 — Authoring (plan)

José opened theme **0.70**. Vision: [VISION-0.70](docs/vision/closed/VISION-0.70.md). Seed: [VISION-AUTHORING](docs/vision/VISION-AUTHORING.md). ADR [038](docs/adr/038-authoring-adapter.md) **Accepted**. Migration: [MIGRATION-0.70](docs/migrations/MIGRATION-0.70.md).

- Floor: one-shot land on `CompositionProfile.embedded()` via adapter walking `host.definitions`; present starts the landed definition.
- Execute starts at `0.70.1`. Package stamp stays `0.68.0`.
- Design stays overlay on fat phenotypes. Do not stamp `INTENTION_KITS`. Do not grow land onto present.

### 0.69 — Navigator (**theme closed** · José 2026-09-17)

Vision: [VISION-0.69](docs/vision/closed/VISION-0.69.md) · ADR [037](docs/adr/037-navigator-invert.md) **Accepted** · Migration: [MIGRATION-0.69](docs/migrations/MIGRATION-0.69.md)

- Floor: one embedded walk without Assist (`0.69.7`). Last growth: kit owns the walk-role key (`0.69.8`).
- Package stamp stays `0.68.0`. No embedded release.
- Residual named, not paid: Assist / CLI / Portal; leftover `SessionOwnershipHook`, nested park, `operator_entry` ending; unnamed handle / Protocol / env.

### 0.69.8 — kit owns the walk-role key
- Present kit owns `GUIDANCE_INSTANCE_ID` (`"guidance_instance_id"`). Session plane does not export that constant.
- `SessionService` / session plane `stamp(session_id, key, instance_id)` and `replace(...)` write a named metadata key. Degenerate allow stays owner + attached instance. No "guidance" in the session verb.
- `BoundSurface.SESSION_CONTEXT_KEYS` no longer lists the kit role key. Kit `replace_guidance_instance` stays the predicate door.
- Tests: `tests/test_present_kit_walk_role_key_0_69_8.py`. Floor walk `0.69.7` stays green.

### 0.69.7 — empty-handed start dogfood (floor proof)
- One embedded walk without Assist: bind → empty-handed `start()` of **`navigator`** → stamp `guidance_instance_id` → stay `WAITING_FOR_INPUT` → sibling `start(title)` (no job `session_id`, no `WaitInterest`) → `focus(guidance_instance_id)` home.
- Seed is `kit.guidance_definition_id = "navigator"` after bind. Empty-handed start does not start `operator-entry`. Unset kit key still refuses. `present()` of the waiting navigator has no Assist envelope.
- Tests: `tests/test_navigator_dogfood_0_69_7.py`. Phenotype `ApplicationHost.for_mode("test")` / `CompositionProfile.embedded()`. Constructor override and env spelling stay later.

### 0.69.6 — navigator wizard pack
- New catalog wizard **`navigator`** (`examples/definitions/navigator.py`) beside `operator_entry`. Definition id `navigator`.
- Stays `WAITING_FOR_INPUT` after naming work (no `__end__`). Sibling start is kit `start()` / `spawn_sibling`. Return is `focus` of `guidance_instance_id`.
- Do not copy handoff, coconut/design doors, or Assist scenario façade. Leftover `operator_entry` still ends. Floor dogfood: `0.69.7`.

### 0.69.5 — kit-contributed guidance_definition_id
- Present kit owns `guidance_definition_id` (`str | None`). Unset → no empty-handed start. Not a field on core `PalmSettings`.
- Stamp caller: after session-side attach, the kit asks `SessionService.stamp_guidance_instance` if the started definition id equals that key. Stamp if absent; replace stays explicit.
- Replace predicate: kit asks `replace_guidance_instance` only when the instance is attached and its definition id equals `guidance_definition_id`. Titles cannot become Home.
- Env spelling and constructor override stay later. New wizard pack waits for `0.69.6`.

### 0.69.4 — present kit (kit-as-composition)
- Install `palm.kits.present` (`INSTALLED_KITS`). One library object holds one `BoundSurface` and walks bind, present, submit, start, attach, focus.
- Present is `JobInspectable.inspect_job` plus wait plane `waiting_on`. Submit is `InputCapable` via runtime input. Start reuses `FlowExecutionService.spawn_sibling`.
- Handle class unnamed. Do not stamp `guidance_instance_id`. Do not seed `guidance_definition_id` (0.69.5).

### 0.69.3 — spawn without nested park
- Product door `FlowExecutionService.spawn_sibling`: start named work as a same-session sibling. Attach via `SessionService.attach_after_start`. Job stays session-ignorant.
- Guidance job stays `WAITING_FOR_INPUT`. Do not open `WaitInterest` on the sibling.
- Leftover `until_input` nested park stays. Kit `start()` waits for `0.69.4`.

### 0.69.2 — session-side attach after start
- Product door `SessionService.attach_after_start`: after execution start, attach the new instance on the bound session.
- Job stays session-ignorant: do not copy `session_id` onto the job. Attach does not stamp `guidance_instance_id`.
- Leftover `SessionOwnershipHook` (job metadata attach) stays. Kit `start()` waits for `0.69.4`.

### 0.69.1 — walk-write seam
- Named session-metadata key **`guidance_instance_id`**: `SessionService.stamp_guidance_instance` / `replace_guidance_instance` (product door) → session plane store.
- Floor allow is degenerate: owner session + attached instance. Stamp if absent; replace is explicit. Attach and focus do not stamp.
- Interface type stays unnamed until José locks it. Kit caller and definition-id replace predicate wait for `0.69.5`.

### 0.69.0 — Navigator (plan)
- José opened theme **0.69**. Vision: [VISION-0.69](docs/vision/closed/VISION-0.69.md). Seed: [VISION-NAVIGATOR](docs/vision/VISION-NAVIGATOR.md). ADR [037](docs/adr/037-navigator-invert.md) (Accepted at exit). Migration: [MIGRATION-0.69](docs/migrations/MIGRATION-0.69.md).
- Floor: one embedded walk (bind → empty-handed guidance start → stay waiting → sibling attach → focus home). Execute starts at `0.69.1`. Package stamp stays `0.68.0`.
- Assist stays. Do not pay [SD-024](TECH-DEBT.md#sd-024) as Navigator.

### Named residual
- [SD-024](TECH-DEBT.md#sd-024) — host still names wizard (`get_wizard_progress` / `list_wizard_progress_views`, job-context stitch, `current_wizard_step`). Dispatch and projection factories already walk the registry. Named, not paid. Not Navigator.

### Portal dogfood — pt-BR paint skin
- Empty `/portal/` page keeps the FAB and adds language links (`?lang=en`, `?lang=pt-BR`). Chat chrome is unchanged until a skin opens.
- Portal paints chrome, action labels, choice labels, and demo questions (operator-entry, todo-builder, coconut-npc). Values, aliases, paths, and ids stay English. Missing keys stay English.
- Optional typed synonyms (`sim` → `yes`) on the client only. Not a 0.68 compost slice.

### Portal dogfood — session vs instance slots
- Portal keeps two slots: `session_id` (system subject) and `instance_id` (continue handle). Start / Menu / Open send `clear: true` so the previous run does not stick.
- Hello auto-starts operator-entry even when Assist WS already bound a `sess-…`. Continue frames send both ids. Not a 0.68 compost slice.

## [0.68.0] — 2026-09-15

### 0.68 — The great cleansing (**theme closed** · José)

Vision: [VISION-0.68](docs/vision/closed/VISION-0.68.md) · Migration: [MIGRATION-0.68](docs/migrations/MIGRATION-0.68.md) · residual [SD-023](TECH-DEBT.md#sd-023)

- Costume composted: empty boot phase, runner `ready()` doctor, living POST lies, outbox DNA skip, empty Local ready, runner ready call, write-only RunnerApp bag, empty `palm.common.runtimes`, Pattern MCP second ready, unused webhook events, unused webhook/projection journal facades, unused work_drain journal consumer, unread parking lots, unused host query facades, living README / transform-count / L0 copy.
- Honest packaging stays: `enable_state_snapshot`, Pattern/Provider `ready()`, living projections, WorkIntent drain, two Portal slots.
- Exit residual named, not paid: MCP `experimental` = `full`; recovery webhook alias; host status triple names; `HttpWebhookDeliverer` default. Do not wire production POST.
- Stamp `0.68.0`. No open minor.

### 0.68.16 — living README / L0 continue copy
- Trim README (and copied wiki / llms snippets) to STATUS: theme **0.68** open, package `0.67.0`. Server start is `palm host server`. Resource inspect is REPL-only.
- Lock one transform count: **24** installed builtins (`append_item`, `put_resource`, `count_by` on the tuple). Catalog drops gated `parquet_load`. Do not un-gate parquet.
- L0 `palm_assist` continue example uses `instance_id`, not `session_id` + `inst-1`. FastMCP kwargs unchanged. Package stamp stays `0.67.0`.

### 0.68.15 — unused host query facades
- Drop `host.instances` / `jobs` / `wizards` grouping objects. Flat list/get methods stay. CLI already used the flats.

### 0.68.14 — unread parking lots and skip stubs
- Drop unread `palm.system.ports` / `planes` / `supervisor` re-export shims, `palm.utils`, `palm.patterns.dag.flow` placeholder, `kits.doctor_section`, and vitality skip stubs `boot_membership` / `system_log_tail`.
- `monitor_agent` stays parked. Canonical homes stay. Closed chronicles stay. Package stamp stays `0.67.0`.

### 0.68.13 — unused work_drain journal consumer
- Drop `mark_work_drain_caught_up`, doctor consumer name `"work_drain"`, and host `redrive_journal` (coordinator twin included). Nothing in product advanced the offset. The body counted journal entries; drain still uses the WorkIntent store.
- Work-drain organ stays. `EventJournal.redrive` stays. Do not wire journal consume into drain. Package stamp stays `0.67.0`.

### 0.68.12 — unused projection journal facade
- Drop `drain_journal_projections`, `consume_for_projections`, and the doctor consumer name `"projections"`. Nothing in product called the host method. The body counted journal entries; it did not rebuild.
- Living projections organ stays. `work_drain` stays. `HttpWebhookDeliverer` stays. Package stamp stays `0.67.0`.

### 0.68.11 — unused webhook journal facade
- Drop `drain_journal_webhooks`, `consume_for_webhooks`, and the doctor consumer name `"webhooks"`. Nothing in product called the host method. The body counted journal entries; it did not POST.
- Do not wire `dispatch`. Projection journal drain stays. `HttpWebhookDeliverer` stays. Package stamp stays `0.67.0`.

### 0.68.10 — unused host webhook events
- Drop unused `HostEventType.WEBHOOK_DELIVERED` / `WEBHOOK_FAILED` and dashboard paint for those names. Nothing emitted them.
- Do not wire production POST. `HttpWebhookDeliverer` stays. Package stamp stays `0.67.0`.

### 0.68.9 — Pattern MCP second ready() call
- Drop the extra `app.ready()` loop in `register_pattern_mcp_tools`. Autoload still runs `PatternApp.register` → `ready()`. MCP drains `iter_mcp_contributors`.
- Pattern and provider `ready()` stay. Package stamp stays `0.67.0`.

### 0.68.8 — empty common.runtimes parking lot
- Drop `palm.common.runtimes` (empty after 0.68.2). Living runtime is `palm.system.runtime`. Server kit stays `palm.kits.server`.
- Pattern and provider `ready()` stay. Package stamp stays `0.67.0`.

### 0.68.7 — write-only RunnerApp bag
- Drop `RunnerApp`, `palm.runners._registry`, and the three runner `app.py` postcards. Autoload still registers `WorkloadRuntime` classes into `workload_runtime_registry`.
- Pattern and provider `ready()` stay. Package stamp stays `0.67.0`.

### 0.68.6 — runner ready() call
- Drop `RunnerApp.ready()` and the call from `register()`. Runner autoload stores the manifest only.
- Pattern and provider `ready()` stay. Do not dissolve the write-only runner app bag. Package stamp stays `0.67.0`.

### 0.68.5 — empty local runner ready()
- Drop `LocalRunnerApp.ready()` empty override. All runner apps inherit the optional `RunnerApp.ready()` hook.
- Do not delete the hook. Do not add a Vitality runner probe. Package stamp stays `0.67.0`.

### 0.68.4 — DNA-shaped outbox skip
- `system.outbox.wire` skips `capability_off:outbox` when DNA omits `outbox`. Drop `enable_event_outbox` from settings, start options, and host spawn.
- Explicit `host.start(enable_event_outbox=…)` no longer overrides DNA. Keep `enable_state_snapshot`. Package stamp stays `0.67.0`.

### 0.68.3 — living POST lies
- Trim living docs that promised webhook POST (`ARCHITECTURE.md` capability table, README / llms “what works today”). Production outbox drain still ACKs without HTTP.
- Retune the `on_before_publish` test as a hook, not a drain. Do not wire production POST. Package stamp stays `0.67.0`.

### 0.68.2 — runner ready() doctor register
- Drop `HostRunnerApp` / `NeonrootRunnerApp.ready()` doctor side-effects. `WorkloadEngine.doctor()` already samples runner seats.
- Drop `palm.common.runtimes.doctor_contributors`, runner `doctor.py` helpers, and anatomy bags `neonroot` / `workload_host`. CLI doctor reads neonroot from `workloads`.
- Do not add a Vitality runner probe. Package stamp stays `0.67.0`.

### 0.68.1 — empty projections boot phase
- Drop `host.projections.attach` and `_attach_projections`. The DNA hand already attaches; host slots alias in product wire.
- Drop unread `build_host_projections` / `register_host_projections` / `HostProjections`. Pattern extras stay `build_pattern_projections`.
- Inventory and 0.59 dogfood pins retune onto `admission.has_capability("projections")`. Closed 0.59 chronicle stays.
- Package stamp stays `0.67.0`.

### 0.68.0 — the great cleansing (plan)
- José closed 0.67 and opened 0.68: compost remaining costume after assembly dependents.
- Named remaining: empty `host.projections.attach`, bare `enable_event_outbox`, runner `ready()` doctor callbacks, living POST lies, twin seats that pin empty work.
- Not delivery POST. Not 0.56 spawn. `enable_state_snapshot` stays read packaging.
- Package stamp stays `0.67.0` until 0.68 exit.

## [0.67.0] — 2026-08-21

### 0.67 — Dependents require the organ (**theme closed** · José)

Vision: [VISION-0.67](docs/vision/closed/VISION-0.67.md) · ADR: [036](docs/adr/036-require-capability.md) **Accepted** · Migration: [MIGRATION-0.67](docs/migrations/MIGRATION-0.67.md)

- Two doors: `require_business_admission` (ready) and `require_capability` (ready then installed name).
- Work-plane / host `able` is drain membership; wait stays ready. Surfaces speak `capability_refused`.
- Journal, projections, compensation, webhook, analytics: DNA list + attach hand + leftover one object.
- Unread `enable_compensation` / `enable_webhook_dispatcher` composted.
- Remaining costume (empty boot phases, bare `enable_event_outbox`) waits in 0.68.

### 0.67.17 — analytics leftover (one organ)
- Analytics is one organ on the install board. The host slot reads that object. `analytics_enabled` refines it. Composition services do not keep a twin when DNA omits. Not a supervisor loop.

### 0.67.16 — analytics DNA + attach hand
- `analytics` is name + attach hand + omit. DNA lists it on `local.cli` / `server` / `all_in_one` / `mcp`; `embedded` / `worker` omit.
- Admission reads `has_capability("analytics")`, not `composition.has`. Composition/seed no longer write the name.
- Not a no-op organ. Product `AnalyticsService` vs install-board attach is leftover. `analytics_enabled` stays product packaging. Not all of SD-021. Package stamp stays `0.66.0`.

### 0.67.15 — unread-flag compost
- `PalmSettings` drops unread `enable_compensation` and `enable_webhook_dispatcher`. Membership is DNA.
- Dead `attach_runtimes` on compensation and projections is gone. Living docs no longer wire those organs from a flag.
- Package stamp stays `0.66.0`.

### 0.67.14 — webhook leftover (one dispatcher)
- Webhook is one install dispatcher. The host slot reads that object. Recover refines URLs on it. Empty URLs keep empty targets. Not a supervisor loop and not a recover twin.
- Production outbox drain does not POST. Package stamp stays `0.66.0`.

### 0.67.13 — webhook DNA + attach hand
- `webhook` is name + attach hand + omit. DNA lists it on `local.cli` / `server` / `all_in_one` / `mcp`; `embedded` / `worker` omit.
- Recover reads `has_capability("webhook")`, not `composition.has`. Composition/seed no longer write the name.
- Not a no-op organ. Recovery-built dispatcher vs install-board attach is leftover. Settings URLs still refine. Not all of SD-021. Package stamp stays `0.66.0`.

### 0.67.12 — compensation leftover (one organ)
- Compensation is one attach on the runtime bus. The recovery slot reads that object. Drop-on-omit unsubscribes. Not a supervisor loop and not a second interceptor on `host.event`.
- Package stamp stays `0.66.0`.

### 0.67.11 — compensation DNA + attach hand
- `compensation` is name + attach hand + omit. DNA lists it on `local.cli` / `server` / `all_in_one` / `mcp`; `embedded` / `worker` omit.
- Recover reads `has_capability("compensation")`, not `composition.has`. Composition/seed no longer write the name.
- Not a no-op organ. Dual-attach of `host.event` vs runtimes is leftover. Not all of SD-021. Package stamp stays `0.66.0`.

### 0.67.10 — projections leftover (one organ)
- Projections is one attach on the runtime bus. Host slots read that object. Drop-on-omit unsubscribes. Not a supervisor loop and not a second interceptor on `host.event`.
- Package stamp stays `0.66.0`.

### 0.67.9 — projections DNA + attach hand
- `projections` is name + attach hand + omit. DNA lists it on `local.cli` / `server` / `all_in_one` / `mcp`; `embedded` / `worker` omit.
- Host attach reads `has_capability("projections")`, not `composition.has`. Composition/seed no longer write the name.
- Not a no-op organ. Dual-attach of `host.event` vs runtimes is leftover. Not all of SD-021. Package stamp stays `0.66.0`.

### 0.67.8 — journal leftover (one organ)
- Journal is one attach on the runtime bus. The host slot reads that object. Drop-on-omit unsubscribes. Not a supervisor loop and not a second interceptor on `host.event`.
- Package stamp stays `0.66.0`.

### 0.67.7 — journal DNA + attach hand
- `journal` is name + attach hand + omit. DNA lists it on `local.cli` / `server` / `all_in_one` / `mcp`; `embedded` / `worker` omit.
- Host attach reads `has_capability("journal")`, not `composition.has`. Composition/seed no longer write the name.
- Not a no-op organ. Not all of SD-021. Package stamp stays `0.66.0`.

### 0.67.6 — vitality work_cycle drain proofs
- Vitality `work_cycle` drain proofs pin `local.cli`. Embedded ready still enqueues; tick does not process.
- Package stamp stays `0.66.0`.

### 0.67.5 — schedule fire uses drain able
- Work-plane `tick_schedules` uses the same able query as `tick` (`started ∧ ready ∧ work_drain`). Host `tick_work` follows. Ready without the organ does not advance the schedule clock.
- Package stamp stays `0.66.0`.

### 0.67.4 — capability refused surface voice
- Surfaces map `CapabilityRefusedError` to `capability_refused` (REST/MCP **409**, CLI/SSR/WS brand). Not a 500 and not `admission_refused`.
- Existing start/continue handlers pick up REST/MCP via the current maybe-helpers. Package stamp stays `0.66.0`.

### 0.67.3 — host start_ports.able is drain
- Host `start_ports.able` is `started ∧ ready ∧ work_drain`. Wait uses a ready-only sibling (`install_admission_able`).
- Spawn no longer shares one `_started` override onto both planes. Package stamp stays `0.66.0`.

### 0.67.2 — work-plane able is drain
- Install-board `able` closes over `has_capability("work_drain")` after ready.
- Wait / continue keeps the ready query (`admission_able`). Ready is not membership.

### 0.67.1 — require_capability
- Sibling door `require_capability(source, name)` beside ready-only `require_business_admission`.
- Not ready → `AdmissionRefusedError`. Ready but organ missing → `CapabilityRefusedError` (snapshot + name).
- Drain-shaped proof: require `work_drain`; ready without the organ is not membership.

- **CLI doctor uses InspectService.doctor.** One bag with REST / assist / MCP. Host binds `application_host` at spawn; REST no longer assigns it per request.
- CLI doctor `--format json` emits that bag. Anatomy / admission / neonroot / CS-002 tables render from it. Instance list and definition catalog stay as operator extras.
- NeonRoot is a WorkloadRuntime only. Composition no longer lists `neonroot`. Settings drop `enable_neonroot_runners`. Doctor reports registered / available / health; it does not invent “declared but missing.”

## [0.66.0] — 2026-08-20

### 0.66 — Admission sits on capabilities (**theme closed** · José)

Vision: [VISION-0.66](docs/vision/closed/VISION-0.66.md) · ADR: [035](docs/adr/035-admission-sits-on-capabilities.md) **Accepted** · Migration: [MIGRATION-0.66](docs/migrations/MIGRATION-0.66.md)

- `AdmissionSnapshot` publishes installed `capabilities` / `has_capability`.
- Seat overlays materialized names after assemble. Engine does not walk.
- Eyes (packaging, doctor, vitality load) show the list. `admission_as_dict` replaces 3-key remain menus.
- Ready stays the short wall. Step 4 dependents (`able`, `require(organ)`) wait.

## [0.65.0] — 2026-08-18

### 0.65 — Outbox as the proof cut (**theme closed** · José)

Vision: [VISION-0.65](docs/vision/closed/VISION-0.65.md) · ADR: [034](docs/adr/034-supervised-start-walks-registration.md) **Accepted** · Migration: [MIGRATION-0.65](docs/migrations/MIGRATION-0.65.md)

#### Plan (0.65.0)
- **Theme open** — outbox copies the 0.64 home (name + hand + omit)
- Floor: invert `system.background.start`; grow seats; same phenotypes as drain; old walkers die with the hand
- Locks (José): invert first; list `outbox` on cli/server/all_in_one/worker; omit embedded/mcp
- Execution starts at `0.65.1`

#### 0.65.1 — invert start
- `system.background.start` walks registration + `may_start`
- Skip `none_registered` / `none_ready`
- `CapabilitySeats` carries `outbox_store` / `outbox_processor`

#### 0.65.2 — outbox hand + DNA
- DNA lists `outbox` on cli / server / all_in_one / worker; omits embedded / mcp
- Hand `apply_outbox` is the only register; freelance catalog is empty
- Host recover does not start the loop; `enable_outbox_service` and `enable_outbox_background` are gone
- Host store wire follows DNA listing; explicit `enable_event_outbox` still wins

#### 0.65.3 — leftover cleanup
- Delete unused `OUTBOX_SERVICE` recipe (hands call `register_outbox`)
- `phase_outbox` module doc and SD-021 progress name DNA listing, not composition
- Strip dead `enable_outbox_service=False` test kwargs
- Appendix freelance catalog / B1: default catalog is empty

#### 0.65.4 — surface / comment costume
- CLI `palm host master` is command acceptance, not an outbox processor
- Drop unused `host.outbox.processed` event name
- Host notes and ARCHITECTURE no longer treat host as the outbox owner

#### Exit
- ADR-034 **Accepted**. Theme closed at `0.65.0`. Journal / webhook / admission remain later.

## [0.64.0] — 2026-08-18

### 0.64 — First capability (**theme closed** · José)

Vision: [VISION-0.64](docs/vision/closed/VISION-0.64.md) · ADR: [033](docs/adr/033-one-walker.md) **Accepted** · Migration: [MIGRATION-0.64](docs/migrations/MIGRATION-0.64.md)

- **`work_drain` is copyable.** Name + hand + omit. José closed the theme.
- ADR-033 **Accepted** — old wiring dies in the same cut.
- Spine: definition lists the name; walker loops `LOCAL_CAPABILITY_HANDS`; one start (`system.background.start`). Host does not start drain.
- Costume gone: composition does not type the name; assemble/seed/refuse do not shovel a capabilities bag; `WORK_DRAIN_SERVICE` deleted.
- Structure identifiers (DNA env, packages, `Structure*`) replace assembly names. No aliases.
- Doctor JSON: vitality seat raw does not stash bound methods.

### 0.63.39 — work_drain materialize
- `AssemblyDefinition.capabilities` — builtin DNA lists `work_drain` on cli/server/all_in_one/worker (not embedded/mcp)
- Structure manager materializes `work_drain` (supervisor register) only when DNA lists it
- Host and system background start read DNA, not `composition.has("work_drain")` or `BootMode.allow_background_drain`
- Theme stamp (stay 0.63 vs open 0.64) still open

## [0.63.0] — 2026-08-08

### 0.63 — Organism assembly (**theme open**)

Vision: [VISION-0.63](docs/vision/closed/VISION-0.63.md) · seed: [VISION-ASSEMBLY](docs/vision/VISION-ASSEMBLY.md) · ADR: [032](docs/adr/032-organism-assembly.md) **Accepted** · Migration: [MIGRATION-0.63](docs/migrations/MIGRATION-0.63.md)

#### Plan (0.63.0)
- **Theme open** — DNA · admission gate · single readiness · purge pretenders  
- Floor: core assembly + **embedded** DNA + one citizen fail-closed + coherence suite (truth instrument)  
- Growth: cli/server DNA · more citizens · seed map · intents · eyes present  
- Unplanned reserve slices for break inventory (unknown impact allowed)  
- Env = seed + packaging; not dual structure king  
- Debt named: **SD-020** (dual readiness) · **SD-021** (profile/env structure dual)  
- Exit: **José** when readiness feels proper  

#### Core floor (0.63.1)
- **`palm.core.assembly`** — `AssemblyDefinition` / `local_embedded`, `AssemblyStatus` / `AdmissionSnapshot`, closed `EffectIntent` + `Observation`, `AssemblyEngine`  
- Pure reconciler: receive definition → tick → ready (empty places) · ensure_place intents · truth-home / place block · new definition invalidates  
- Fail closed when empty or not ready; pure tests in `tests/core/test_assembly_engine.py`  

#### System household (0.63.2)
- **`palm.system.assembly`** — `AssemblySeat`, effect port, assemble loop  
- Boot phase **`system.assembly.assemble`** after `system.ready` (before background)  
- Default DNA **`local.embedded`** → shell `runtime.admission.may_run_business`  
- Options: `assembly_skip`, `assembly_dna_id` / `assembly_definition`, `assembly_max_ticks`  
- Fail closed when skip or no seat; tests `tests/test_assembly_system_0_63_2.py`  

#### Raise the gate (0.63.3)
- Work-plane **citizen path**: install `able` = machine started **and** `admission.may_run_business`  
- Fail closed when assembly skipped, blocked, or truth home down — `tick` processes 0; enqueue may wait  
- `WorkPlaneService.is_able` / status `able`; tests `tests/test_assembly_gate_0_63_3.py`  
- **Break inventory (pretenders still open):** direct `submit_flow` / product start doors / assist without admission check; host soft-ready flags; tests that force `able=True`  

#### Coherence + submit citizens (0.63.4)
- **`AdmissionRefusedError`** + `require_business_admission` — `DefinitionExecutor` submit_flow/process fail closed  
- Coherence suite: `tests/assembly/` · `just guard-assembly` · wired into `just check`  
- Work plane + submit share one admission law  
- Residual pretenders: assist/MCP packaging soft-ready; host dual flags; SD-021 seed map  

#### DNA seed map (0.63.5)
- Builtin DNA: `local.embedded` · `local.cli` · `local.server` · `local.all_in_one` · `local.worker` · `local.mcp`  
- `resolve_builtin_dna` · `palm.system.assembly.seed` — mode/composition → decree  
- Host `system.spawn` seeds DNA unless caller set `assembly_dna_id` / definition  
- Profiles remain seed choosers, not parallel structure kings after load  

#### Refuse policy (0.63.6)
- Pure `refuse_violations` — DNA refuse vs surfaces/capabilities  
- Structure policy observations block admission when membership lies  
- Host seed passes membership facts into assemble  

#### Eyes (0.63.7)
- Vitality seat **`assembly`** — samples admission + definition id  
- `may_run_business` false → degraded state (honest eyes)  

#### Kingdom inventory (0.63.8)
- `kingdom_map` / `kingdom_snapshot` — gated citizens vs pretender edges  
- Host packaging nests admission pointer (not a second ready flag)  
- `ApplicationHost.admission` → primary runtime snapshot  

#### CLI dogfood wall (0.63.9)
- `create_cli_host` seeds **BootMode.cli** → DNA **local.cli** (refuse server_surfaces)  
- Matches `palm` terminal entry to assembly law  

#### Operate eyes admission (0.63.10)
- `present_top` / `present_vitality` nest living **admission** snapshot  
- Assist/inspect operate paths show the gate without inventing soft ready  

#### Place book hands (0.63.11)
- `InProcessPlaceBook` + `PlaceBookEffectPort` — ENSURE/RELEASE place  
- Default assembly seat hands; DNA with `places_required` can converge  

#### Deployment walls (0.63.12)
- `boot_mode_name_for_deployment` — server/worker/all_in_one/cli seed names  
- Host without BootMode: profile seeds composition + DNA (server → local.server)  

#### Env structure seed (0.63.13) — SD-021 growth
- **`PALM_ASSEMBLY_DNA_ID`** / `settings.assembly_dna_id` — explicit DNA seed (wins over mode/composition)  
- Host spawn always seeds membership for refuse (caller DNA override no longer hides dual shape)  
- Continuous work_drain respects DNA refuse `background_drain` (env/composition cannot peer-law)  
- Cartography: `STRUCTURE_SEED_ENV` · pretender `env.structure_toggles` → partial_0_63_13  

#### Place spawn port (0.63.14)
- **`PlaceSpawnPort`** + `InProcessPlaceSpawn` (default) + `RegisteredPlaceSpawn`  
- `PlaceBookEffectPort` calls spawn hands before ledger mark — fail closed on spawn fail  
- **`os:`** prefix via `os_prefix_spawn_port` — fail closed without body handle (no soft place)  
- Residual: real OS process / workload runner wire  

#### Household hands + OS process (0.63.15)
- **`HouseholdEffectPort`** — default seat hands: places + invalidate/refresh projection, apply policy, request seed  
- **`OsProcessRegistry`** — real `subprocess` for `os:` when `argv`/`command` given; release terminates process group  
- Seat/phase default household; residual: workload place-book wire  

#### Workload place book (0.63.16)
- **`WorkloadPlaceSpawn`** — `workload:` places via WorkloadEngine (fail closed unbound)  
- Default kind **workspace** (warm body); `kind=run` needs argv  
- `combined_structure_spawn_port` — `os:` + `workload:` on one port  
- Residual: host auto-bind engine into default assembly seat  
- `run_host` accepts optional boot_mode; deployment still seeds when omitted  

#### Host structure bind (0.63.17)
- **`bind_host_structure_to_seat`** / **`default_household_effects`** — combined place spawn on assemble  
- Default host path binds live **`shell.workload`** after engines init  
- Opt-out: **`assembly_bind_workload=False`** (workload: stays fail-closed)  
- Does not clobber recording / custom effect ports without a place book  
- Coherence: `tests/assembly/test_host_bind_0_63_17.py` · residual place_book.os_spawn paid  

#### Reassemble edges (0.63.18)
- **`AssemblySeat.reassemble`** — named re-converge (DNA and/or membership)  
- **`receive_definition(force=)`** · **`AssemblyEngine.invalidate()`**  
- Assemble always clears refuse then re-checks membership (heal + worsen)  
- Fail closed while invalidated; place-gone recovers via reassemble  
- Coherence: `tests/assembly/test_reassemble_0_63_18.py`  

#### Membership seed catalog (0.63.19) — SD-021 residual
- **`MEMBERSHIP_CAPABILITY_SEEDS`** — full enable_* / analytics → capability map (compensation, outbox, webhook, work_drain, analytics, neonroot)  
- **`membership_capabilities_from_settings`** — bootstrap single source for composition resolve  
- **`STRUCTURE_SEED_ENV`** expands with all membership seeds + packaging spirit notes  
- Kingdom: `env.membership_seed_catalog` gated · `env.structure_toggles` paid_catalog · outbox start-option residual named  
- Coherence: `tests/assembly/test_membership_seed_0_63_19.py`  

#### Workload start citizen (0.63.20)
- **`BaseRuntime.start_workload`** — `require_business_admission` before engine (product / graph citizen)  
- Household place-book still uses **`WorkloadEngine` directly** (not forced through ExecutionPort gate)  
- Coherence: `tests/assembly/test_workload_start_gate_0_63_20.py`  

#### Assist start citizen (0.63.21)
- **`AssistScenarioService.start`** — product scenario start fails closed on admission  
- **Menu open→flow create** — same gate before create dispatch  
- **Menu honesty** — nests `admission`, `start_allowed`; no Operator-entry start CTA when closed  
- Kingdom pretender `assist.soft_catalog` → paid_start_0_63_21  
- Coherence: `tests/assembly/test_assist_start_gate_0_63_21.py`  

#### Assist admission oath (0.63.22) — peasants' fealty / SD-016 boy-scout
- **`AssistService.admission_source`** inject + **`admission_gate()`** published gate  
- Host packaging wires snapshot factory once; citizen doors use gate (not `resolve_runtime` dig)  
- **`coerce_admission_snapshot`** — snapshot · zero-arg factory · object with `.admission`  
- Scenario start / open→create / menu eyes share the oath path  
- Kingdom: `assist.admission_oath` gated · pretender soft_catalog → paid_oath_0_63_22  
- Coherence: `tests/assembly/test_admission_oath_0_63_22.py`  

#### Work-plane able fail-closed + access helper (0.63.23)
- **Able default False** — construct / attach omit / `set_able(None)` / install missing able refuse (was soft-open True)  
- Runtime still binds `started ∧ admission` on real install  
- **`admission_source_from_runtime_resolver`** — packaging helper; shape without product service base  
- Host soft “definitions ready” dual **named** residual (packaging eyes only)  
- Kingdom: `work_plane.able_fail_closed` gated · pretenders paid/named  
- Coherence: `tests/assembly/test_able_fail_closed_0_63_23.py`  

#### Resource invoke citizen (0.63.24)
- **`BaseRuntime.invoke_resource`** — `require_business_admission` before resource engine (product / graph citizen)  
- Direct **`ResourceEngine.invoke`** stays ungated (unit / non-port path — not ExecutionPort)  
- Kingdom: `execution.invoke_resource` gated  
- Coherence: `tests/assembly/test_invoke_resource_gate_0_63_24.py`  

#### Product continue + name not-this-door residuals (0.63.25)
- **`resume_job`** / **`provide_input`** — admission fail closed (product continue citizens)  
- **Named residual on SD-020 / inventory:** WorkloadEngine dig · ResourceEngine dig · wait-plane → `orchestration.resume_job` spine  
- Law: “not this door” must be **named debt**, not silent dual  
- Kingdom: `execution.resume_job` · `runtime.provide_input` gated; dig pretenders `named_0_63_25`  
- Coherence: `tests/assembly/test_continue_gates_0_63_25.py`  

#### Wait-plane continue able (0.63.26)
- **WaitPlaneService.able** — match→resume fails closed when not able (owner → `AdmissionRefusedError`)  
- Install binds same **`started ∧ admission`** able as work plane; omit / `set_able(None)` refuse  
- Target **fail** still applies (completer failure is not a soft resume dig)  
- Residual **`wait_plane.orch_resume_dig`** → paid  
- Coherence: `tests/assembly/test_wait_plane_able_0_63_26.py`  

#### Workload exec citizen (0.63.27)
- **`BaseRuntime.exec_workload`** — `require_business_admission` before engine exec (product / graph citizen)  
- Direct **`WorkloadEngine.exec`** stays ungated (unit / non-port)  
- **`stop_workload`** stays ungated for shutdown/cleanup — **named** residual (`execution.stop_workload_ungated`)  
- Coherence: `tests/assembly/test_exec_workload_gate_0_63_27.py`  

#### Host outbox composition king (0.63.28) — SD-021 packaging dual
- Host **`system_spawn`** sets `enable_event_outbox` from **`composition.has("outbox")`** when not explicit  
- Settings flag seeds composition at resolve only — not peer OR for store wire on host path  
- Explicit `host.start(enable_event_outbox=…)` still overrides (named)  
- Bare `BaseRuntime.start(enable_event_outbox=…)` remains packaging residual  
- Kingdom: `host.outbox_composition_king` gated · `outbox.start_option_seed` paid_host · bare residual named  
- Coherence: `tests/assembly/test_outbox_composition_king_0_63_28.py`  

#### Assist continue citizens (0.63.29)
- **`AssistSession.input` / `resume` / `backtrack`** — `require_business_admission(admission_gate())` (oath; product continue)  
- **`resume_process`** cartography as citizen (already gated via executor `_require_runtime` since 0.63.4)  
- **`AssistSession.cancel`** stays ungated for operator stop — **named** residual  
- Kingdom: `assist.continue_session` · `executor.resume_process` gated; `assist.session_cancel_ungated` named  
- Coherence: `tests/assembly/test_assist_continue_gate_0_63_29.py`  

#### Flow continue citizens + cancel residual (0.63.30)
- **`FlowSession.input` / `resume` / `backtrack`** — `require_business_admission(flows.admission_gate())`  
- **`FlowExecutionService.admission_source` inject** + `admission_gate()` (same helper as assist; no product base)  
- Host providers wire inject for flows  
- **`cancel_job` / FlowSession.cancel** stay ungated — **named** residual (`runtime.cancel_job_ungated` · `flows.session_cancel_ungated`)  
- Kingdom: `flows.continue_session` · `flows.admission_oath` gated  
- Coherence: `tests/assembly/test_flows_continue_gate_0_63_30.py`  

#### Execution product façade oath (0.63.31)
- **Workload** `start` / `exec` · **Provider** `invoke` · **Process** `prepare` / `submit` / `run` — edge `admission_gate()`  
- Host shares one **`admission_source`** inject across execution façades  
- Workload product **stop/cancel** stays ungated — **named** residual  
- Kingdom: `execution.product_facade_oath` gated · façade edge paid · stop residual named  
- Coherence: `tests/assembly/test_execution_facade_oath_0_63_31.py`  

#### Flow product start oath (0.63.32)
- **`submit_flow_body` / `run_wizard` / `run_flow`** — edge `admission_gate()` (continue already **0.63.30**)  
- LIST / DESCRIBE soft catalog stays ungated — **named** residual  
- Kingdom: `flows.start_session` gated · start edge paid · soft catalog named  
- Coherence: `tests/assembly/test_flows_start_gate_0_63_32.py`  

#### Host packaging market-day (0.63.33)
- **ApplicationHost** `submit_flow` / `submit_process` / `provide_input` / `resume_process` / `invoke_resource` — admission edge  
- **CQRS** SubmitFlow/Process · ProvideInput · ResumeProcess · PreparePlans · SubmitPlans — same law  
- CancelJob stays control residual; kernel/runtime dig **named** residual (port still gates)  
- Kingdom: `host.packaging_market_day` gated · packaging edge paid · kernel dig named  
- Coherence: `tests/assembly/test_host_packaging_gate_0_63_33.py`  

#### Surface fealty (0.63.34)
- **CLI** `resume_job` / resource invoke → host packaging (not kernel dig)  
- **SSR explorer** invoke / resume_wizard → host or admit+port  
- **Wizard CQRS** Provide / Backtrack edge admission  
- **`host.resume_job`** packaging continue door  
- Kingdom: `surface.fealty` gated · surface edge paid  
- Coherence: `tests/assembly/test_surface_fealty_0_63_34.py`  

#### REST admission voice (0.63.35)
- **`errors.admission_refused`** — HTTP **503**, code **`admission_refused`** (not 500 `submit_failed`)  
- **`maybe_admission_refused`** on assist / flows / processes / providers / workloads / jobs / plans / instances market-day + continue handlers  
- Gate already raised under product/port; REST surface now speaks honest closed-gate voice  
- Kingdom: `surface.rest_admission_voice` gated · edge paid  
- Coherence: `tests/assembly/test_rest_admission_voice_0_63_35.py`  

#### MCP + WebSocket admission voice (0.63.36)
- **MCP** `admission_refused_error` / `maybe_admission_refused_error` → **PalmRestError 503** `admission_refused`  
- In-process market-day + continue: create/submit/input/resume/backtrack/plans/invoke/assist_dispatch  
- **WebSocket assist** maps `AdmissionRefusedError` → error code **`admission_refused`** (not `internal`)  
- HTTP MCP inherits REST voice via bridge  
- Kingdom: `surface.mcp_ws_admission_voice` gated · edge paid  
- Coherence: `tests/assembly/test_surface_admission_voice_0_63_36.py`  

#### CLI + SSR explorer admission voice (0.63.37)
- **CLI** — `print_cli_error` / `format_cli_error` brand closed gate as **`admission_refused`** on market-day and continue commands (assist, flow, process, resume, input, wizard, resource invoke)
- **SSR explorer** — `operator_error_text` prefixes **`admission_refused:`** on submit/provide/resume/assist/resource invoke banners
- Wizard backtrack catches **RuntimeError** so closed gate is honest voice, not unhandled 500
- Kingdom inventory · tests `test_cli_ssr_admission_voice_0_63_37.py`

#### Exit residual ledger (0.63.38)
- **`open_pretender_edges` / `paid_pretender_edges`** — named open vs paid cartography  
- **`kingdom_map`** — `open_residuals` · `open_residual_ids` · `open_residual_count` · `paid_edge_*`  
- **Doctor** — Assembly admission table + open residual ids (exit map, not dual ready)  
- **Packaging bag** nests open residual counts; REPL outer catch uses admission voice  
- Coherence: `tests/assembly/test_exit_residual_ledger_0_63_38.py`

## [0.62.8] — 2026-08-04

### 0.62 — Multi-claimer work drain (**theme closed**)

Vision: [VISION-0.62](docs/vision/closed/VISION-0.62.md) · ADR: [031](docs/adr/031-multi-claimer-work-drain.md) **Accepted** · Migration: [MIGRATION-0.62](docs/migrations/MIGRATION-0.62.md) · Release: [RELEASE-0.62.8](docs/releases/RELEASE-0.62.8.md)

#### Theme exit (0.62.8)
- **ADR-031 Accepted** — José judged in-process capacity proper  
- Residual named: **SD-019** (multi-process shared claim needs storage CAS); one drain owner per store  
- Stamp `0.62.8` · [WORK-DRAIN](docs/WORK-DRAIN.md) knobs · migration + release notes  

#### Plan (0.62.0)
- **Theme open** — exclusive claim first, then multi-claimer drain under supervisor  
- Floor: claimer/lease + reclaim (same API at `workers=1`)  
- Growth: N workers · drive concurrency · vitality **1 vs K**  
- Residual: multi-process shared claim needs storage CAS (not floor)  

#### Floor (0.62.1–0.62.3) — exclusive claim
- Core `WorkIntent.claimed_by` / `lease_until`  
- `WorkIntentStore`: store lock · exclusive `claim_due(claimer_id=…)` · `reclaim_expired` · owner-aware ack/fail  
- `WorkPlaneService.tick` passes claimer + reclaim; status exposes claim heat  
- Concurrent claim tests — two claimers never share one intent (**SD-017** ✅)

#### Growth (0.62.4) — N drain workers
- Plane-owned `workers` (default **1**); distinct claimer ids per thread  
- Settings: `work_drain_workers` · `work_drain_lease_seconds`  
- Install options + host coordinator rebind  
- Multi-worker background drain test

#### Honesty + proof (0.62.5–0.62.6)
- Product honesty: claim pool ≠ host-core job parallelism (GIL)  
- `run_benchmark(..., workers=K)` multi-claimer `work_cycle` · wall_ms in recipe_meta

#### Concurrent job drive (0.62.7)
- **OrchestrationEngine** — `RLock` on job membership; `begin_drive` / `end_drive` exclusive drive per job; `apply_result` status under lock  
- **`drive_job`** — acquires exclusive drive; returns `False` on conflict (safe double-queue drop)  
- **QueuedScheduler** — worker **pool** (`workers=N`, default **1**); one sentinel per worker on shutdown  
- Settings: `queued_workers` / `PALM_QUEUED_WORKERS` · `resolve_scheduler` wires pool  
- Tests: concurrent submit, exclusive drive, multi-worker overlap (**SD-018** ✅)  
- Honesty: drive pool = job **overlap** under I/O/wait — not host-core pattern parallelism

## [0.61.13] — 2026-08-04

### 0.61 — Living-kernel vitality (**theme closed**)

Vision: [VISION-0.61](docs/vision/closed/VISION-0.61.md) · ADR: [030](docs/adr/030-system-vitality.md) **Accepted** · Migration: [MIGRATION-0.61](docs/migrations/MIGRATION-0.61.md) · Release: [RELEASE-0.61.13](docs/releases/RELEASE-0.61.13.md)

#### Theme exit (0.61.13)
- **ADR-030 Accepted** — José judged eyes proper  
- Residual named: **BI-015**, **SD-016**, enrich/catalog packaging, BI-003 growth, `monitor_agent`, surface deflation  
- Stamp `0.61.13` · neighbor BI-003 product packaging floor under theme

#### Added / paid (0.61.0–0.61.13)
- **`palm.system.vitality`** — seat walk, seat reports (`palm.seat_report/1`), projection + registry  
- **`emission_window`** · **`process_resources`** · **`loaded_bulk`** · **`benchmark`** (off everyday top)  
- **InspectService** product door (**SD-007**) — top / vitality / benchmark present  
- **Doctor demotion (OD-001)** · **host status packaging (CS-002)**  
- CLI human units + recipes (`work_cycle` default)  
- Plane-only work drain (host `WorkDrainService` removed)  
- Shared `apply_product_packaging` (host + host-less ServerContext)

## [0.60.9] — 2026-08-01

### 0.60 — System Supervisor + Work Plane (**theme closed**)

Vision: [VISION-0.60](docs/vision/closed/VISION-0.60.md) · ADR: [029](docs/adr/029-system-supervisor.md) **Accepted** · Migration: [MIGRATION-0.60](docs/migrations/MIGRATION-0.60.md) · Release: [RELEASE-0.60.9](docs/releases/RELEASE-0.60.9.md)

#### Added / paid (0.60.0–0.60.9)
- **`SystemSupervisor`** — continuous services registry + lifecycle on `SystemInstance`  
- **`WorkPlaneService`** — start plane (`runtime.work_plane`): enqueue / tick / triggers / schedules / background  
- **System session attribution** for reactive start (`session_attr`; inherit-or-service)  
- **Supervised** `work_drain` + **`OutboxLoopService`** + optional `system.background.start`  
- **Inbound** home under `palm.system.planes.work.inbound` (host re-export)  
- Host prefers plane/supervisor; lean BaseRuntime seats without ApplicationHost  

#### Theme exit (0.60.9)
- **ADR-029 Accepted** · **BI-013 closed**  
- Residual host product enrich/catalog wire named  
- **MIGRATION-0.60** · **RELEASE-0.60.9** · stamp `0.60.9`

## [0.59.8] — 2026-08-01

### 0.59 — System Boot + Composition Truth (**theme closed**)

Vision: [VISION-0.59](docs/vision/closed/VISION-0.59.md) · ADR: [028](docs/adr/028-system-boot.md) **Accepted** · Migration: [MIGRATION-0.59](docs/migrations/MIGRATION-0.59.md) · Release: [RELEASE-0.59.8](docs/releases/RELEASE-0.59.8.md)

#### Added / paid (0.59.0–0.59.8)
- **Host + system boot phase tables** walked in code (`HOST_PHASES` / `SYSTEM_PHASES`); boot packages own handlers  
- **CompositionProfile membership truth** — sole switch for services / surfaces / capabilities; PhaseSkip `composition_off:*`  
- **BootMode** + `ApplicationHost.for_mode` — safe / test / dev / prod + shape presets; `server_port` for CI  
- **SystemLog** — ordered boot narrative seats (`palm.system.log`)  
- **Dogfood** — mode + shape phenotype tests; spine on collapsed modes  
- **Residual cleanup (0.59.8)** — default `host` fixture → `for_mode("all_in_one")`; dead quick-dag examples → spine wizard helper  

#### Theme exit (0.59.8)
- **ADR-028 Accepted** · **SD-014 closed**  
- Residual **BI-*** named (dual root, suite force, work start home, surface chrome, log catalog, …)  
- **MIGRATION-0.59** · **RELEASE-0.59.8** · stamp `0.59.8`

## [0.58.20] — 2026-07-30

### 0.58 — Session plane (**theme closed**)

Vision: [VISION-0.58](docs/vision/closed/VISION-0.58.md) · ADR: [027](docs/adr/027-session-plane.md) **Accepted** · Migration: [MIGRATION-0.58](docs/migrations/MIGRATION-0.58.md) · Release: [RELEASE-0.58.20](docs/releases/RELEASE-0.58.20.md)

#### Added (0.58.0 plan)
- Theme plan: session as **system glue**, multi-instance, bind law (not user plane)  
- [ADR-027](docs/adr/027-session-plane.md) Proposed  
- Tech debt **SI-001…014** session impact inventory; **SD-008** theme-active  
- [VISION-SESSION-PLANE](docs/vision/closed/VISION-SESSION-PLANE.md) marked **superseded**

#### Added (0.58.1)
- **`palm.system.planes.session`** — `SessionRecord`, `SessionStatus`, `SessionStore` on **StorageEngine**, `SessionPlaneService`  
- **`BaseRuntime.session_plane`** — open/get/close/list lifecycle wired at start (same storage as work plane)  

#### Added (0.58.2)
- **Multi-attach** — `attach_instance` / `detach_instance` / `list_instances` / `session_for_instance`  
- **Reverse index** — `palm:session:by_instance:{instance_id}` → session_id (one instance → one session)  
- OPEN → ACTIVE on first attach; refuse attach on closed; refuse dual-session ownership  

#### Added (0.58.3)
- **Bind law** — `SessionPlaneService.bind` / `require_open` / `SessionBind` / `require_session_plane`  
- **Host** — `ApplicationHost.session_plane` + `bind_session`  
- **CLI** — `active_system_session_id` + `bind_system_session`; assist/job activation binds system subject without equating it to instance id  

#### Added (0.58.4)
- **Job path link** — `ProcessInstance.session_id`; job metadata `session_id`; `SessionOwnershipHook` attaches instance on plane  
- **Events** — `EventContext.session_id`; `flow.session.*` / instance events carry session when known  
- **Host** — `submit_flow(..., session_id=)` merges into job metadata  

#### Added (0.58.5)
- **Journey inspect** — `SessionPlaneService.inspect` / `list_waiting` (instances + open waits)  
- **Host** — `inspect_session`; note: inspect only, continue stays wait plane  

#### Added (0.58.6)
- **Dogfood** — flow submit auto-binds system session; `SessionOwnershipHook` attaches instance  
- **Envelope** — `system_session_id` / `refs.system_session_id` on Assist start and flow create  
- Product `session_id` remains the instance handle for continue (SI-001 residual, intentional)

#### Added (0.58.7)
- **WS bind law** — `op: bind` / hello / dispatch bind **system** session via plane (`system_session_id`)  
- **Cookie-like transport** — `X-Palm-Session` header + Cookie `palm_session`; REST create `Set-Cookie`  
- **Kit helpers** — `extract_system_session_hint`, `resolve_session_plane`, `looks_like_system_session_id`  
- Product instance id stays separate on the connection for continue (SI-001 residual)

#### Fixed (0.58.7)
- Flow create path: name-shaped ids (`todo-builder`) no longer forced `by_id=True` (id-shaped `flow-*` still use by_id)

#### Added (0.58.8)
- **Session watches** — `event_matches` / `attributed_session_id` / `make_event_filter` on session plane  
- **Events WS fan-in** — subscribe with `session_id` (or cookie); filter live + journal catch-up  
- **Continue resolve** — `resolve_continue_instance`; operator path rewrite `sess-…` → attached instance  
- **Operator** — `system/session/{id}` inspect / waiting / instances  
- **Workload** — owner session/job/instance enriched from active EventContext on start  

#### Changed (0.58.9) — vocabulary slash
- **One edge name:** `session_id` is the system subject only (`sess-…`)  
- **Continue handle:** `instance_id` only; plane picks waiting → else last attached when only session given  
- **Deleted duals:** no `system_session_id` / `palm_session_id` fields (cookie name `palm_session` remains transport)  
- **Product residual (SI-001):** class/path names still say “session” for instance handles; resolve at entry  
- **Fix:** wizard/dict `SubmitFlowCommand` path preserves job metadata (session bind on REST create)

#### Added (0.58.10) — active instance on record
- **`SessionRecord.active_instance_id`** — plane-owned continue focus (not equal to `session_id`)  
- **Attach** sets active to the newly attached instance; re-attach does not steal focus  
- **`set_active_instance` / `clear_active_instance` / `active_instance`**  
- **`resolve_continue_instance`** order: active (if attached) → open wait → last attached  
- **Inspect / SessionBind** expose `active_instance_id`; legacy store rows seed last attached  

#### Documented (0.58.10) — ownership vs focus
- **Exclusive ownership:** one instance → one owner session (not softened by active)  
- **Active = focus only** inside the owner attach list; not a cross-session pass  
- **ADR-027** D9–D11; **VISION-0.58** §4.1 / §7.1; residual **SI-015** (gate continue when bound)  
- **Later seed:** user-plane session **impersonation** / grants — act as owner; do not dual-own  

#### Added (0.58.11) — SI-015 owner gate
- **`owns_instance` / `require_owned_instance` / `InstanceNotOwnedError`** on session plane  
- **Operator rewrite** refuses continue when bound system `session_id` does not own path/param instance  
- **Flows + Assist** dispatch gate when params carry system `session_id`  
- **Host** `require_session_owns_instance`; WS error code `session_owner`  
- Path product instance is **authoritative** (not replaced by plane focus)  
- **Residual:** bare instance without bound system session still ungated  

#### Added (0.58.12) — product SessionService (surface door)
- **`palm.services.session.SessionService`** — product door over the system session plane  
- **Helpers for surfaces / other services:** `continue_target`, `enrich_submit_body`, `surface_view`, resolve/gate, event filter  
- **Host** `session` slot; composition **core** includes `session`; ServerContext exposes `ctx.session`  
- **Flows + Assist + MCP operator** prefer SessionService (no scattered `session_plane` reinvent)  
- Plane remains law — service does **not** resume jobs  
- **Residual SI-001:** product path/handle names still say `session` for instance segments  

#### Added (0.58.13) — service / origin sessions (SI-011 partial)
- **Service sessions** — stable `sess-svc-{origin}` for automated / internal start (not outside bind)  
- **Host seat** — `sess-svc-host` ensured at runtime start  
- **Work drain** — submit path enriches `work-drain:{target}` so intents share an owner per flow  
- **SessionService** — `ensure_service_session` / `ensure_host_session` / `enrich_submit_body(origin=…)`  
- **Plane** — `ensure_service_session` / `ensure_host_session`  
- Outside interactive submit still mints a new `sess-…` when no session present  
- **Not** one junk-drawer root for all automation; workloads inherit job session only  

#### Documented (close plan) — remaining 0.58.14–0.58.20 + exit
- [VISION-0.58 §4.3–4.4](docs/vision/closed/VISION-0.58.md) — session owns **BoundSurface**; session metadata ≠ job metadata  
- [VISION-0.58 §6.2](docs/vision/closed/VISION-0.58.md) — ordered close slices: BoundSurface → strict attribution → inherit-or-service → kit door → operate → rename → docs → exit  
- ADR-027 **D13–D14** · TECH-DEBT **SI-016** · STATUS table  

#### Added (0.58.14) — BoundSurface + session context metadata
- **BoundSurface** — product handle: `session_id`, `instance_id`, `kind` (outside|service|host), `origin`, session metadata snapshot  
- **SessionService** — `bind_surface`, `surface_from_session` / `from_bind` / `from_params` / `from_dict`, `get_metadata` / `merge_metadata` / `replace_metadata`  
- **Session plane** — `get_metadata` / `merge_metadata` / `replace_metadata` on the record  
- **surface_view** — includes `bound_surface`, `session_kind`, `origin`  
- Session metadata holds walk/surface/attribution facts; job metadata stays run facts (ADR-027 D14)  
- **SI-016** seat partial; surface dogfood dual-slot cleanup remains **0.58.17**  

#### Added (0.58.15) — strict attribution (SI-015 residual closed)
- **Plane** — `require_continue_attribution` + `SessionAttributionError`  
- **SessionService** — `strict_attribution` (default on); gate injects owner from reverse index; bare orphan refuse on rewrite / `continue_target`  
- **Settings** — `session_strict_attribution` / `PALM_SESSION_STRICT_ATTRIBUTION` (compat off)  
- **Start** — enrich refuses when plane ready but no system session  
- **Handoff auto-start** — inherits parent system `session_id` so the walk stays one subject  
- **Assist** — product door via `_session` / `product_session` (no longer shadowed by handle API)  
- **WS** — error code `session_attribution`  
- Product unknown instance defers to not-found (404); known unowned → attribution refuse  

#### Added (0.58.16) — inherit-or-service reactive start (SI-011 closed)
- **Triggers** — copy system `session_id` from event signal into WorkIntent payload  
- **SessionService** — `enrich_reactive_start`, `inherit_or_service_session`, `reactive_origin`  
  * inherit parent walk when signal carries `sess-…`  
  * else stable service session: `work-drain:{flow}` / `schedule:{flow}` / `inbound:{resource}`  
  * never random outside `sess-…` for reactive paths  
- **Work drain coordinator** — submit uses inherit-or-service (not blind service-only)  
- **Inbound** — `trigger=inbound`; inherit envelope session when present  
- Workloads still inherit job session only (no separate workload session type)  
- **SI-011** closed  

#### Added (0.58.17) — single kit door + surface dogfood
- **Kit** — `resolve_session_service` / `require_session_service` as the **only** product door (`palm.kits.server`)  
- **`resolve_session_plane`** — system/tests only; not for product verbs  
- **MCP operator** — rewrite / system session inspect / owner gate use SessionService only (no plane fallback)  
- **WS assist** — bind via `bind_surface`; connection holds **BoundSurface**; snapshot includes `bound_surface`  
- **WS events** — cookie/subscribe bind + event filter via product door  
- **MCP in-process** — `resolve_session_continue` via SessionService  
- **CLI** — `CliContext.bound_surface` is truth; dual slots remain mirrors (SI-006 residual until 0.58.19)  
- **SI-016** dogfood partial ✅; path rename remains **0.58.19** (SI-001/005)  

#### Added (0.58.18) — session operate + surface_view v2
- **SessionService operate** — `focus` / `clear_focus` (BoundSurface), `list_owned_waiting`, `cancel_owned` / `cancel_all_owned`  
- **Cancel law** — owner gate + `SystemService.cancel_job` only; no private session resume/cancel path  
- **surface_view v2** — `view_version: 2`, `waiting`, richer `refs` (incl. `job_id`), `actions` catalog for operator paths  
- **Operator (SI-007 partial)** — `system/session/{id}/view` · `/focus` · `/focus/clear` · `/cancel` · `/cancel/all`  
- Full CQRS session contributor still optional residual  

#### Changed (0.58.19) — product vocabulary rename (SI-001 / SI-005)
- **Grammar emit** — assist/flows command paths use segment `instance` + `instance_id` (legacy segment `session` still **parsed**)  
- **REST** — `/v1/api/assist/instance/{instance_id}/…` and `/v1/api/flows/{flow_id}/instance/{instance_id}/…`  
- **MCP** — aliases resolve `{instance_id}` (legacy `session_id` param fills continue when absent); rest_map + normalize + operator rewrite aligned  
- **Handles** — `FlowSession` / `AssistSession` class field names may stay thin (SI-002); public path/envelope law: `session_id` = system, `instance_id` = continue  
- **System paths** — `system/session/{id}/…` unchanged (system journey)  

#### Documented (0.58.20) — docs/skill + residual honesty (SI-012)
- **Skill** — `docs/skills/palm/` vocabulary: session ≠ instance; BoundSurface; SessionService; prefer `instance_id`  
- **Operator surfaces** — `mcp-card.txt`, `mcp.txt`, `MCP.md`, `llms.txt` teach 0.58.9/19 law  
- **Wiki** — `docs/wiki/concepts/session-plane.md`  
- **PALM.md** — session plane vocabulary line  
- **Residual honesty** — SI-012 ✅; SI-010 open (explorer bare / SU-*); thin SI-002/006; SI-007/016 partial  

#### Theme exit (0.58.20)
- **ADR-027 Accepted** · **SD-008 closed**  
- **[VISION-SURFACE-DEFLATION](docs/vision/VISION-SURFACE-DEFLATION.md)** named — surface compost / walk handles later; not paid in 0.58  
- **MIGRATION-0.58** · **RELEASE-0.58.20** · stamp `0.58.20`  
- Residual seeds: SI-002 family, SU-*, SD-014, user-plane impersonation, API/SDK docs when value unlocks  

## [0.57.14] — 2026-07-29

Embedded release covering **0.55–0.57** (previous stamp `0.54.10`).  
**0.57 Palm System closed.** Map: [PALM.md](docs/PALM.md) · ADR: [026](docs/adr/026-palm-system-layer.md) **Accepted** · migration: [MIGRATION-0.57](docs/migrations/MIGRATION-0.57.md) · notes: [RELEASE-0.57.14](docs/releases/RELEASE-0.57.14.md)

### 0.57 — Palm System (**theme closed**)

Logical slices **0.57.0–0.57.14**. Vision: [VISION-0.57](docs/vision/closed/VISION-0.57.md)

#### Added
- **`palm.system`** — system instance: `BaseRuntime`, **ExecutionPort**, wait/work/workload **planes**, executions, job hooks  
- **`palm.kits`** — surface kits registry; **`palm.kits.server`** transport kit (from `common.runtimes.server`)  
- **P2 graph bind** — `ResourceInvoker` / `WorkloadDriver` over the execution port  
- **Capability catalog truth** — default `INSTALLED_*` vs gated `INTENTION_*` ([STUBS.md](docs/STUBS.md))  
- Living map [PALM.md](docs/PALM.md) · [SYSTEM-LOW-LEVEL](docs/SYSTEM-LOW-LEVEL.md) · live [TECH-DEBT.md](TECH-DEBT.md) (SD/SU/ST)

#### Changed
- **`palm.common`** is shared libraries only — system deflated; **SD-012 shims deleted**  
- Product workload list/doctor/stop and job resume use **ExecutionPort**  
- `RuntimeHost` = submit contract + execution (honest scope)

#### Breaking
- Import homes for BaseRuntime, planes, executions, server kit — see [MIGRATION-0.57](docs/migrations/MIGRATION-0.57.md). No dual-path shims.

#### Residual (not blocking close)
- **SU-*** surface debt (explorer, MCP dual stack, CLI weight) — optional  
- **SD-008** session plane — opened as theme **0.58** ([VISION-0.58](docs/vision/closed/VISION-0.58.md))

#### Slice log
- **0.57.0–1** — Plan, map, ADR, debt archive, low-level  
- **0.57.2–5** — Boundary, port, product/graph rebind  
- **0.57.6–8** — Deflate, edge policy, import sweep  
- **0.57.9–10** — Catalog truth, docs coherence  
- **0.57.11–12** — Executions/hooks, shim delete, port catalog  
- **0.57.13** — Kits package  
- **0.57.14** — Theme exit + version dump (**closed**)

### 0.56 — Workload (**scout embedded**)

Vision: [VISION-0.56](docs/vision/VISION-0.56.md) · ADR: [024](docs/adr/024-workload-engine.md)

- WorkloadEngine + leaf foundation; host/neonroot runners  
- Product `execution.workloads` over port (0.57 rebind)  
- Direction only for later runner growth — structure sits on 0.57 map

### 0.55 — Reactive Interests (**theme closed · embedded**)

Logical slices **0.55.0–0.55.16** (was unstamped until this release).  
Vision: [VISION-0.55](docs/vision/closed/VISION-0.55.md) · ADR: [025](docs/adr/025-reactive-interests.md) · migration: [MIGRATION-0.55](docs/migrations/MIGRATION-0.55.md)

#### Added
- **Wait interest** (`palm.core.wait`) — durable `palm.wait.interests` on job/instance state  
- **Continue plane** — `WaitPlaneService` / matcher on `runtime.event`  
- Nested wizards open `kind=job` interest; workload wait kind socket  
- Operator **`waiting_on`**; doctor **`reactive_interests`**  
- [EVENT-PLANE](docs/EVENT-PLANE.md) · [WORK-DRAIN](docs/WORK-DRAIN.md)

#### Notes
- **Start** = WorkIntent drain; **continue** = wait interest  
- Inverted completer→parent resume removed  
- Session plane remains queued: [VISION-SESSION-PLANE](docs/vision/closed/VISION-SESSION-PLANE.md)

## [0.54.10] — 2026-07-26

Embedded release of the **0.54 Hermetic Jobs** theme (0.54.0–0.54.10).  
Vision: [VISION-0.54](docs/vision/closed/VISION-0.54.md) · ADR: [023-hermetic-jobs](docs/adr/023-hermetic-jobs.md) · notes: [RELEASE-0.54.10](docs/releases/RELEASE-0.54.10.md)

### Added
- Hermetic job contract (`neonroot` spawn / seed / allowlist) and [HERMETIC-JOBS.md](docs/HERMETIC-JOBS.md) / [HERMETIC-RUN-DIR.md](docs/HERMETIC-RUN-DIR.md)
- **DAG pattern v0** — resource nodes, `depends_on`, `drain_ready`
- Dogfood flows: `hermetic-job-smoke`, `hermetic-job-dag`, `hermetic-job-fanout`, `hermetic-ci-slice`
- **Assist run-code:** `neonroot.run_script` + wizard `hermetic-run-code` (image → code → resource → state → display)
- NeonRoot `seed_mode` bind/copy; run-dir staging helpers

### Fixed
- **0.54.10** Portal/resource ergonomics: palm-ci `uv run` entrypoint (no bare `python`), resource steps non-interactive + Portal auto-resume, longer session idle wait for long spawns, clearer stdout feedback

### Changed
- Discarded interim 0.54 library product stack (`common.library`, `providers/library`, `services/docs`)
- Next theme (opened as plan): [VISION-0.55](docs/vision/closed/VISION-0.55.md) **Reactive Interests** (session plane deferred to [VISION-SESSION-PLANE](docs/vision/closed/VISION-SESSION-PLANE.md))

### Slice log
- **0.54.0** — Replan + discard product stack  
- **0.54.1** — Hermetic job contract  
- **0.54.2** — `hermetic-job-smoke`  
- **0.54.3** — DAG pattern v0  
- **0.54.4** — `hermetic-job-fanout`  
- **0.54.5** — `seed_mode` + run-dir docs  
- **0.54.6** — `hermetic-ci-slice`  
- **0.54.7** — Purpose-test notes  
- **0.54.8** — `drain_ready`, run_dir, Assist discover  
- **0.54.9** — `hermetic-run-code` + `run_script`  
- **0.54.10** — Dogfood complete + Portal auto-advance (**theme closed**)

## [0.51.6] — 2026-07-16

**Bundled release since 0.48.8** — the **composition-profile arc**. Palm learns to *declare its own
shape*: a `CompositionProfile` (services × surfaces × capabilities) alongside the `DeploymentProfile`,
so every shape it ships — `all_in_one`/`server`/`embedded`/`worker`/`cli`/`mcp` — is a **declaration,
not a bespoke class**. Both composition roots now build services through one registry; the capability
axis is authoritative (scattered `enable_*` flags unified); and a **lean, projection-less
`ApplicationHost` is real** (submit + read complete). Renames: `PalmApp → PalmKernel`,
`HostProfile → DeploymentProfile`. Public API stable (rename shims + one internal import move — see
[MIGRATION-0.49.md](docs/migrations/MIGRATION-0.49.md)); behaviour-preserving throughout, hermetic CI green at each
theme's close. New: [PHILOSOPHY.md](PHILOSOPHY.md).

### 0.51 — Living Capabilities (the composition profile's third axis comes alive · [VISION-0.51](docs/vision/closed/VISION-0.51.md) · [ADR-020](docs/adr/020-living-capabilities.md))
- **0.51.0** — Plan + ADR-020. Grounded in the code: `composition.capabilities` had been declared since 0.50.1 and read by nothing; the machinery it should gate was still scattered across `settings.enable_*` + deployment flags + unconditional wiring.
- **0.51.1** — Resolver comes alive: `composition_profile_from_settings` **derives** `capabilities` from the `enable_*` flags (pinned against today's wiring). Declared → *derived*, not yet gating.
- **0.51.2** — Compensation + webhook gate on `composition.has(...)` instead of `settings.enable_*` (settings refine, never bypass).
- **0.51.3** — Outbox + work_drain — **available (composition) and activated (deployment)**: `has(cap) and profile.<activates>`. No uniform helper — the two gates' activation logic genuinely differs (AND vs OR).
- **0.51.4** — Journal gates on `has("journal")` (always-derived → behaviour-preserving; lean shapes omit it).
- **0.51.5** — **Projections become a capability** — `has("projections")` gates the projection layer, so `ApplicationHost` can assemble the lean, projection-less shape (the 0.50.5f blocker removed). Default shapes keep projections.
- **0.51.6** — Scouted the `ServerContext` fold-in ([SCOUT](docs/SCOUT-0.51.6-serverctx-foldin.md)): evidence says the type **stays** (`ctx.runtime` is a single-runtime view the multi-runtime host can't be). Took the contained half — a lean `ApplicationHost` serves reads direct-from-runtime (reused `StandaloneQueryHandlers`). Deferred-import ratchet **219 → 218**.

### 0.50 — Composition Profiles (declare the app's shape · [VISION-0.50](docs/vision/closed/VISION-0.50.md) · [ADR-019](docs/adr/019-composition-profiles.md))
- **0.50.0–0.50.1** — Plan + ADR-019; `CompositionProfile` skeleton (name-tuples + presets + `composition_profile_from_settings` seam), `all_in_one().services` pinned to `CORE_SERVICE_PROVIDERS`.
- **0.50.2** — `ApplicationHost` assembles services from `composition.services` via a dependency-closure `HostServiceRegistry.build_all(only=…)` — **the embedded shape is real** (core-3, starts clean).
- **0.50.3** — Surfaces driven by `composition.surfaces` (`default_surfaces(ctx, only=…)`).
- **0.50.4** — Read facades — `host.instances` / `host.jobs` / `host.wizards`; the flat query methods become thin delegators.
- **0.50.5a–e** — **Convergence**: both composition roots (`ApplicationHost` + host-less `ServerContext`) now build services through **one** `core_service_registry()` — `_RuntimeKernelView` presents the runtime as the kernel shape; `HostServiceContext.event` made optional.
- **0.50.5f** — **Reframe** (evidence over sketch): `ServerContext` is **retained** — the surface-facing context + lean phenotype, not redundant logic — not dissolved. Docs corrected so no future contributor does the rip-out.

### 0.49 — Naming (vocabulary for the composition/deployment split · [MIGRATION-0.49](docs/migrations/MIGRATION-0.49.md))
- **0.49.1** — `HostProfile → DeploymentProfile` (+ `HostProfilePreset`/`HostRoleName`/`host_profile_from_settings`) — names the deployment axis.
- **0.49.2** — `PalmApp → PalmKernel`, `palm.app.app → palm.app.kernel` — the infrastructure *substrate*, not "the app".
- Anchored the `CompositionProfile × DeploymentProfile` vocabulary; grounded the mechanism in palm's existing extensibles (convergence, not invention).

### Docs
- **[PHILOSOPHY.md](PHILOSOPHY.md)** — a meditation on Palm's nature (grown-not-built, register-downward, coherence-as-immune-system, one-genome-many-phenotypes, truth-over-surface, the map yielding to the territory).
- README / ARCHITECTURE state the register-downward + coherence-as-fitness-function design philosophy; stale `(0.12 architecture)` headings corrected.

## [0.48.8] — 2026-07-15

**Bundled release since 0.47.4** — completes **T3** (import-cycle cleanup, 0.47) and delivers **T2**
(`ApplicationHost` decomposition, 0.48). Headline: upward cycle-forcing imports **35 → 3**;
`ApplicationHost` **1164 → 629 LOC**; **PD-012, PD-013 closed** (+ PD-009/010/018 addressed). Two clean
debt themes; public API stable (one internal import-path move — see [MIGRATION-0.48.md](docs/migrations/MIGRATION-0.48.md)).

### T2 — Decompose `ApplicationHost` (0.48 · PD-009/010/013/018)
- **0.48.0** — Plan: [VISION-0.48](docs/vision/closed/VISION-0.48.md) + [ADR-018](docs/adr/018-application-host-decomposition.md) + characterization tests freezing the 3 status reports' JSON contract.
- **0.48.1** — `app/host/observability.py::HostObservability` — the three status reports extracted (PD-018).
- **0.48.2** — `app/host/services/` — the 6 core services build via a dependency-ordered `HostServiceRegistry` (PD-010).
- **0.48.3** — `app/host/workplane/` — `WorkPlaneCoordinator` (work-drain / inbound / journal) + folds in the flat service files.
- **0.48.4** — `app/host/lifecycle/` — `RuntimeSpawner` + `RecoveryCoordinator`.
- **0.48.5–0.48.6** — `app/host/wiring/` (projections + CQRS bus handlers); **found & fixed a latent `services → server → ServerContext → services` import cycle** via lazy composition-root exports in `common/runtimes/server/__init__`.
- **0.48.7** — Relocated `ServerContext`/`ServerApp` `common → runtimes/server/` — **PD-013 closed**; upward imports **5 → 3**; server infra stays in `common`. (import-path MIGRATION.)
- **0.48.8** — Removed 8 dead host `@property` accessors (whole-repo zero-consumer sweep). `ApplicationHost` **1164 → 629 LOC**; T2 structurally complete (the final <350 shrink via facades moves to [VISION-0.50](docs/vision/closed/VISION-0.50.md), the app-composition-profile theme).

### T3 — Break the import cycles, cont'd (0.47.5–0.47.9 · PD-012 closed)
- **0.47.5 (a–d)** — Pattern + provider **registry inversion**: registries move into `common/{patterns,providers}/_registry`; plugins register downward; registration-by-side-effect autoloads removed; back-compat shims retired.
- **0.47.6** — **Storage backend polymorphism** — `BaseBackend.keys_with_prefix` replaces `common`'s `isinstance` + private-attribute poking.
- **0.47.7 (a–b)** — Service **CQRS contributor registry** → `common/cqrs/service_contributors`; services self-register their contributor on package import.
- **0.47.8** — `job_inspect` → a `JobInspectable` capability: each pattern owns `inspect_job`; the shared inspector is pattern-agnostic (no `isinstance` ladder).
- **0.47.9** — analytics preflight + assist CTA enrichment inverted via contributor registries; [ADR-017](docs/adr/017-import-seams.md) sanctions the 5 remaining composition-root/lazy seams; **PD-012 closed** (upward 35 → 5).

### 0.47.4 — Hoist ApplicationHost `_wire_cqrs` service imports (T3)
- Hoisted the 13 `_wire_cqrs` service/schema imports in `app/host/application_host.py` (SystemService, DefinitionService, ExecutionService + flows/processes/providers, AssistService, DesignService, AnalyticsService, `build_schema_registry`, `wire_all_service_cqrs`, `wire_builtin_design_contributors`) from function-local to module top. Pure downward (`app→services`/`app→common`) — verified no cycle (`import palm.app`, host start/shutdown, full suite all clean).
- **⛳ Unblocks T2:** the god-class's service dependency surface is now top-level and visible, the precondition for the contributor-pipeline decomposition (VISION-0.48).
- Ratchet: **267 → 254** function-local imports. Left deferred (by design): `import palm.patterns` side-effect (→ 0.47.5) and the scattered work-drain/inbound/consumers imports (follow-up).

### 0.47.3 — Centralize shared surface helpers → `common/surfaces/` (T3)
Kills the `mcp → rest` coupling for shared helpers (from review feedback: mcp shouldn't depend on rest).
- New **`palm/common/surfaces/`** package holds the transport-agnostic helpers — `pagination` (`PaginationParams`, `list_envelope`, `paginate_rows`) and `serializers` (`snapshot_summary`/`detail`). Every surface (rest/mcp/ssr/ws) now depends *down* on `common` instead of sideways on `rest`.
- Repointed the 9 importers; `rest/validation.py` re-exports `PaginationParams` (via `__all__`) so existing REST handlers are unchanged; removed `rest/pagination.py` + `rest/serializers.py`.
- `mcp/in_process.py` no longer imports `rest` for shared helpers — the only remaining `mcp→rest` edge is `build_openapi_spec` (the REST API's own OpenAPI spec, which is inherently rest). Full suite green; single canonical `PaginationParams` (no dual class).

### 0.47.2 — De-cycle mcp↔server: hoist `in_process.py` imports (T3)
- Hoisted 20 function-local imports in `runtimes/mcp/in_process.py` to module top — the leaf `rest.*` helpers (`pagination`/`validation`/`serializers`/`openapi`, all mcp-import-free) + the mcp intra-package imports. Verified `import palm.runtimes.mcp.in_process` is cycle-free; the 4 `server→mcp` edges + the bootstrap `server`/`app` imports stay deferred by design. The worst-offender file drops 32→12 deferred imports.
- Ratchet: function-local `palm` imports **287 → 267** (`guard_deferred` ceiling lowered). Upward/cycle-forcing count unchanged at 35 (this is sibling de-cycling). Full suite green.

### 0.47.1 — Deferred-import ratchet (T3)
- `scripts/guard_deferred.py` — AST fitness function: counts runtime function-local `palm` imports (excludes `TYPE_CHECKING`), classifies by layer direction, and fails if the total (**287**) or upward/cycle-forcing (**35**) ceiling is exceeded. Wired into `just check` / `just ci` as `just guard-deferred`. Locks the graph so nothing regresses while 0.47 cuts the seams; the ceilings only ratchet down toward 0. Zero behavior change.

### 0.47.0 — Open T3: import-cycle cleanup (plan)
Opens the 0.47 minor (theme **T3**, the dependency root for the T2 `ApplicationHost` decomposition).
- `docs/VISION-0.47.md` — de-cycling plan. **AST-verified reframing:** the audit's "595 deferred imports" = **310 `TYPE_CHECKING`** (the correct pattern, not debt) + **287 runtime**, of which only **~35 are upward/cycle-forcing** across ~8 seams. Slices `0.47.1`–`0.47.8`, driving upward function-local imports 35 → 0.
- `docs/VISION-0.48.md` — forward plan for T2 (`ApplicationHost` → 5 composition seams, < 350 LOC), which 0.47 unblocks.
- `TECH-DEBT.md` — PD-012 metric corrected; roadmap → 0.47 / 0.48.

### 0.46.5 — Coverage floor (T1 complete)
Closes **PD-008** — the last T1 item. The safety net is now in place: green suite + green lint + CI-enforced + coverage-gated.
- `just ci` runs the suite with `--cov=src/palm`; `[tool.coverage.report] fail_under = 78` gates against regression (current **80.33%**). `pytest-cov` added to the `dev` group.

### 0.46.4 — CI gate: sovereign hermetic checks via NeonRoot (T1)
Closes **PD-001** (no CI gate), **PD-006** (pre-commit), **PD-007** (audit deps undeclared). See [ADR-016](docs/adr/016-ci-gate.md).
- **`just ci`** — the gate: `ruff check` + `guard_core.py` + the full suite (`pytest -q` with `--extra cli --extra mcp --group dev`, incl. MCP tests) all **blocking**; **`mypy` report-only** (379 errors ride the T2 refactor — PD-005).
- **`just ci-sandbox`** — runs `just ci` in a throwaway NeonRoot `palm-ci` container seeded from `git archive HEAD` (**git-tracked files only** — no stale `data/`/`.venv`). Sovereign, offline, hermetic. `ci/Containerfile` (Arch + git + just + uv, `UV_PYTHON=3.12`) is the tracked image source; `just ci-image` builds it; the `.neonroot/` vault is git-ignored.
- **`.pre-commit-config.yaml`** — ruff check/format + core-purity guard on staged files, via the project's pinned tools (`uv run`).
- **`[dependency-groups] audit`** — pins vulture/radon/xenon/bandit/pip-audit/autoflake so `just audit`/`complexity`/`refactor` run on a fresh checkout.

### 0.46.3 — Lint gate green (T1)
`ruff check src/palm tests examples` now passes (was ~133 findings). Closes **PD-004**.
- Auto-fixed I001/F401/RUF100/UP035/UP038/B010/B905/F541/UP041 across ~90 files (import sorting, unused imports, modernizations).
- Manual: removed 3 dead locals, de-ambiguated a variable name (`l`→`lbl`), fixed 2 en-dashes in docstrings, added `# noqa: E402` to 5 guard-pattern (importorskip/setup) imports.
- Suite still green (0 failures). Intentionally **not** in this slice: `ruff format` (335-file whole-repo reformat) and `mypy --strict` (379 errors, entangled with the `ApplicationHost` Any-typing → T2). mypy will run as a **report-only** CI job; xenon/complexity (PD-005) is deferred to the complexity themes.

### 0.46.2 — Green the test suite (T1)
Fixed all **22** pre-existing failures on master (the suite was red and undetected — no CI). Full suite green. Closes **PD-002**, **PD-003**.
- **Prod fixes** (tests correctly caught real bugs, not just stale assertions):
  - `flows/{id}/session/{id}/*` handlers (input, backtrack, resume, resume-child-wait, cancel) now catch `InstanceNotFoundServiceError` → return a clean 404 instead of crashing the request thread.
  - `common/runtimes/server/cqrs.py` guards `wizard_answers` (`_safe_wizard_answers`) so inspecting a non-wizard (etl) instance no longer raises `TypeError` → 400.
- **Test/fake/doc updates** to current contracts: compact "powertool" session view (`instance_id`/`step`/top-level `waiting_for_child`), `_FakeRestClient.flows_session_input(input_token=…)`, `include_commit=False` todo-builder flow, normalized assist statuses (`waiting`/`complete`), design-contributor + palm-manifest registry growth, todo-builder example loading; **+15 REST route response examples** (docs-as-code).

### 0.46.1 — Security: pydantic-settings CVE (T1)
- Bump `pydantic-settings` floor to `>=2.14.2` (was `>=2.2`) — fixes GHSA-4xgf-cpjx-pc3j; `pip-audit` now clean. Closes **PD-028**.

### 0.46.0 — Debt-paydown line opens: versioning convention + T1 plan
- `docs/VERSIONING.md` — canonical versioning & release convention: one theme per minor; `0.X.0` plans (a `VISION-0.X.md`), `0.X.N` ships one slice; green `just check` gated in CI
- `docs/VISION-0.46.md` — 0.46 = TECH-DEBT **T1 · Safety Net** (green the red suite → wire CI → coverage/complexity gates); slices `0.46.1`–`0.46.5`
- `TECH-DEBT.md` — themes→minors roadmap over the debt register (`PD-001…031`); baseline metrics in `docs/audit/`, decision in `docs/adr/015`
- `AGENTS.md` — new explicit rules: CI-green `just check`, no new god-objects, test doubles must contract-match prod, gated placeholders, deferred-import discipline
- Note: `just docs-check` is currently red on master (skill/mcp-data mirror drift, PD-031) — to be greened in a 0.46 patch

### 0.44.1 — Inbound demo docs + server profile work drain default
- `examples/definitions/inbound_demo/README.md` — webhook dogfood + debug curls
- `docs/WORK-DRAIN.md` — WorkIntent drain (explicit vs background, env, ops)
- **`host server` profile** enables background work drain by default (`HostProfile.enable_work_drain_service`)

### 0.44.0 — Inbound store inbox, poll mode, WS stream
- Wire ``store_resource`` / ``store_action`` — persist envelope via resource invoke before WorkIntent
- ``mode=poll`` background worker (HTTP GET ``url`` or pull-invoke listening resource)
- Stream prefers WebSocket transport; HTTP journal poll fallback
- ``inbound_demo`` pack adds ``inbound-inbox`` resource; Vision: [VISION-0.44](docs/vision/closed/VISION-0.44.md)

### 0.43.1 — Fix server startup circular import (0.42.3 regression)
- Move RFC6455 WebSocket frame codec to ``palm.common.websocket.frames``
- ``PalmEventsWebSocketClient`` no longer imports ``palm.runtimes.server`` at provider autoload
- Server shim re-exports ``palm.runtimes.server.surfaces.websocket.frames`` for compatibility

### 0.43 — Inbound as a Resource capability
- **`metadata.inbound`** on `ResourceDefinition` (no separate definition kind)
- `parse_inbound_spec` · `InboundBindingService` (webhook + palm stream)
- REST `POST/GET /v1/api/inbound…` → WorkIntent (202); doctor `control_plane.inbound_*`
- Event `inbound.received`; pack `examples/definitions/inbound_demo/`
- Vision: [VISION-0.43](docs/vision/closed/VISION-0.43.md)

### 0.42.3 — Native WebSocket events client (palm provider)
- `PalmEventsWebSocketClient` for `/ws/v1/events` (stdlib RFC6455)
- Client-masked frames; subscribe + live wait helpers


### 0.41.0–0.41.2 — Durable dashboards, schedules, design publish
- Design `propose_dashboard` / `publish_dashboard` + REST `/v1/api/design/dashboards`
- Tile validation contributor; system README design + origin story

### 0.41.0–0.41.1 — Durable dashboards & schedules
- Storage-backed dashboard registry (`palm:dashboard:*`); host attaches on start
- `ScheduleRegistry` durable `next_fire_at`; work drain `tick_schedules` uses it
- Doctor/control_plane includes schedule entries

## [Unreleased]

### Added

- **0.40.5** — Remote system analytics dogfood: `params.remote_url` on `palm-system-*` query; [system/README](examples/definitions/system/README.md); integration test.
- **0.40.4** — Assist **`open:dataset`** (describe + preview query); Assist binds AnalyticsService; virtual view ops **`filter_eq` / `limit` / `sort_by`**.
- **0.40.3** — Journal named consumers (`work_drain` / `webhooks` / `projections`); `consume_for_*` helpers; doctor **`control_plane`** section + lag soft issues.
- **0.40.2** — Optional continuous **WorkDrain** (`PALM_ENABLE_WORK_DRAIN_SERVICE`); trigger **debounce**; **max_depth** drop counter; coalesce storm tests.
- **0.40.1** — Example **trigger dogfood**: `todo-analytics` `options.triggers` on `put-palm-todos` / `palm-todos` → WorkIntent; `host.reload_work_triggers()`; still drain via `tick_work()`.

### Docs

- **0.40+ charter** — [VISION-0.40](docs/vision/closed/VISION-0.40.md): composition-first mesh; 0.36–0.39 open debt; trains 0.40–0.42 (triggers dogfood → durable UX → event transport / provider consumer). [VISION-0.36](docs/vision/closed/VISION-0.36.md) §12a landed vs open.

## [0.39.0] — 2026-07-10

**Bundled release since 0.34.5** — **Analytics data plane** (0.35–0.36) · **WorkIntent / triggers / journal** (0.37–0.38) · **Dashboards** (0.39) · **Palm provider system inspect** + ops datasets.

**Checklist:** [RELEASE-0.39.0.md](docs/releases/RELEASE-0.39.0.md) · **Vision:** [VISION-0.35](docs/vision/closed/VISION-0.35.md) · [VISION-0.36](docs/vision/closed/VISION-0.36.md)

### Added — Analytics data plane (0.35–0.36)

- **0.35** — `AnalyticsService` (list/describe/query), published resources, present profiles `raw|table|series|kpi`, REST `/v1/api/analytics/*`, static `/analytics/`, todos dogfood + definition packs (`coconut/`, `todos/`).
- **0.36** — Virtual views (`source` + `transform` + `materialize`); `count_by`; field roles on describe; doctor analytics preflight; assist menu **datasets**; `palm-todos-by-priority` virtual.

### Added — Reactive control plane (0.37–0.38)

- **0.37** — Pure `WorkIntent`; durable store + coalesce; triggers parse/registry; `resource.changed` on mutating invoke; `WorkDrainService` + `host.tick_work()` (run-when-able).
- **0.38** — `EventJournal` (offsets, consume, compact keys, redrive); `host.control_plane_status()` / `redrive_journal()`.

### Added — Dashboards & system ops (0.39 + provider)

- **0.39** — `DashboardDefinition` / `DashboardTile`; render loop; REST dashboards; UI dashboard mode; [ADR-014](docs/adr/014-dashboard-definitions.md).
- **Palm provider** — system-read actions `list_jobs|instances|waiting|flows|resources` (local + remote).
- **Pack `system/`** — ops datasets + dashboard **`palm-system`** + virtual **`palm-system-instances-per-flow`** (`count_by` `flow_name`).

### Upgrade notes

- Non-breaking for existing MCP/REST flows; new optional surfaces only.
- Hello/version reports **0.39.0**.
- Work drain is **explicit** (`tick_work`); not a continuous Kafka consumer.
- Dashboard registry is in-process (reloaded with example packs on host start).

## [0.34.5] — 2026-07-09

**Bundled release since 0.32.10** — **Assist modularity** (0.33) + **operator remote** menu/open/chat L0 (0.34). No Bot; Assist is the navigation remote; Portal/MCP are clients.

**Checklist:** [RELEASE-0.34.5.md](docs/releases/RELEASE-0.34.5.md) · **Vision:** [VISION-0.33](docs/vision/closed/VISION-0.33.md) · [VISION-0.34](docs/vision/closed/VISION-0.34.md)

### Added — Assist modularity (0.33)

- **0.33.0** — `present/*` presentation pipeline; **tool vs chat** `profiles/`; handoff → `sessions/handoff.py`; views re-export compat.
- **0.33.1** — Execution-shaped leafs: `AssistService.scenarios` / `.sessions` / `.catalog`.
- **0.33.2** — Chat policy (auto-start demos, intro continue, action rewrite) in `assist.profiles`; WS injects dispatch/shape only.
- **0.33.3** — MCP assist dispatch modular (`normalize`, `operator`, `shape/*`).

### Added — Operator remote (0.34)

- **0.34.1 Chat L0** — design intents auto-start **design-entry**; confirm **Yes/No** choices; design handoff CTAs.
- **0.34.2–0.34.3** — `assist/menu` browse/search/page; `assist/open` + `open:kind:id` normalize routing.
- **0.34.4** — Portal menu shell (Menu, search, open tokens); **Browse all flows** CTAs.
- **0.34.5** — Menu typeahead debounce; waiting **Resume** chips; open session `flow_id` polish.
- **Open fix** — `open:flow:…` re-inspects first turn (question + input, not raw `WAITING_FOR_INPUT`).

### Changed

- Assist is Execution-shaped (façade + subdomains); chat continuity no longer lives in WebSocket transport.
- Bot deferred: use menu/open + chat profile instead of a second brain.

### Try it

```bash
uv pip install 'palmengine==0.34.5'   # or uv sync from tag
just palm-server
# Portal: http://127.0.0.1:8080/portal/?open=1
# Menu → Flows → open a flow → first wizard prompt
# WS: wss?://host/ws/v1/assist
```

## [0.32.10] — 2026-07-09

**Bundled release since 0.31.5** — **WebSocket Assist** transport + **Portal dogfood chat** (0.32.0–0.32.10). Same Assist meta-dispatch brain as MCP; human real-time channel for floating UI / future PWA.

**Checklist:** [RELEASE-0.32.10.md](docs/releases/RELEASE-0.32.10.md) · **Vision:** [VISION-0.32.md](docs/vision/closed/VISION-0.32.md)

### Added — WebSocket Assist (0.32.0–0.32.3)

- **0.32 foundation** — [VISION-0.32.md](docs/vision/closed/VISION-0.32.md); design [spec](docs/superpowers/specs/2026-07-09-websocket-assist-portal-design.md) + [plan](docs/superpowers/plans/2026-07-09-websocket-assist-portal-0.32.md).
- **0.32.1 transport MVP** — pure-Python RFC6455 on stdlib HTTP; `GET /ws/v1/assist`; `hello` / `ping`/`pong`; surface info `live`.
- **0.32.2 assist channel** — `dispatch` frames → shared path/alias/params spine → assistant `turn` payloads.
- **0.32.3 Portal input schema + continuity** — structured ``input`` (widget, field_type, choices, collection) on **WebSocket** turns; **MCP omits** ``input`` by default; WS ``bind`` / auto-bind; hello auth mode.

### Added — Portal dogfood (0.32.4–0.32.10)

- **0.32.4** — Static chat at `GET /portal/` (FAB + panel, chips from ``payload.input``).
- **0.32.5** — Human-first demos: skip summary for demo intents; WS **auto-start** todo/compositional/coconut; summary **no** → backtrack; action hygiene.
- **0.32.6** — First-turn lock fix (`include_input_schema` without clobbering assist turns).
- **0.32.7** — Auto-open operator-entry on connect; correct ``bound.flow_id`` after handoff.
- **0.32.8** — Auto-continue introduction steps (land on real work).
- **0.32.9** — Optional field **Skip** chip; active-field ``required``; richer finish blurb; no false ``handoff_ready`` on business flows.
- **0.32.10** — Split ``intro_banner`` / question bubbles; themed scrollbar; pending/thinking indicator.

### Changed

- WebSocket surface is **live** (no longer 501 placeholder).
- Prefer `include_input_schema` only on human transports (WS); MCP stays token-lean.
- Portal is a **dogfood** shell, not a full product PWA (auth, events, Android deferred).

### Try it

```bash
just palm-server   # or: uv run palm server
# open http://127.0.0.1:8080/portal/?open=1
# ws: /ws/v1/assist
```

## [0.31.5] — 2026-07-08

**Bundled release since 0.30.7** — terminal assistant polish (0.30.8) and **MCP meta-surface / progressive disclosure** (0.31.0–0.31.4). Upgrade notes: [MIGRATION-0.30.md](docs/migrations/MIGRATION-0.30.md) (§ 0.31.1 surface, 0.31.2 aliases).

**Checklist:** [RELEASE-0.31.5.md](docs/releases/RELEASE-0.31.5.md)

### Added — MCP meta-surface (0.31)

- **0.31 foundation** — [VISION-0.31.md](docs/vision/closed/VISION-0.31.md); [design](docs/superpowers/specs/2026-07-08-mcp-meta-surface-design.md) + open [plan](docs/superpowers/plans/2026-07-08-mcp-meta-surface-0.31.md).
- **0.31.1 surface profiles** — `PALM_MCP_SURFACE=full|assist|core|experimental`; assist-only ≈1 tool; `just mcp-inventory` / `scripts/mcp_catalog_inventory.py`.
- **0.31.2 assist-complete paths** — aliases `assist/doctor`, `assist/catalog/flows`, `assist/catalog/waiting`, `flows/session-resume`; assistant envelopes; CTAs use aliases.
- **0.31.3 progressive docs** — L0 short tool description; L1 `palm://agent/card` (`docs/mcp-card.txt`); L2 full guide on demand; publish CTAs → `palm_assist`.
- **0.31.4 assist/discover** — `alias=assist/discover` (+ optional `query`); AGENTS/README/llms/skill assist-first refresh.

### Added — Terminal polish (0.30.8)

- Complete turns: “Finished. Answers: …” blurb; waiting **Send answer** CTA; complete **Run again** + operator-entry.

### Changed

- Default MCP surface remains **`full`** (backward compatible). Token-sensitive hosts should set **`PALM_MCP_SURFACE=assist`**.
- Prefer progressive docs: card before full guide/skill dumps.

## [0.30.7] — 2026-07-08

**Bundled release since 0.26.0** — compositional design parity (0.27), local document/KV resources (0.28–0.29), and Assist design-entry + weak-LLM operator UX (0.30.0–0.30.6). Upgrade from 0.26.0: read [MIGRATION-0.30.md](docs/migrations/MIGRATION-0.30.md) (and 0.24/0.25 if jumping from older cuts).

**Checklist:** [RELEASE-0.30.7.md](docs/releases/RELEASE-0.30.7.md)

### Added — Assist design entry & weak-LLM MCP (0.30)

- **0.30 foundation** — [VISION-0.30.md](docs/vision/closed/VISION-0.30.md); design [spec](docs/superpowers/specs/2026-07-08-assist-design-entry-design.md) + [plan](docs/superpowers/plans/2026-07-08-assist-design-entry-0.30.md).
- **0.30.1 design discovery CTAs** — operator-entry intents `create-flow` / `improve-flow`; assistant action merge + `OperatorViewContext.intent`; `inspect_catalog` propose CTA; metadata `handoff_none_hints`.
- **0.30.2 design-entry scenario** — `design-entry` / `design-entry/start`; Design tool CTAs only (no catalog writes on start).
- **0.30.3 design handoff** — `kind: design` with `design_action` / `base_flow_id` / `suggested_name`; post-terminal re-entry CTAs; [MIGRATION-0.30.md](docs/migrations/MIGRATION-0.30.md).
- **0.30.4 one-shot design publish** — `palm_design_publish_flow` / `palm_design_publish_resource` (propose→impact→commit); compact design CTAs and hints.
- **0.30.5 design path shortening** — operator-entry design intents skip summary confirm; design-entry drops summary; `palm_assist(params={body})` → `design/publish`.
- **0.30.6 assist flow + resource ergonomics** — `palm_assist` defaults assistant on flows create/session; `params={flow_id}` starts a flow; create re-inspects first turn; operator-entry adds `coconut-npc` + `propose-resource`; resource failures surface resume/doctor/publish-resource CTAs.

### Added — Compositional design parity (0.27)

- **Example flow `coconut-npc`** — branching wizard reference (hub menu, transforms, routing); MCP dogfood profile.
- **Wizard design contributor** — flat transform steps validate like runtime builder.
- **Prompt interpolation** — `{{ state.key }}` in wizard `prompt` / `title` ([ADR-010](docs/adr/010-prompt-state-interpolation.md)).
- **Design `propose_resource`** — impact scan for referencing flows; `palm_design_propose_resource`.
- **`palm://agent/references/branching-flows`** — hub menu / routing playbook for weak LLMs.
- **Resource operator ergonomics** — doctor `resource_preflight`; wizard `on_resource_failure`; provider invoke remediation; powertool `resource_error` / `resource_remediation`.
- **`step_kind: branch`** — state-driven BT routing ([ADR-012](docs/adr/012-wizard-branch-step.md)).

### Added — Local document resources (0.28) & tiered KV (0.29)

- **`kv` resource provider** — `get`/`put`/`delete`/`list`; `backend: auto|memory|storage`; coconut player profile load/save.
- **`file` document provider** — `read`/`write`/`delete`/`exists`/`list` under `documents_root`.
- **Coconut cross-session persistence** — KV keyed by `player_name`; visit counts / reputation for returners.
- **KV/file design contributors + doctor preflight** — [ADR-011](docs/adr/011-local-document-resources.md).
- **Tiered KV backend** — hot memory + cold storage, LRU eviction (`hot_max_keys`).

### Changed

- Agent skill / `mcp.txt` emphasize one-shot publish, `palm_assist` as primary driver, and coconut as the resource-backed reference flow.
- Bare `palm_assist()` remains operator-entry; design is sibling intent/scenario (not a new default).

### Migration notes

- Prefer `palm_design_publish_*` over multi-step propose→impact→commit for agents.
- Treat unknown handoff `kind` like `none` and always read `operator_hint` (`kind: design` in 0.30.3+).
- Flows via `palm_assist` are assistant-first; direct `palm_flows_*` stay powertool-default.

## [0.26.0] — 2026-07-08

**Design Service hardening and CQRS bus parity** — post-0.25.0 quality release. No breaking API changes vs 0.25.0; upgrade path is drop-in.

### Added

- **Design CQRS transport** (`0.25.7`) — `ProposeFlowDefinitionCommand`, `CommitDesignProposalCommand`, design query types; bus tests via `ApplicationHost`.
- **Registry-driven design dispatch** (`0.25.8`) — `design_commands()` + handler table; `match_command_path` / `resolve_design_command`.
- **Service CQRS contributors** (`0.25.9–0.25.12`) — `ServiceCqrsContributor` registry; `definitions/bindings/cqrs/` for impact/migrate; unified `collect_cqrs_catalog()` for host and standalone.
- **Pipeline design contributor** (`0.25.5`) — transform step validation on proposals.
- **Pattern design contributor hook** (`0.25.4`) — `DesignContributorHook` drained at host bootstrap (wizard, pipeline).
- **Design proposal demo** (`0.25.6`) — end-to-end propose → commit + auto-migrate; meta-flow sketch.
- **ADR-009** — [service CQRS contributors](docs/adr/009-service-cqrs-contributors.md).
- **Tests** — `test_mcp_design_in_process.py`, `test_definitions_cqrs_standalone.py`, `test_cqrs_bus_catalog_parity.py`, `test_design_dispatch.py`.

### Changed

- **`wire_all_service_cqrs()`** — host and `ServerContext` wire definitions + design transport after generic bus registration.
- **`build_schema_registry()`** — drains service contributor schemas (design).
- **Host CQRS** — definitions impact/migrate handlers moved to service bindings (no duplication in `HostQueryHandlers`).

### Fixed

- **In-process MCP** — `palm_design_impact` and `palm_design_commit` failed with `No handler registered for AnalyzeDefinitionImpactQuery` on standalone `ServerContext`; standalone bus now registers definitions CQRS types.
- **Design commit correctness** (`0.25.2`) — re-runs impact before auto-migrate; `DesignCommitRejectedServiceError` for token failures; `next_revision_for_flow()` helper.
- **Proposal storage index** (`0.25.3`) — non-open proposals removed from index on save.
- **Shared path utilities** — `path_match.py` + `path_alias.py` for MCP alias ↔ path matching.

## [0.25.0] — 2026-07-07

**Definition revisioning, instance migration, and Design Service** — one PyPI release bundling the full 0.24 stack and complete 0.25 design orchestration. Jump from 0.23.1: read [MIGRATION-0.24.md](docs/migrations/MIGRATION-0.24.md) and [MIGRATION-0.25.md](docs/migrations/MIGRATION-0.25.md).

### Added — Design Service (0.25)

- **`palm/services/design/`** — sixth service domain: `propose_flow` → `validate_proposal` → `analyze_proposal_impact` → `commit_proposal`.
- **`host.design`** / `ServerContext.design` · REST `/v1/api/design/proposals` · MCP `palm_design_*`.
- **Durable proposals** — `StorageDesignProposalRepository` (`palm:design:proposals:{id}`) when storage is active.
- **Auto-migrate on commit** — compatible instances migrated after revision publish; `migrations` summary in commit response.
- **Agent safety** — `commit_token` on validate/impact; `PALM_MCP_REQUIRE_INPUT_TOKEN` applies to `palm_design_commit`.
- **`palm_assist` design paths** — `design/*` aliases, dispatch, assistant views on validate/impact.
- **Wizard design contributor** — step slug uniqueness, collection `item_fields`, resource/transform checks.
- **Docs** — [ADR-008](docs/adr/008-design-service.md), [MIGRATION-0.25.md](docs/migrations/MIGRATION-0.25.md), `examples/definitions/design_proposal_demo.py`.

### Added — Definition revisioning & migration (0.24, bundled)

- **Append-only flow revisions** — `update_flow` publishes `latest + 1`; optional `?revision=N` on get.
- **Instance revision pin** — `flow_revision` on submit; snapshot retained until migration.
- **Migration rules** — `register_migration_rule()` in `definition_migration.py`.
- **Impact query** — instances behind target revision with compatibility flags.
- **Instance migration** — `POST …/instances/{id}/migrate`; `migration_*` metadata preserved on job sync.
- **MCP** — `palm_definitions_analyze_impact`, `palm_definitions_migrate_instance`.
- **Docs** — [MIGRATION-0.24.md](docs/migrations/MIGRATION-0.24.md), [ADR-007](docs/adr/007-definition-revisioning.md).

### Changed

- **Agent policy** — prefer `palm_design_*` for catalog writes; `palm_definitions_*` direct CRUD remains for integrators.
- **`update_flow` semantics** — append revision, not in-place overwrite (see MIGRATION-0.24).

### Fixed

- **CQRS schemas** — `GetFlowQuery.revision` and `AnalyzeDefinitionImpactQuery.target_revision` accept `null`.

## [0.24.4] — 2026-07-07

**Documentation cleanup** — align operator surfaces with shipped 0.24.1–0.24.3 revisioning and migration.

### Added

- **`MIGRATION-0.24.md`** — revision semantics, impact/migrate REST, agent workflow.
- **MCP tools** — `palm_definitions_analyze_impact`, `palm_definitions_migrate_instance`.
- **`docs/mcp.txt` §14** — definition revision migration operator loop.
- **Route tests** — impact + migrate paths in definitions REST table.

### Changed

- **`STATUS.md`**, **`VISION-0.24.md`**, **`ADR-007`**, **`AGENTS.md`** — 0.24.1–0.24.4 status; migration rule path corrected to `common/persistence/definition_migration.py`.
- **`docs/MCP.md`**, **`docs/llms.txt`**, **`README.md`**, **`DEVELOPMENT.md`** — 0.24 capabilities and operator references.
- **Assist dispatch** — `definitions/flows/{id}/impact`, `definitions/instances/{id}/migrate` paths.

## [0.24.3] — 2026-07-07

**Instance migration execution** — apply migration rules to durable instances.

### Added

- **`migrate_instance()`** — dry-run and apply; updates `flow_revision`, snapshot, and definition pin.
- **`MigrateInstanceCommand`** + `DefinitionService.migrate_instance()`.
- **REST** — `POST /v1/api/definitions/instances/{instance_id}/migrate`.
- **Instance metadata** — `migration_status`, `migration_target_revision`, `migration_from_revision`, `migration_blockers`.
- **Job sync** — preserve `migration_*` keys in `update_instance_from_job`.
- **Example** — `migrate-instance-demo` wizard (`examples/definitions/migrate_instance_demo.py`).
- **Tests** — `test_instance_migration.py`, `test_instance_sync_migration_metadata.py`.

## [0.24.2] — 2026-07-07

**Migration rules + impact query** — compatibility analysis before upgrading instances.

### Added

- **`definition_migration.py`** — `MigrationContext`, `DefinitionMigrationRule`, `register_migration_rule()`.
- **`definition_impact.py`** — `analyze_definition_impact()`.
- **`AnalyzeDefinitionImpactQuery`** + `DefinitionService.analyze_impact()`.
- **REST** — `GET /v1/api/definitions/flows/{flow_id}/impact`.
- **Tests** — `test_definition_migration_rule.py`, `test_definition_impact_query.py`.

## [0.24.1] — 2026-07-07

**Append-only flow revisions** — catalog evolution without silent overwrites.

### Added

- **`publish_flow_revision`** — monotonic revisions per `flow_id`; repository key layout `flow:{id}:rev:{n}`.
- **`ProcessInstance.flow_revision`** — explicit pin on submit.
- **`GET flow?revision=`** — load explicit revision.
- **Tests** — `test_definition_repository_revisions.py`, `test_flow_submission_revision.py`.

### Changed

- **`update_flow`** / **`create_flow`** — publish revisions (append-only semantics).

## [0.23.1] — 2026-07-03

**Inspect-only catalog** — operator-entry menu item 3 no longer commits on summary `yes`.

### Added

- **Wizard step routing** — `route_on_answer` and `complete_on` in step `params`.
- **Operator-entry `catalog` step** — non-terminal read mode until `exit`.
- **`operator-entry/inspect`** MCP alias — read-only catalog via `AssistService.inspect_catalog()`.
- **`operator_mode: inspect`** on instance metadata at catalog step.
- **Choice menu coercion** — numeric picks (e.g. `3`) on assist input path.

### Changed

- **`inspect-only` intent** — routes to catalog, skips summary; handoff stays `none` until exit.
- **`docs/mcp.txt` §13** — inspect-only catalog semantics.

## [0.23.0] — 2026-07-03

**input_token strict mode** — CSRF-style mutation gate for agent hardening (opt-in).

### Added

- **`input_token`** on `mutation` envelope when `mutations_allowed`; HMAC-bound to session + step.
- **`issue_input_token`**, **`validate_input_token`**, **`require_mutation_token`** in `palm/common/operator/mutation_gate.py`.
- **Instance metadata** `mutation_gate` — rotated on inspect (`sync_gate=True` paths).
- **`PALM_MUTATION_SECRET`**, **`PALM_MCP_REQUIRE_INPUT_TOKEN`** env vars (`.env.example`, `MIGRATION-0.23.md`).
- **`input_token`** param on `palm_flows_session_input` and REST session input bodies.
- **Tests** `tests/test_mutation_gate_token.py`; replay harness strict-mode pass.

### Changed

- **`apply_flows_session_input`** — validates token before mutations when strict mode enabled.
- **`docs/mcp.txt` §12** — strict-mode drive loop for agents.

## [0.22.1] — 2026-07-03

**Mutation envelope protocol** — read vs drive signals on inspect views; inspect guard docs.

### Added

- **`mutation` envelope** on assistant/powertool inspect (`mutations_allowed`, `confirm_step`, `agent_hint`).
- **`palm/common/operator/mutation_gate.py`** — `build_mutation_envelope()`.
- **Inspect vs drive** rules in `docs/mcp.txt` §11 and agent skill.
- **Replay harness** `tests/test_conversation_replay_inspect_guard.py` (xfail documents tc4 until 0.23.0).

### Changed

- **Version** `0.22.1` on documentation surfaces.

## [0.22.0] — 2026-07-03

**Agent skill release** — portable skill as MCP resources, operator guide split, Docker stack documentation.

### Added

- **`docs/mcp.txt`** — focused MCP operator guide (default `palm://agent/guide` via `PALM_LLMS_TXT`).
- **`docs/skills/palm/`** — portable agent skill + references (manual adoption for any agent host).
- **MCP resources** — `palm://agent/skill`, `palm://agent/references/agent-guide`, `…/mcp-patterns`, `…/session-management`, `…/common-flows`.
- **`palm.runtimes.mcp.agent_assets`** — skill path resolution (`PALM_SKILL_DIR`, bundled `data/skills/palm/`).
- **`palm.runtimes.mcp.descriptions.tool_description()`** — weak-LLM-friendly MCP tool docstrings.
- **`docs/DOCKER.md`** — Docker Compose stack, volumes, HTTP MCP against container, troubleshooting.
- **`.grok/skills/palm/`** — Grok Build mirror (synced from `docs/skills/palm/` via `docs-check`).
- **`MIGRATION-0.22.md`** — agent doc split and resource migration guide.

### Changed

- **`palm_assist`**, **`palm_flows_session`**, **`palm_flows_session_input`**, **`palm_flows_list`**, **`palm_flows_create_session`**, **`palm_system_doctor`** — enriched descriptions with `call_connected_tool` prefix.
- **Docker** — `PALM_SKILL_DIR=docs/skills/palm` in Dockerfile and compose; `docs/` copied into image.
- **`docs/llms.txt`** — project context only; points to `docs/mcp.txt` for operator guide.
- **Version** `0.22.0` on documentation surfaces.

## [0.21.12] — 2026-07-01

**Weak-LLM MCP ergonomics (0.21.10–0.21.12 bundle)** — unified `palm_assist` flows driving, edit shortcuts, replay harness.

### Added

- **Flows path inference** — `palm_assist(params={session_id, flow_id, value})` without explicit `path`.
- **MCP aliases** — `flows/session-input`, `flows/session`.
- **`apply_flows_session_input`** — shared coercion + collection one-shot/edit in flows service dispatch.
- **Collection edit shortcut** — `params.edit={item_index, …fields}` chains menu → select → fields.
- **Fuzzy menu coercion** — `add`/`edit`/`done`/`continue` tokens map to menu choice labels.
- **Priority intent** — `"high priority"` → `"high"` on collection priority fields.
- **Replay harness** — `tests/test_conversation_replay_019f1e9c.py` (todo-builder weak-LLM path).

### Changed

- **Collection `actions`** — use `flows/session-input` alias with `flow_id` + `session_id`.
- **`operator_hint`** — recommends `palm_assist(params={…})` for waiting sessions.
- **Version** `0.21.12` on documentation surfaces.

## [0.21.9] — 2026-07-01

**Assistant envelope on flows mutations** — opt-in human view after session input.

### Added

- **`palm_flows_session_input(format="assistant")`** — returns `question`, `choices`, `hint` after input.
- **`palm_wizard_collection_action(format="assistant")`** — same opt-in on collection mutations.
- **Collection `actions` block** — `build_collection_assistant_actions` on menu-phase assistant turns.
- **Flows REST** `POST …/input?format=assistant` — parity with GET session (already wired via `_session_body`).

### Changed

- **`build_assistant_view`** — merges collection menu `actions` when `flow_id` is set.
- **Version** `0.21.9` on documentation surfaces.

## [0.21.8] — 2026-07-01

**Collection one-shot add** — weak LLMs can add a titled item in one MCP call.

### Added

- **`drive_collection_add`** in `palm/common/operator/collection_drive.py` — menu `add` + field `value` in one helper.
- **`palm_wizard_collection_action(action=add, value=…)`** — one-shot at menu phase (no menu-phase error).
- **`palm_flows_session_input(input="add", value=…)`** — same one-shot via coercion sentinel.

### Changed

- **Version** `0.21.8` on documentation surfaces.

## [0.21.7] — 2026-07-01

**Weak-LLM MCP hotfixes** — boot reliability, null param coercion, human-first `palm_assist` defaults.

### Fixed

- **MCP boot:** `shape_flow_session_view` moved to `palm/common/operator/flow_session_view.py` (break circular import blocking `palm-mcp` startup).
- **`palm_assist`:** Accept `action`/`format: null` from weak LLM clients.
- **`palm_assist`:** Bare `{}` starts `operator-entry`; infer `session_id` + `value`/`input` continuation paths via `normalize_assist_dispatch_args`.

### Changed

- **`MIGRATION-0.21.md`**, **`docs/MCP.md`**, **`docs/llms.txt`**, **`AGENTS.md`** — weak-LLM MCP defaults documented.
- **Version** `0.21.7` on documentation surfaces.

## [0.21.6] — 2026-07-01

**0.21 release complete** — migration guide, agent docs, verification.

### Added

- **`MIGRATION-0.21.md`** — CLI/Explorer entry, `actions` block, flows `format=assistant` opt-in
- **`RELEASE-0.21.6.md`** — release checklist and verify commands

### Changed

- **`docs/MCP.md`**, **`docs/llms.txt`**, **`AGENTS.md`** — 0.21 human surfaces and flows opt-in documented
- **`MIGRATION-0.20.md`** — cross-link to 0.21 shipped features
- **Version** `0.21.6` on documentation surfaces

## [0.21.5] — 2026-07-01

**Flows assistant opt-in** — human envelope on business sessions without changing defaults.

### Added

- **`palm_flows_session(format="assistant")`** — opt-in assistant envelope (`question`, `choices`, `hint`)
- **Flows REST** `?format=assistant|powertool|verbose` on session inspect routes

### Changed

- **`palm_flows_session`** default `format` is `powertool` (`compact` alias retained)
- **`shape_dispatch_result`** flows branch delegates to `shape_flow_session_view` when `params.format=assistant`
- **`palm_assist`** on flows session paths respects `params.format=assistant` (tool-level `format` alone still powertool)

## [0.21.4] — 2026-07-01

**Assistant envelope depth** — `actions` block and production enrichers.

### Added

- **`actions` block** — progressive disclosure from `next_commands` (`label`, `path`, `alias`)
- **`AssistContributor.assistant_enricher`** — auto-registers on `register_assist_contributor`
- **Operator-entry enricher** — handoff CTA in `examples/definitions/operator_entry.py`
- **REST** `GET /v1/api/assist/catalog/flows` — parity with assist dispatch command

### Changed

- **`AssistSessionContext.to_dict`** — includes `actions` on `format=assistant`

## [0.21.3] — 2026-07-01

**Explorer assist HTMX** — interactive session verbs in the browser.

### Added

- **POST** `/explorer/assist/session/{id}/input|backtrack|cancel|handoff` — HTMX partial updates on `#assist-workspace`
- **`assist_input_form`**, **`assist_handoff_form`**, **`assist_session_toolbar`** — choice buttons + text input
- **`assist_handoff_result`** — handoff card with link to flows submit

### Changed

- **`assist_workspace`** — interactive forms replace read-only 0.21.2 placeholder

## [0.21.2] — 2026-07-01

**Explorer assist panel** — catalog, start, and assistant workspace.

### Added

- **`/explorer/assist`** — scenario catalog and detail pages
- **`assist_workspace`** — SSR consumer of assistant envelope (`question`, `choices`, `compose`)
- **`ExplorerFetcher`** assist methods — `list_assist_scenarios`, `start_assist_scenario`, `get_assist_session`
- **Tests** — `tests/test_explorer_assist_ssr.py`

### Changed

- **Explorer nav** — Assist entry in sidebar and overview link card

## [0.21.1] — 2026-07-01

**CLI assist commands** — REPL consumes 0.20 assistant envelope.

### Added

- **`assist list|start|input|handoff|status|cancel`** — CLI commands via `host.assist`
- **`render_assistant_panel`** — Rich panel for `question`, `choices`, `hint`, `handoff_ready`
- **`dispatch_repl_line`** — plain REPL input routes to assist when session active
- **`CliContext.active_assist_session_id`** — assist session tracking
- **Tests** — `tests/test_cli_assist.py`

### Changed

- **REPL welcome** — recommends `assist start operator-entry`
- **`help`** — assist command section

## [0.21.0] — 2026-07-01

**Design** — Assistant expansion: human surfaces + envelope depth (implementation 0.21.1–0.21.6).

### Added

- **Spec** — [docs/superpowers/specs/2026-07-01-assistant-expansion-design.md](docs/superpowers/specs/2026-07-01-assistant-expansion-design.md): CLI `assist *` commands, Explorer `/explorer/assist` panel, `actions` block, opt-in flows `format=assistant`

## [0.20.5] — 2026-07-01

**0.20 release complete** — migration guide, agent docs, verification.

### Added

- **`MIGRATION-0.20.md`** — assistant vs powertool migration for assist surfaces
- **`RELEASE-0.20.5.md`** — release checklist and verify commands

### Changed

- **`docs/llms.txt`** — 0.20.5 agent rules (two view modes, typical session examples)
- **`docs/MCP.md`** — `palm_assist` `format` param; link to `MIGRATION-0.20.md`
- **`AGENTS.md`** — assistant/powertool conventions for MCP operators

## [0.20.4] — 2026-07-01

**`palm_assist` format default** — assistant on assist paths; powertool on flows/system.

### Added

- **`palm_assist` `format` param** — default `assistant`; `powertool` / `verbose` opt-in
- **`shape_dispatch_result`** + **`resolve_dispatch_format`** in assist MCP dispatch

### Changed

- Flows/system paths dispatched via `palm_assist` remain **powertool** regardless of tool default
- REST assist dispatch forwards `format` query param when set

## [0.20.3] — 2026-07-01

**Assist session defaults** — assistant envelope on service + REST; start returns first turn.

### Changed

- **`AssistSessionContext.to_dict`** — defaults to `format=assistant`; `verbose` and `powertool` opt-in
- **`start_scenario`** — returns first assistant turn (question + choices), not ids-only
- **REST assist handlers** — `?format=assistant|powertool|verbose` on session routes
- **MCP assist dispatch** — passthrough assistant envelopes (`question` field)

## [0.20.2] — 2026-07-01

**Assistant views** — compose + humanize pipeline registered from assist domain.

### Added

- **`palm/services/assist/views.py`** — `build_assistant_view`, compose-always pipeline, humanized envelope
- **`register_assistant_enricher`** on assist registry — per-scenario post-humanize hooks
- **`OperatorViewContext.handoff_ready`** — assist handoff shaping
- **Tests** — `tests/test_assistant_view.py`

### Changed

- **`AssistService`** — registers `assistant` view builder at construction

## [0.20.1] — 2026-07-01

**Operator view registry** — thin format dispatch in common; powertool registered by default.

### Added

- **`palm/common/operator/view_registry.py`** — `OperatorViewContext`, `register_operator_view_builder`, `build_operator_view`, `compact` → `powertool` alias
- **Tests** — `tests/test_operator_view_registry.py`

## [0.20.0] — 2026-07-01

**Design** — Assistant vs Powertool operator view split (implementation 0.20.1–0.20.5).

### Added

- **Spec** — [docs/superpowers/specs/2026-07-01-assistant-powertool-views-design.md](docs/superpowers/specs/2026-07-01-assistant-powertool-views-design.md): assistant (compose + human) default on assist surfaces; powertool (today's compact) on flows/system; thin `view_registry` in common

## [0.19.1] — 2026-07-01

**Bugfix** — `palm_assist` compact shaping for in-process flow session dispatch.

### Fixed

- **`compact_dispatch_result`** — coerce `SessionContext` dataclass results to dicts before compact branching so `palm_assist` flow session inspect/input returns slim operator snapshots (not verbose `result` blobs)

## [0.19.0] — 2026-07-01

**Stable MCP proxy** — single `palm_assist` dispatch tool for agent config stability.

Migration: [MIGRATION-0.19.md](docs/migrations/MIGRATION-0.19.md) · Vision: [docs/vision/closed/VISION-0.18-ASSIST.md](docs/vision/closed/VISION-0.18-ASSIST.md)

### Added

- **`palm_assist`** MCP tool — parametric `path` / `alias` / `params` dispatch
- **`palm://assist/routes`** — generated command-path catalog + contributor aliases
- **`mcp_aliases`** on `AssistContributor` — stable alias map (`operator-entry/start`, etc.)
- **`assist_dispatch`** on in-process and REST MCP backends
- **Tests** — `test_palm_assist_tool.py`, `test_assist_mcp_aliases.py`

### Changed

- **`docs/MCP.md`**, **`docs/llms.txt`** — document `palm_assist` operator loop
- Per-domain MCP tools (`palm_flows_*`, …) **unchanged** — migration optional

## [0.18.0] — 2026-07-01

**Assist domain MVP** — fifth service for conversational operator guidance and handoff.

Migration: [MIGRATION-0.18.md](docs/migrations/MIGRATION-0.18.md) · Vision: [docs/vision/closed/VISION-0.18-ASSIST.md](docs/vision/closed/VISION-0.18-ASSIST.md)

### Added

- **`palm/services/assist/`** — `AssistService`, `AssistSession`, command registry, grammar
- **`host.assist`** — wired on `ApplicationHost` and `ServerContext`
- **REST `/v1/api/assist/…`** — scenarios, session verbs, doctor shortcut, handoff
- **`palm-operator-entry`** — assist catalog scenario (`examples/definitions/operator_entry.py`)
- **`palm/app/assist_registry.py`** — app-level assist contributor registry
- **OpenAPI Assist group** — `openapi_registry.py` aggregates assist routes
- **Tests** — `test_assist_*`, `test_operator_entry_flow.py`

### Changed

- **`INSTALLED_SERVICES`** — includes `"assist"`
- **`STATUS.md`**, **`docs/MCP.md`**, **`docs/llms.txt`**, **`AGENTS.md`** — assist surface documented
- **ADR-006** — status Accepted

### Notes

- MCP unchanged in 0.18; stable `palm_assist` proxy deferred to 0.19
- Assist wizards support existing `step_kind: resource` compositional steps

## [0.17.3] — 2026-07-01

**OpenAPI from service registries** — `/v1/openapi.json` and `/v1/docs` document the full `/v1/api/…` surface.

Migration: [MIGRATION-0.17.md](docs/migrations/MIGRATION-0.17.md) · Plan: [docs/superpowers/plans/2026-07-01-0.17-service-completion.md](docs/superpowers/plans/2026-07-01-0.17-service-completion.md)

### Added

- **`openapi_registry.py`** — aggregates per-service `ROUTES` into `RouteDefinition` metadata
- **`tests/test_openapi_registry.py`**

### Changed

- **`openapi.py`**, **`docs.py`**, **`doc_examples.py`** — full service-domain route catalog
- **`routes.py`** — registers meta routes only; service routes remain on `service_routes.py`
- **`ARCHITECTURE.md`** — REST/OpenAPI layout note

### Fixed

- OpenAPI/HTML docs no longer meta-only after 0.17 monolith route removal

## [0.17.2] — 2026-07-01

**Palm provider remote alignment** — compositional remote client uses `/v1/api/…` only.

Migration: [MIGRATION-0.17.md](docs/migrations/MIGRATION-0.17.md)

### Changed

- **`submit_flow_remote`** → `POST /v1/api/flows/{flow_id}/create`
- **`get_job_remote`** → `GET /v1/api/system/jobs/{job_id}`
- **`submit_process_remote`** → `/v1/api/processes/{process_id}/prepare` + `/submit`
- **`remote_job_payload`** — maps `session_id` to `instance_id`

### Documentation

- **`docs/PROVIDER-APPS.md`** — remote binding path table

## [0.17.1] — 2026-07-01

**Process execution service** — multi-flow runs under `/v1/api/processes/…`; legacy `/v1/plans` removed.

Migration: [MIGRATION-0.17.md](docs/migrations/MIGRATION-0.17.md)

### Added

- **`ProcessExecutionService`** — `prepare`, `submit`, `run`, `dispatch` with command-path grammar
- **REST** — `POST /v1/api/processes/{process_id}/prepare`, `/submit`, `/run`
- **Registry** — `process_commands()` in `execution/processes/registry.py`

### Changed

- **`PalmRestClient`** / in-process MCP — plan staging via `/v1/api/processes/…`
- **`ServerContext`** — wires `ProcessExecutionService` with runtime for submit idle sync

### Removed (breaking)

- **`POST /v1/plans/prepare`**, **`POST /v1/plans/submit`** monolith routes

## [0.17.0] — 2026-07-01

**System REST parity** — observe/lifecycle HTTP under `/v1/api/system/…`; legacy monolith job/instance/snapshot routes removed.

Migration: [MIGRATION-0.17.md](docs/migrations/MIGRATION-0.17.md) · Plan: [docs/superpowers/plans/2026-07-01-0.17-service-completion.md](docs/superpowers/plans/2026-07-01-0.17-service-completion.md)

### Added

- **System REST** — `inspect_job`, `cancel_job`, `list_instances`, `inspect_instance`, `instance_tree`, snapshots, `resume_instance` on `/v1/api/system/…`
- **`tests/test_system_service_routes.py`**, **`tests/test_rest_system_routes.py`**

### Changed

- **`PalmRestClient`** — waiting jobs, job context, cancel, tree, snapshots → `/v1/api/system/…`; `provide_job_input` delegates to flows session input
- **`job_context.next_actions`** — flows session input + system instance/job paths
- Wizard read model and invoke tree links → system service paths
- Explorer SSR copy and doc examples updated

### Removed (breaking)

- **`GET/POST /v1/jobs`** monolith routes (submit → `/v1/api/flows/{flow_id}/create`; input → flows session)
- **`/v1/instances`**, **`/v1/snapshots`** monolith routes

## [0.16.5] — 2026-07-01

**Services are the API** — domain services in `palm/services/`, per-service REST under `/v1/api/…`, MCP remounted by service domain. Breaking release for integrators on legacy `/v1/wizards` and monolithic MCP tool names.

Vision: [docs/vision/closed/VISION-0.16.md](docs/vision/closed/VISION-0.16.md) · ADR: [docs/adr/005-service-domain-api.md](docs/adr/005-service-domain-api.md) · Migration: [MIGRATION-0.16.md](docs/migrations/MIGRATION-0.16.md) · MCP: [docs/MCP.md](docs/MCP.md)

### Added

- **`palm/services/`** — `definitions`, `execution/flows`, `execution/providers`, `system` with per-domain `registry.py` and `dispatch()` command-path grammar
- **REST `/v1/api/…`** — definitions catalog + CRUD, flow session REPL, provider invoke, system doctor/jobs
- **MCP per-domain tools** — `palm_flows_*`, `palm_system_*`, `palm_definitions_*`, `palm_providers_invoke` (26 tools total with pattern contributors)
- **`ProviderExecutionService`** — `host.execution.providers.invoke()` with provider validation
- **Definitions CRUD** — `POST/PUT/DELETE` on `/v1/api/definitions/{flows,processes,resources}/…`
- **`FlowSession` / `SessionContext`** — service-layer session handles; `session_id` terminology at API boundary

### Changed

- **`host.internal`** → **`host.system`** (`SystemService`)
- **`host.execution.on(id)`** → **`host.execution.flows`** session API (`dispatch`, `FlowSession`)
- Explorer SSR and operator hints updated to `/v1/api/flows/…` and `palm_flows_*` tool names
- MCP prompts and `docs/llms.txt` agent guide rewritten for 0.16 conventions

### Removed (breaking — no deprecation window)

- **`/v1/wizards`** REST surface and `handlers/wizard.py`
- Legacy catalog routes (`/v1/flows`, `/v1/processes`, `/v1/resources`, `/v1/doctor`, `/v1/flows/validate`)
- **`POST /v1/resources/invoke`** — replaced by `/v1/api/providers/{provider}/{resource_ref}/invoke`
- Orphaned monolith handlers `handlers/catalog.py`, `handlers/resources.py`
- Monolithic MCP tools (`palm_submit_wizard`, `palm_inspect_instance`, `palm_wizard_input`, `palm_doctor`, …)

### Transitional (at 0.16.5 ship; removed in 0.17.0)

- `/v1/jobs`, `/v1/instances`, `/v1/snapshots` — migrated to `/v1/api/system` in **0.17.0**
- `/v1/plans` — remains until **0.17.1**

## [0.15.4] — 2026-06-30

**Service layer release** — CQRS schemas, `palm.common.services`, in-process MCP, REST schema dedupe, and legacy cleanup. PyPI packages the full 0.15 track (internal milestones 0.15.1–0.15.3 on master).

Vision: [docs/vision/closed/VISION-0.15.md](docs/vision/closed/VISION-0.15.md) · ADR: [docs/adr/004-cqrs-schemas-service-layer.md](docs/adr/004-cqrs-schemas-service-layer.md) · MCP: [docs/MCP.md](docs/MCP.md)

### Added

- **`CqrsSchemaRegistry`** — `DictStateSchema` per command/query; patterns contribute via `CqrsContributor.command_schemas` / `query_schemas`
- **Service layer** (`palm/common/services/`) — `InternalService`, `DefinitionService`, `ExecutionService`, `InstanceSession`, `ReplSession`, `BaseService` with schema-validated dispatch
- **Instance-centric API** — `host.execution.on(instance_id).input("yes")`; `ReplSession` for CLI REPL
- **`PalmInProcessBackend`** — MCP tools call services on `ServerContext` when `PALM_MCP_IN_PROCESS=1` (default in `.grok/config.toml`)
- **`rest/schema_bridge.py`** — REST input bodies projected from `CqrsSchemaRegistry`
- **`ServerContext.schemas`** — registry exposed for REST handlers
- **Docs** — `docs/VISION-0.15.md`, ADR 004, cleanup track specs/plans under `docs/superpowers/`

### Changed

- REST inspect/catalog/wizard writes delegate to services (thin handlers)
- MCP local mode avoids HTTP round-trip when in-process
- REST `provide_input` / wizard input validation uses registry (single source of truth)
- Definition views imported from `palm.common.services.views` (serializer shim trimmed)
- Ruff import hygiene across `src/` and `tests/`; wizard packages exempt from isort (`I001`) for circular-import safety

### Removed (experimental — no deprecation window)

- `create_cli_app()` — use `create_cli_host()`
- `interactive_runtime` wizard aliases (`resolve_wizard_job`, `provide_wizard_input_for_instance`, …)
- `ChildWizardCompletionHook` — use `ChildCompletionHook`
- `serializers.py` re-exports of `views.py` helpers (snapshot serializers remain)
- `ssr/explorer/collection_input.py` shim

## [0.14.9] — 2026-06-26

**MCP Operator release** — `palm-mcp` adapter for coding agents: 26 tools, 4 prompts, 10 resources; stdio + native HTTP transports; agent-oriented docs.

Guide: [docs/MCP.md](docs/MCP.md) · Agent context: [docs/llms.txt](docs/llms.txt) (`palm://agent/guide`)

### Added

- **`palm-mcp` stdio server** — FastMCP adapter proxying to Palm REST (`PALM_BASE_URL`); install via `pip install "palmengine[mcp]"` or `uv sync --extra mcp`
- **26 MCP tools** — operator loop (`palm_inspect_instance`, `palm_wizard_input`, `palm_resume_child_wait`, …), lifecycle (`palm_submit_wizard`, `palm_cancel_job`, `palm_invoke_resource`, …), debug (`palm_doctor`, `palm_trace_events`, `palm_validate_flow`, …)
- **10 MCP resources** — `palm://agent/guide`, `palm://definitions/*`, `palm://instances/{id}/tree`, `palm://openapi`, `palm://server/health`
- **4 MCP prompts** — `debug-wizard-block`, `drive-wizard-to-step`, `explain-compositional-stack`, `operator-handoff`
- **Pattern MCP contributors** — `register_mcp_contributor()` in `palm/patterns/_registry.py`; wizard (`palm_wizard_collection_action`, `palm_wizard_commit_preview`), parallel (`palm_parallel_branch_status`), pipeline (`palm_pipeline_step_trace`)
- **App MCP contributors** — `register_app_mcp_contributor()` in `palm/app/mcp_registry.py` for downstream apps
- **Native HTTP MCP** — streamable HTTP at `POST /mcp` and SSE at `/mcp/sse` + `/mcp/messages` when `mcp` extra installed; discovery via `GET /v1/surfaces/mcp`
- **REST endpoints for MCP** — `POST /v1/wizards/{id}/resume-child-wait`, `resume-wizard-tick`; `GET /v1/instances/{id}/tree`; `POST /v1/jobs/{id}/cancel`; `POST /v1/flows/validate`; `GET /v1/doctor`; resource catalog `GET /v1/resources`, `GET /v1/resources/{ref}`
- **`palm/common/operator/`** — `compact_wizard_inspect()`, `compact_job_inspect()`, `build_invoke_tree()`, `resolve_mcp_wizard_input()` (plain-string coercion), `enrich_job_list_rows()`, `slim_waiting_job_row()`, `build_doctor_report()`, snapshot diff helpers
- **`palm_invoke_resource`, `palm_compose_status`** — resource invoke and compositional session summary tools
- **Grok project config** — [`.grok/config.toml`](.grok/config.toml) registers `palm-mcp` stdio for this repo
- **Just recipes** — `just mcp-sync`, `just mcp-inspector`
- **Tests** — `tests/test_mcp_tools.py`, `test_mcp_phase3.py`, `test_mcp_phase4.py`, `test_mcp_phase5.py`, `test_mcp_http_surface.py`, `test_mcp_registry.py`, `test_operator_waiting_jobs.py`, `test_server_list_jobs_enrichment.py`
- **Documentation** — [docs/MCP.md](docs/MCP.md) agent development guide; MCP sections in README, DEVELOPMENT, AGENTS, STATUS, `docs/llms.txt`

### Changed

- **MCP module split** — `src/palm/runtimes/mcp/tools.py`, `resources.py` extracted from monolithic `server.py`
- **Plain-string wizard input** — `palm_wizard_input` and `palm_provide_job_input` prefer `input="yes"` over JSON `value`; coercion matches Explorer forms
- **`GET /v1/flows`** — list includes `step_slugs` for wizard flows; `GET /v1/flows/{id}?verbose=0` returns slim summary
- **`GET /v1/jobs`** — enriches rows with `instance_id`, `pattern`, `flow`, `step` from metadata and instance manager
- **`palm_list_waiting`** — never aliases `job_id` as `instance_id`; omits `instance_id` when unknown

### Developer notes

- **Agent conventions:** instance-first (`instance_id`); plain `input` strings; resources = read, tools = write; `palm_resume_child_wait` when `waiting_for_child`
- **Operator loop:** definitions → submit → inspect → input → wait on children → resume
- **Prerequisite:** `palm server` on `:8080` before connecting MCP stdio
- **MCP Inspector:** `just mcp-inspector` for interactive tool testing

## [0.13.13] — 2026-06-25

**Provider apps + compositional follow-ups** — PatternApp alignment, ProviderApp framework, remote resource invoke, REST HTTP bindings.

### Added

- **[docs/PATTERN-APPS.md](docs/PATTERN-APPS.md)** — canonical guide for PatternApp manifests, `bindings/`/`flow/` layout, and `palm.common` boundaries
- **[docs/PROVIDER-APPS.md](docs/PROVIDER-APPS.md)** — canonical guide for ProviderApp manifests and provider `bindings/`/`flow/` layout
- **ADR-002** — [docs/adr/002-pattern-apps-and-common-boundaries.md](docs/adr/002-pattern-apps-and-common-boundaries.md)
- **ADR-003** — [docs/adr/003-provider-apps.md](docs/adr/003-provider-apps.md)
- **`ProviderApp`** — Django-style manifest base in `palm/common/providers/app.py`; `providers/_registry.py` for app lifecycle, runtime binding, and runtime accessor hooks
- **`POST /v1/resources/invoke`** — REST endpoint for remote resource invocation (compositional palm provider remote mode)
- **`register_runtime_accessor`** — decouples `child_wait` and wizard bridges from palm-specific wiring imports
- **`tests/test_provider_boundary.py`** — AST enforcement for provider imports in `palm.common` and `palm.patterns`
- **`just guard-common`** — runs `test_common_boundary.py`, `test_provider_boundary.py`, and `test_modular_apps.py` (wired into `just check`)

### Changed

- **parallel** — reorganized into `bindings/` (definitions, instances, context, behavior_tree) and `flow/` (branch, scope, merge); `ParallelApp` manifest documents `palm_layers`
- **pipeline** — `bindings/definitions` + `bindings/behavior_tree`; enhanced `PipelineApp` manifest
- **dag, etl** — `bindings/definitions/builder.py` + `flow/` scaffold; honest `PatternApp` manifests
- **palm provider** — reorganized into `bindings/` (resource, orchestration, runtimes, recursion) and `flow/` (coordinator, params, target, remote); `PalmProviderApp` manifest; remote `invoke_resource` via `/v1/resources/invoke`
- **rest provider** — `bindings/resource` + `bindings/transport` with real HTTP fetch (stub fallback when `base_url` absent)
- **graphql, postgres** — minimal `ProviderApp` manifests
- **Documentation** — AGENTS, ARCHITECTURE, STATUS, `docs/index.html`, `docs/llms.txt` updated for PatternApp and ProviderApp models; stale path bans in `scripts/docs_check.py`

## [0.13.0] — 2026-06-18

**Wizard Experience release** — first-class `/v1/wizards` REST surface, HTMX-powered Explorer workspace, and rich collection-step UI.

Vision: [docs/vision/closed/VISION-0.13.md](docs/vision/closed/VISION-0.13.md) · Guide: [EXPLORER-WIZARD.md](docs/wiki/guides/explorer-wizard.md) · Phases: [src/palm/patterns/wizard/MIGRATION-WIZARD-PHASES.md](src/palm/patterns/wizard/MIGRATION-WIZARD-PHASES.md)

### Added

- **`/v1/wizards` REST API** — `POST` submit, `GET` rich status, `POST` input, `POST` backtrack keyed by durable `instance_id`
- **`build_wizard_view()`** — instance-centric read model combining projections, job inspection, prompt, answers, and `next_actions`
- **CQRS** — `SubmitWizardCommand`, `ProvideWizardInputCommand`, `RequestWizardBacktrackCommand`, `GetWizardStatusQuery`
- **Palm Explorer wizard workspace** — HTMX partial updates at `/explorer/instances/{id}` with progress bar, prompt card, answers panel, step timeline, and backtrack controls
- **Collection step UI** — overview card, numbered item cards, add/edit/remove flows, field-phase draft panel, remove confirmation dialog
- **`collection_input.py`** — maps Explorer form actions to wizard `provide_input` values (including compound edit/remove)
- **Extended job inspection** — collection phase metadata (`collection_draft`, `collection_progress`, `item_fields`, …) flows into wizard `prompt`
- **Guide** — [EXPLORER-WIZARD.md](docs/wiki/guides/explorer-wizard.md) for operators and integrators
- **Tests** — `tests/test_server_wizards.py`, Explorer wizard + collection HTMX coverage in `tests/test_server_ssr.py`

### Changed

- **Wizard phase modularization** — collection, input, summary, commit, resource, and transform phases live under `palm/patterns/wizard/phases/` with BT routing (`PhaseKeyedSelectorNode`, `PhaseTransitionLoopNode`)
- **`WizardPattern`** — slim orchestration surface; step logic owned by phase nodes
- **OpenAPI / `/v1/docs`** — wizard request examples for collection menu, field input, and continue actions
- **Documentation** — README “Try in Explorer”, ARCHITECTURE wizard Explorer section, `docs/index.html` and `docs/llms.txt` refreshed for 0.13

### Developer notes

- Explorer collection UI posts `collection_action` (+ optional `item_index`) to `/explorer/instances/{id}/input`; REST clients use `/v1/wizards/{id}/input` with wizard menu strings (`"Add a new item"`, etc.)
- HTMX targets `#wizard-workspace` with `outerHTML` swap; forms disable controls during flight via `hx-disabled-elt`

## [0.12.9] — 2026-06-17

**Compositional Power release** — Resources as first-class, declarative citizens; Palm calling Palm via the `palm` provider; Explorer resource hub.

Vision: [docs/vision/closed/VISION-0.12.md](docs/vision/closed/VISION-0.12.md) · Migration: [MIGRATION-0.12.md](docs/migrations/MIGRATION-0.12.md) · ADR: [docs/adr/001-compositional-power-resources.md](docs/adr/001-compositional-power-resources.md)

### Added (Phase 1)

- **`ResourceDefinition`** — declarative resource contracts in `palm/definitions/resource.py`
- **`DefinitionRepository` resource CRUD** — register, save, get, list, delete with storage roundtrip
- **Bootstrap hydration** — resources loaded from storage alongside flows and processes
- **CLI** — `resource list`, `resource describe <ref>`; `palm doctor` and `process list` catalog show resources
- **Example** — `examples/definitions/fetch_customer.py`

### Added (Phase 2)

- **`ProviderResult`** — structured invoke outcomes (`success`, `data`, `error`, `metadata`)
- **`BaseProvider.invoke()`** — action-based contract; `describe()` and `health()` metadata
- **`ResourceEngine.invoke()`** — definition ref or direct provider; `{{ state.* }}` and `{param}` binding
- **Events** — `resource.invoked`, `resource.completed`, `resource.failed` via injected `EventEngine`
- **`palm/common/resource/`** — `resource_definition_resolver()` bridge (core purity preserved)
- **`PalmApp.invoke_resource()`** / **`ApplicationHost.invoke_resource()`**
- **CLI** — `resource invoke <ref> key=value ...` and direct `--provider` mode
- **Integration** — `WizardActionLeaf`, `enrich_resource` transform use engine invoke path

### Added (Phase 3)

- **`ResourceLeaf`** — core BT leaf invoking `ResourceEngine` with trace + output keys
- **`WizardResourceLeaf`** — wizard `step_kind: resource` with answer promotion for state binding
- **Wizard config** — `resource_ref`, `params`, `output_key`, `action` on resource steps
- **Example flow** — `resource-customer-wizard` (input + `fetch-customer` resource step)
- **Events** — `wizard.resource.invoked`

### Added (Phase 4)

- **`palm` provider** — built-in compositional orchestration at `palm/providers/palm/`
- **Local mode** — `submit_flow`, `submit_process`, `invoke_resource`, `fetch` via bound runtime
- **Remote mode** — HTTP delegation to `ServerRuntime` (`POST /v1/jobs`, plans API for processes)
- **Recursion guardrails** — configurable depth limit and cycle detection via `contextvars`
- **Correlation metadata** — child jobs carry `__palm:parent_job_id`, `__palm:invoke_depth`, `__palm:invoke_chain`
- **Runtime wiring** — `BaseRuntime.start()` binds local runtime for in-process `palm` calls
- **Example** — `compositional-parent` wizard calling `ingest-etl` via `submit-ingest-etl` resource

### Changed (Phase B — resource cleanup)

- **Breaking:** removed wizard `step_kind: action` and `WizardActionLeaf`
- **Breaking:** resource steps require `resource_ref` (`resource_provider` / `resource_id` removed)
- Removed `resource_leaf_from_legacy_action()` compatibility helper
- **`ResourceLeaf`** — richer failure messages and trace (`resource_ref`, `action`, correlation fields)
- **`promote_binding_keys()`** — shared wizard answer promotion for param binding
- **Events** — `resource.completed` / `resource.failed` include correlation payload; dropped `wizard.resource.invoked`

See [MIGRATION-0.12.md](docs/migrations/MIGRATION-0.12.md).

### Added (Phase C — future-proofing)

- **`palm/core/utils/recursion.py`** — reusable `recursion_frame()` depth/cycle guard
- **`ResourceCatalog`** — rich discovery (`describe`, provider actions, schemas)
- **Explorer** — `/explorer/resources` catalog and detail pages
- **`ResourceEngine` caching** — optional definition + read-result TTL caches (`PALM_RESOURCE_CACHE_*`)
- **`DefinitionRepository.find_resources()`** / `list_resources_by_provider()`
- **Examples** — expanded compositional demo (nesting + remote URL pattern)

### Added (Phase 5 — cross-cutting integration)

- **Compensation** — `register_for_resource()` undo handlers; `CompensationCoordinator` triggers on `resource.failed` and commit failure with tracked mutating invokes
- **`resource.compensated`** observability event when resource undo succeeds
- **`ResourceInvocationProjection`** — per-instance/job resource call timeline (`GetResourceInvocationsQuery`)
- **Explorer** — resource step timeline on instance detail pages
- **Wizard** — mutating invoke tracking (`RESOURCE_INVOCATIONS`); enriched `RESOURCE_FEEDBACK`
- **`enrich_resource`** — full `resource_ref` support with custom `action`, `params`, and state binding
- **Observability** — `JobExecutionContextHook` stamps execution correlation; `resource.*` events include job/instance/wizard/step metadata
- **`palm/core/resource/observability.py`** — core-safe correlation helpers

### Added (Phase 6 — release polish)

- **Explorer resources hub** — `/explorer/resources` catalog (filters, usage counts, invoke shortcuts); detail pages with action catalog, flow cross-refs, invocation timeline; **Try Invoke** form at `/explorer/resources/{id}/invoke`
- **Explorer integration** — resource steps on flow detail; resource invocations on job detail; overview stat + link card
- **Documentation** — `MIGRATION-0.12.md`, Resource Best Practices in README and ARCHITECTURE; `RELEASE-0.12.9.md` checklist
- **Quality** — `just docs-check` version surfaces; full test suite green at 0.12.9

## [0.11.8] — 2026-06-17

**Explorer polish release** — Palm Explorer becomes the living server hub; legacy wiki/docs paths redirect; flow submission UX refined.

### Added

- **Palm Explorer** — schema-driven SSR hub at `/explorer` for flows, jobs, instances, schemas, patterns, and processes
- **Explorer surface** — `ExplorerSurface` (`explorer`); `/v1/surfaces/explorer` and `/v1/surfaces/ssr` surface info endpoints
- **Flow submission UX** — registered-flow primary form, advanced test-wizard panel, **Start this flow** buttons, `?flow=` pre-fill on submit page
- **Instance browser** — browse and inspect durable process instances and snapshots from the hub
- **Root redirect** — `GET /` → `/explorer` (302); health payload includes `home`

### Changed

- **SSR layering** — `palm/common/runtimes/server/ssr/` stays thin (render + layout shell); Explorer implementation lives in `palm/runtimes/server/surfaces/ssr/explorer/`
- **Legacy paths** — `/wiki/*` and `/docs` redirect to `/explorer`; health keeps `wiki: "/explorer"` as deprecated alias
- **REST docs hub** — links to Palm Explorer alongside `/v1/docs` and OpenAPI

### Fixed

- **Explorer forms** — choice fields tolerate `choices: null` without crashing (`_normalize_choices`)

## [0.10.9] — 2026-06-16

**Architecture evolution release** — ApplicationHost becomes the primary orchestrator, CQRS read models power the CLI, and reliability primitives (outbox, compensation) ship for production-style deployments.

### Added

- **ApplicationHost** — top-level orchestrator with composable role profiles (`all_in_one`, `master`, `worker`, `server`), startup recovery, and coordinated shutdown
- **CQRS layer** (`palm.common.cqrs`) — `CommandBus` / `QueryBus`, handlers for submit/resume/input, and three projections:
  - `InstanceIndexProjection` — instance catalog read model
  - `WizardProgressProjection` — wizard step, backtrack trace, commit status
  - `JobStatusBoardProjection` — live job board for dashboards
- **Reliability** — transactional event outbox (`OutboxStore`, background drain), `CompensationCoordinator` for commit-failure undo, optional `WebhookDispatcher`
- **Projection rebuild safeguards** — configurable batch size, max instances, `skip_if_fresh` policy on startup
- **Status dashboard** — projection-backed Rich overview (`palm status` default):
  - Host health (roles, runtimes, outbox, recovery)
  - Instance counts, active wizards, job board, recent host events
  - `--full` detailed view, `-r` / `--refresh` live refresh in REPL/TTY
- **`palm host`** subcommand — blocking deployment roles via `run_host()` (`all-in-one`, `master`, `worker`, `server`)
- **`HostEventRecorder`** — ring buffer of recent host bus events for dashboards
- **CLI consolidation** — unified diagnostics routing (`status` / `doctor`), shared `instance resume`, backward-compatible aliases documented in help
- **Test performance** — `PalmSettings.for_tests()`, shared fixtures, `--fast` pytest mode, collapsed-runtime worker-ready fix (~33× faster suite)
- **Migration guide** — [MIGRATION-0.10.md](docs/migrations/MIGRATION-0.10.md)

### Changed

- **CLI bootstrap** — `create_cli_host()` + `ApplicationHost` replace direct `PalmApp` wiring; collapsed profile runtime name `main`
- **`palm status`** — live dashboard by default; `status --full` is detailed dashboard; use `palm doctor` for full health report
- **`palm doctor`** — supports `--dashboard` (and `--full` / `-r` when combined with dashboard flags in REPL)
- **Worker coordination** — collapsed `all_in_one` hosts register embedded runtime as worker (no 5s startup timeout)
- **`examples/full_demo.py`** — rewritten for `ApplicationHost` + CQRS + resume across restart
- **Documentation** — README, ARCHITECTURE, DEVELOPMENT, examples README refreshed for 0.10 primary paths

### Removed

- **`PalmApp.bootstrap_cli()`** — use `ApplicationHost` / `create_cli_host()`
- **`CLI_RUNTIME_NAME`** constant
- **`palm/runtimes/cli/pkg/`** re-export shim

### Deprecated

- **`create_cli_app()`** — use `create_cli_host()`; returns `host.app` for legacy callers
- **Wizard-only CLI shortcuts** — `wizard start` / `wizard status` remain but `flow start` / `status` are preferred

### Fixed

- **Collapsed host startup** — `WorkerCoordinator` counts embedded runtime in `all_in_one` profile (eliminates spurious worker-ready timeout)
- **`palm host all-in-one`** — `HostProfile` import available at module level (fixes `NameError` on one-shot host command)

### Upgrade notes (0.9.x → 0.10.9)

| Before (0.9) | After (0.10.9) |
|--------------|----------------|
| `PalmApp.bootstrap_cli()` | `create_cli_host()` or `ApplicationHost(...).start()` |
| `app.submit_flow(...)` in services | `host.submit_flow(...)` or `host.execute(SubmitFlowCommand(...))` |
| `app.list_instances()` in CLI | `host.list_instance_views()` / query bus |
| `status --full` = doctor | `status --full` = detailed dashboard; `doctor` = health report |

See [MIGRATION-0.10.md](docs/migrations/MIGRATION-0.10.md) for full migration steps.

## [0.9.7] — 2026-06-15

**Transform release** — declarative data shaping from core engine to wizard steps, plus security and reliability polish to close the 0.9 line.

### Added

- **TransformEngine** (`palm.core.transform`) — pure core engine with `TransformContext`, batch/chained pipelines, and scoped `BaseState` reads/writes with optional schema validation
- **Built-in transform rules** (`palm.common.transforms`) — **22 registered rules** with catalog descriptions for docs and `palm doctor`:
  - Field shaping: `rename_field`, `map_fields`, `filter_items`, `lookup`, `conditional`, `jsonpath_extract`, `jsonpath_set`, `calculate`, `string_format`
  - Dates: `date_format`, `date_parse`
  - Integration: `enrich_resource`, `callable`
  - Serialization: `json_load`/`json_dump`, `csv_load`/`csv_dump`, `yaml_load`/`yaml_dump`, `toml_load`, `xml_load`, `parquet_load` (stub for custom pyarrow rules)
- **Registration helpers** — `register_transform()`, `@transform_rule`, `TransformExecutor`, `apply_transform_to_state()`, autoload at bootstrap
- **Wizard `step_kind: transform`** — declarative transform steps between interactive prompts; promotes output to answers for summary and flow-schema validation; CLI shows `Applied transform: …`
- **TransformLeaf** — behavior-tree leaf for programmatic transform chains inside wizard trees
- **Examples** — `transform-example` (wizard transform steps), `transform-shaping` (calculate / lookup / conditional pipeline), `transform-formats` (json → csv ETL-style demo)
- **`palm doctor`** — transform registry table with per-rule catalog descriptions

### Changed

- **Documentation** — README, ARCHITECTURE, examples, and website refreshed for transforms and 0.9.7 capabilities
- **Dev dependencies** — pytest bumped to 9.x (addresses CVE-2025-71176) with compatible pytest-asyncio
- **Version** — release line advances to **0.9.7**

### Fixed

- **Filesystem storage path traversal** — `FilesystemStorageBackend` rejects `..` segments, path separators, and any resolved path outside `data_dir`; prevents writes outside the storage root (e.g. keys like `palm:..:outside`)
- **InstanceManager active slot leak** — `acquire()` marks an instance active only after a successful load; failed lookups no longer consume active slots
- **DictStateSchema length constraints** — validates `minLength`/`maxLength` on strings and `minItems`/`maxItems` on arrays
- **`guard_core.py` Windows console** — success message uses plain `[OK]` instead of a Unicode checkmark

## [0.8.15] — 2026-06-12

Polished release — dynamic list wizards, parallel branches, and friendlier CLI choice UX on top of the state schema foundation.

### Added

- **Collection step kind** (`step_kind: collection`) — repeatable structured items with add, edit, remove, and done; per-item scopes (`item-N:field`), draft state, and resume-friendly session keys
- **Collection item selection** — compact edit/remove flow: pick by number, partial label search, or `cancel`; configurable `label_field` for any collection flow
- **Choice input resolution** — wizard and collection choice fields accept 1-based index, exact value, case-insensitive match, and unique partial match; canonical values stored in answers
- **Parallel pattern** (`parallel-demo`) — concurrent wizard branches with isolated scopes, per-branch snapshots, merge strategies, and CLI branch progress (`@parallel:<branch>`)
- **Examples** — `todo-builder` (collection + schemas), `parallel-demo`; `flow start` as the recommended entry point
- **Tests** — collection steps, item selection, choice resolution, parallel branch resume, CLI E2E for `todo-builder` and `schema-onboard`

### Changed

- **CLI display** — numbered option lists for choices and collection menus; compact item previews during edit/remove selection
- **Collection menu** — main menu stays small (add / edit / remove / continue) even with many items; current list shown as a numbered summary
- **Documentation** — README, ARCHITECTURE, DEVELOPMENT, examples guide, and website refreshed for 0.8.15
- **Version** — release line advances to **0.8.15**

### Fixed

- **Union-type schemas** — `DictStateSchema` validates `type: ["string", "null"]` and similar unions without crashing
- **Optional collection fields** — empty CLI input skips optional fields; regex rules treat `None` as empty
- **Scope stack** — collection field editing avoids duplicate scope frames on resume

## [0.8.8] — 2026-06-12

State schema and scoping release — layered validation, durable scope resume, and CLI polish.

### Added

- **State schemas** (`palm.core.context.state_schema`) — lightweight JSON Schema-inspired validation (`DictStateSchema`) with no external dependencies; supports `type`, `enum`, `minimum`/`maximum`, nested `object`/`array`, and `default`
- **Scoped state** (`BaseState`) — `enter_scope` / `exit_scope`, per-scope values (`set_scoped` / `get_scoped`), per-scope schemas (`bind_scope_schema`), and `effective_schema()` (innermost wins)
- **Flow-level schemas** — `state_schema` / `state_schema_ref` on `FlowDefinition`; materialized at submission via `palm.common.state.schema_binding`
- **Wizard layered validation** — built-in field rules → declarative rules → per-step schema → flow schema; `coerce_step_input` converts CLI string input to schema types (e.g. `"27"` → `27`)
- **Wizard step scopes** — each input step enters a named scope; prompt bundles expose `scope_stack`, `current_scope`, `scope_depth`
- **Schema-aware snapshots** — `__palm:meta` in `snapshot_state()` preserves `scope_stack`, `scope_schemas`, and `effective_schema`; `state_from_snapshot()` restores full scope context for resume
- **State observability** (`palm.common.state`) — opt-in `EventEngineStateObserver` for scope and schema events; value events off by default to avoid tick noise
- **`schema-onboard` example** — flow + per-step schemas demonstrating layered validation and resume
- **CLI context display** — wizard panels, `status`, and REPL prompt show scope and validation feedback when present
- **`palm doctor`** — flow catalog indicates which definitions declare state schemas

### Changed

- **Wizard validation** — failed schema checks keep the user on the current step with formatted, actionable messages
- **Documentation** — `ARCHITECTURE.md`, `DEVELOPMENT.md`, and `examples/README.md` updated for schema/scoping workflows
- **Version** — release line advances to **0.8.8**

### Tests

- `tests/core/test_state_scoping.py`, `tests/test_state_phase3.py`, `tests/test_state_snapshots.py`, `tests/test_state_observability.py`
- `tests/test_wizard_schema.py`, `tests/test_wizard_schemas_layered.py`

## [0.7.4] — 2026-06-10

Distribution and adoption improvements — no breaking API changes.

### Changed

- **PyPI package renamed to `palmengine`** — install with `pip install palmengine[cli]`; Python import remains `import palm`; CLI command remains `palm`
- **Packaging** — `just build`, `just publish-test`, `just publish`, `just install-local`, `just release-prep`; GitHub Actions publish workflow
- **Documentation** — README installation section, DEVELOPMENT release guide, install commands updated across docs

## [0.7.0] — 2026-06-10

Production-ready persistence foundation, storage factory, and instance lifecycle coordination.

### Changed (architectural boundaries)

- **Wizard logic removed from `palm.common`** — instance field extraction, resume restoration, and submission metadata now live in `palm.patterns.wizard.persistence` and `palm.patterns.wizard.submission`, registered via `palm.patterns._registry`
- **`PatternBuildContext` slimmed** — no wizard metadata or default commit/validation registry resolution; wizard builder owns its defaults
- **Generic persistence preserved** — `snapshot_state`, `state_from_snapshot`, `build_instance_from_job`, `update_instance_from_job`, `prepare_resume_state` remain in `palm.common.persistence.instance_sync` and delegate to pattern hooks

### Added (CLI usability)

- **Global CLI flags** — `-b`/`-d`, `--config`, `-S`/`--enable-state-snapshot`, `--max-loaded-instances`, `--max-concurrent-active`, `--scheduler`, `--format` (`table`|`json`); merged via `settings_from_invocation()` with documented env precedence
- **REPL auto-completion** — context-aware suggestions for commands, wizard/process names, and instance ids (active by default; `--all` for terminal); snapshot command scoped to instances with snapshots
- **Instance workflows** — `instance list` filters (`--all`, `--status`, `--flow`, `--limit`), `instance prune [--dry-run]`, richer tables (status emoji, short + full ids), JSON output for scripting
- **`palm doctor`** — persistence mode panel and active (non-terminal) instance summary

### Added (continued)

- **`InstanceManager`** (`palm.common.managers`) — LRU cache, active-instance tracking, lightweight summaries, startup reconciliation, and thread-safe coordination over `InstanceRepository`
- **`BaseManager`** — minimal `initialize` / `shutdown` lifecycle contract for managers
- **`InstanceSummary`** — fast listing view for CLI `instance list` without full payload loads
- **Instance settings** — `max_loaded_instances`, `max_concurrent_active`, `reconcile_instances_on_startup` on `PalmSettings`
- **Manager tests** — `tests/test_instance_manager.py`

### Changed (continued)

- **CLI bootstrap** — thin `PalmApp` client; `resolve_cli_settings()` respects `PALM_*` env unless flags are explicit; persistence banner in REPL/doctor
- **CLI instance resolution** — `instance list` shows full ids; prefix/name resolution shared across `status`, `snapshots`, and `resume`; all commands use `instance_manager`
- **`PalmApp`** — shared `instance_manager` property; instance APIs route through the manager
- **`BaseRuntime`** — wires hooks and executor through `InstanceManager`; shared manager across app runtimes
- **CLI** — `instance list`, `doctor`, and snapshot commands use the manager layer

### Added

- **`FilesystemStorageBackend`** — production filesystem persistence with atomic writes (temp file + rename), JSON serialization, namespace key paths (`palm:instances:*` → nested `.json` files), thread-safe operations, and v0.6 flat-file read compatibility
- **`StorageFactory`** (`palm.common.storage`) — lazy backend registration, `PalmSettings`-driven `backend_options`, and `initialize_engine()` / `select()` helpers
- **Storage exceptions** — `StoragePermissionError`, `StorageCorruptionError` in `palm.core.exceptions`
- **Optional storage extras** — `postgres` and `mongodb` uv extras for lazy-loaded backends
- **Filesystem tests** — `tests/test_filesystem_storage.py` (unit + repository + `PalmApp` integration)

### Changed

- **`BaseRuntime.start()`** — initializes shared `StorageEngine` via `StorageFactory` (respects `backend_options` from `PalmSettings.data_dir`)
- **`runtime_start_options()`** — forwards filesystem `data_dir` through `backend_options`
- **Repository list methods** — skip missing or corrupted index entries instead of failing entire listings
- **Storage autoload** — core backends (`memory`, `filesystem`) register at import; `postgres` / `mongodb` load lazily on first use
- **`FilesystemBackend`** — alias retained; canonical class is `FilesystemStorageBackend`

### Configuration

```bash
export PALM_STORAGE_BACKEND=filesystem
export PALM_DATA_DIR=./data   # optional; defaults to ./data
```

## [0.6.0] — 2026-06-07

Major orchestration maturation release: authoritative lifecycle, layered runtimes, execution plans, and production-oriented server/daemon surfaces.

### Added

- **`palm.app` layer** — `PalmApp`, `PalmSettings`, multi-runtime registry, shared storage, definition bootstrap
- **`palm.common` package** — shared coordination split into `executions/`, `plans/`, `hooks/`, `persistence/`, `patterns/`
- **Django-style extensible apps** — `patterns/`, `providers/`, `storages/` restructured as self-contained subpackages with per-app `registry.py` and `INSTALLED_*` autoload lists
- **Pattern builder registry** — each pattern app registers its own `builder.py`; `common/patterns/builder.py` dispatches generically
- **Lifecycle authority** — `RunResult` + `OrchestrationEngine.apply_result()` as sole job transition path
- **Scheduling model** — `JobScheduler` (inline/queued) composes with `JobRunner`; shared `drive_job` primitive
- **Middleware** — `JobHook` protocol with drive-phase hooks (`on_before_drive`, `on_after_drive`); `AuthMiddleware`, `DriveObservabilityHook`, `InstancePersistenceHook`
- **State snapshots** — optional `StateSnapshotHook` captures `BlackboardState` at configurable job status transitions; stored as bounded `state_snapshots[]` ring buffer on `ProcessInstance`; configured via `PalmSettings` (`enable_state_snapshot`, `snapshot_on_status`, `max_snapshots_per_instance`); CLI `palm instance snapshots <id>`; `PalmApp.list_instance_snapshots()`
- **Thread-safe registries** — `Registry`, pattern builder map, `CommitRegistry`, `PlanRegistry`, and `RuntimeRegistry` use `threading.RLock`; idempotent re-registration; concurrency tests in `tests/test_core_registry.py`
- **Executions handoff** — `ExecutionPlan`, `ProcessPlan`, `prepare_*_plan`, `submit_plan(s)`, `PlanRegistry` for deferred submission
- **Runtimes** — `RuntimeHost` protocol, `BaseRuntime` shared wiring, `DaemonRuntime`, `ServerRuntime` (stdlib HTTP API)
- **Auth** — `AuthEngine` wired on runtimes; `auth_enforce`, per-request `X-Palm-Subject` on server
- **Server API** — `POST /v1/plans/prepare`, `POST /v1/plans/submit`, job input/status endpoints
- **Migration guide** — [MIGRATION-0.6.md](docs/migrations/MIGRATION-0.6.md)

### Changed

- **Package layout** — coordination logic moved from monolithic `palm.executions` to structured `palm.common`
- **EmbeddedRuntime** slimmed to policy wrapper over `BaseRuntime`
- **DefinitionExecutor** uses plan-based submission internally
- CLI storage flag renamed to `--storage-backend`
- Test double renamed: `TestBackend` → `TestRunner`
- Orchestration initialization uses `scheduler=` (not `mode=`)

### Removed

- **`palm.executions` package** — use `palm.common` and subpackages (`common.plans`, `common.hooks`, etc.)
- **`palm.patterns.wizard.commit`** — use `palm.patterns.wizard.handler`
- `ExecutionBackend` alias (use `JobRunner`)
- `BehaviorTreeBackend` alias (use `BehaviorTreeRunner`)
- `EmbeddedMode` (use `InlineScheduler`)
- `wire_instance_persistence()` (automatic hook registration)
- `ProcessExecutor` alias (use `DefinitionExecutor`)
- Deprecated `backend=` parameters on schedulers and runtime runner resolution

## [0.5.0-dev] — 2026-06-05

Milestone toward **0.5.0**: a production-oriented developer experience on top of the 0.4.0 architecture rebuild.

### Added

- **Executions layer** (`palm.executions`) — `DefinitionExecutor`, `DefinitionRepository`, pattern builder, and instance sync outside core
- **Persistent process instances** (`palm.instances`) — durable snapshots with status history; resume across runtime restarts when storage is shared
- **Pluggable state** — `BlackboardState` and orchestration job state decoupled from engine internals
- **Transactional wizards** — declarative validation, summary/commit steps, named commit handlers, resource action steps, backtracking
- **Modern CLI** (`palm.runtimes.cli_pkg`) — Rich output, REPL, `process` / `instance` / `wizard` commands, `input` / `back` / `status`
- **`palm doctor`** and **`palm status --full`** — engine health, registries, definition catalog, recent instances
- **`palm version --full`** — build and plugin matrix without starting a job
- **Example definitions** — onboarding, data ingestion, approval workflow, quick wizard under `examples/definitions/`
- **`examples/full_demo.py`** — end-to-end script: register → submit → input → commit → simulated restart → resume
- **Documentation** — README quick start, ARCHITECTURE.md, DEVELOPMENT.md, examples guide
- **`just` recipes** — `palm-doctor`, `palm-repl`, demos, `demo-full`, release-oriented `prepr`

### Changed

- **EmbeddedRuntime** high-level API — `submit_flow`, `submit_process`, `provide_input`, `resume_process`, `get_instance`
- CLI entry point rebuilt; legacy REPL command aliases retained during transition
- Version series opens at **0.5.0-dev** (supersedes 0.4.0-dev tracking)

### Architecture (carried from 0.4.0)

- Pure **core** layer with registry-based extension
- Patterns: wizard, DAG, ETL; providers: REST, GraphQL, Postgres; storages: memory, filesystem, MongoDB, Postgres
- Legacy code quarantined under `archive/` (not imported by new code)

## [0.4.0] — 2026

### Added

- Full package restructure: `palm.core`, `palm.patterns`, `palm.providers`, `palm.storages`, `palm.definitions`
- Registry-based pattern, provider, and storage registration
- Wizard, DAG, and ETL pattern skeletons
- Embedded runtime wiring and orchestration job lifecycle
- Core purity guard and AGENTS.md constitution

### Removed

- Monolithic pre-0.4.0 layout (preserved in `archive/` for reference)

## [0.3.x and earlier]

See `archive/` for legacy CLI, wizards, and behavior-tree implementations.