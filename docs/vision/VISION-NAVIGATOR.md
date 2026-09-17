# VISION — Navigator (operator-guidance definition · presentation adapter)

**Status:** 📋 **Law seed** for open theme [**0.69** Navigator](VISION-0.69.md) (José opened **2026-09-17**). Named **2026-08-19**.  
**Locks (José 2026-09-15–16):** guidance instance stays as **home**; entry and visibility are **principal / user-plane**, not this invert. Kit **`palm.kits.present`** (**kit-as-composition:** one object holds `BoundSurface` and walks session + execution). Surfaces stay **in-process**. First adapter: **embedded library surface** (not `EmbeddedRuntime`). **Turn invert:** kit walks; pattern fills inspect/input. **Pack:** new wizard guidance definition beside `operator_entry`; sibling start; stay waiting; return is `focus`. Session metadata: **`guidance_instance_id`**. **Walk writes** through a system interface (floor degenerate). **Job is session-ignorant.** **Dashboard model:** guidance is a staying chooser shell; spawned work is session-owned titles. **Kit-contributed settings:** present owns `guidance_definition_id`. **Stamp caller:** kit asks after attach. **Replace predicate:** kit; attached; definition id equals `guidance_definition_id`. Harvest §6.1. Theme plan: [VISION-0.69](VISION-0.69.md). ADR [037](../adr/037-navigator-invert.md) **Proposed**.  
**Language:** Law uses computer-science terms. Spoken teaching words are marked once. They are not types.  
**Map:** [PALM.md](../PALM.md) · [WRITING.md](../WRITING.md) (talk vs law)  
**Compost:** [VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md) (old Assist / CLI / Portal)  
**Session law:** [VISION-0.58](closed/VISION-0.58.md) (**closed**) · [ADR-027](../adr/027-session-plane.md)  
**Principal later:** user plane + impersonation — [ADR-027](../adr/027-session-plane.md) D8 · D11 · [TECH-DEBT.md](../../TECH-DEBT.md) later seeds  
**Doc cleanup:** [TECH-DEBT.md](../../TECH-DEBT.md) **SD-022**  
**North star:** [VISION-GROVE](VISION-GROVE.md)

---

## 1. Why this note exists

Assist captured a real need: a client that does not already know a definition id still needs a **walk** that selects work.

That need became a **product domain** (`AssistService`) and a fat surface stack (MCP operator path, CLI command forest, Portal). The idea is still right. The home is wrong.

This seed records the **intended split**. Theme plan: [VISION-0.69](VISION-0.69.md).

---

## 2. Spoken words vs law

Talk with José is analogical. Docs must not treat those words as types.

| Spoken (teaching only) | Law term |
|------------------------|----------|
| Rails / Terminal | **Presentation adapter** — kit **`palm.kits.present`**, not a product service |
| Navigator / master flow | **Operator-guidance definition** (a catalog definition) |
| Home (the instance that stays) | Session walk fact **`guidance_instance_id`**. Not a type. Not **root**. |
| Dashboard / console menu | Guidance **job**: operator-wait chooser shell. Instance stays. Not a type. |
| Home button | `focus(guidance_instance_id)` |
| Title / game | Sibling instance the **session** owns. Not a child of the guidance job. |
| Root (instance tree) | Do not use — attach list is flat; nested BT is not the home |
| Next | Continue the current run (wait plane) |
| Turn | Waiting-run inspect snapshot (`JobInspectable` / `JobContext` + wait plane). Not a Protocol type yet. |
| Invert | Move operator guidance out of a product service into definitions. **Turn invert:** kit walks; pattern registers ergonomics. |
| Palm is the tool; the product is the client | Palm is the **orchestration engine**. Applications are **clients**. |

Use the left column only to teach. Use the right column in PALM, ADRs, and architecture law.

---

## 3. Intent

**Palm** coordinates work: definition → job → instance.  
An **application** (human UI, agent, another system) is a **client** of that engine.

**Surfaces** map a protocol (HTTP, WebSocket, stdio, MCP) onto product doors. They stay thin.

A **presentation adapter** is shared support for those surfaces. Package: **`palm.kits.present`**. It does not own business rules. It:

1. Binds a session (`SessionService` / `BoundSurface`).
2. Presents the current waiting run (`JobInspectable` / wait plane). Value is **submit**, not a present field.
3. Submits input.
4. Starts work (work plane) or continues a waiting run (wait plane).
5. Changes continue **focus** among instances the session owns.

**Purpose** is not the adapter:

- The client already knows the work → it **names a definition id**.
- The client does not know → it **starts an operator-guidance definition**.

An **operator-guidance definition** is a normal flow or process in the catalog. It may list, select, and start other definitions (resource steps / Palm invoke). **Many** such definitions are allowed. None is the engine’s `main()`. `examples/definitions/operator_entry.py` is the as-built pack (ends after intent — **not** the home). The invert’s pack is a **new** wizard definition **beside** it (§5).

**Constraint (thinness):** the adapter **consumes runs**. Other operations go through **definitions and their leaves** (resource steps to Palm or to other systems). Do not grow catalog, design, or doctor as adapter verbs. Bind, focus, and continue are adapter **geometry**. They are not purpose.

**Guidance home (locked):** the operator-guidance **instance stays** on the session after it starts other work. It does not complete as a handoff. Named work is a **new instance** under the same session. The session holds **`guidance_instance_id`** (walk fact). Return is `focus` to that id. Multi-instance is the walk ([ADR-027](../adr/027-session-plane.md) D9–D10). A wizard that ends after intent is not a home. **Dashboard model (locked):** the guidance **job** is a staying chooser (operator wait, no `WaitInterest` on siblings). Spawned work is peer **titles**. The session is the process list. Thin job state (parked prompt, optional pack answers). Walk facts stay on the session.

**Birth, then delete.** Build the adapter and new surfaces **beside** Assist, the CLI forest, and Portal. Do not migrate those packages in place. Compost is [VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md).

---

## 4. Assist (as-built)

[ADR-006](../adr/006-assist-domain.md) made Assist a product domain so operator conversation had a home. Catalog flows already hold part of that home (`operator-entry`).

| As-built | Intended |
|----------|----------|
| `AssistService` + catalog + aliases | Operator-guidance **definitions** |
| Assist present / profiles | Presentation **adapter** (kit) |
| MCP `dispatch_operator_path` into every prefix | Surface calls product doors; purpose stays definitions |
| CLI command forest + dual slots | Later thin stdio adapter on the kit + `BoundSurface` (not first) |
| Portal as Assist chat (pre-session) | Later thin WebSocket adapter; session bind first (not first) |
| Embedded composition: submit/ask, no Assist | **First** kit adapter: embedded **library surface**. Engine stays `EmbeddedRuntime`. |

### As-built (2026-09-15)

No `BotService` in `src/`. Identity is Assist plus the MCP/Portal operator path stacked on it.

| Fact | Why it is this seed |
|------|---------------------|
| `AssistService.dispatch` is a second spine (list/start/inspect, instance verbs, doctor/top/vitality, discover/menu/open). | Purpose lives in a product path table, not in a **definition**. |
| Root menu and discover starters are Python lists. `inspect_catalog` returns a synthetic turn with no **job**. | Open-coded menu. Tests freeze coconut/design CTAs. |
| `palm-operator-entry` is a wizard that ends. Chat profile then auto-starts `todo-builder` / `coconut-npc` (`CHAT_AUTO_START_INTENTS`, default `auto_start=True`). | The guidance **definition** does not start the work it named. Product owns start after complete. |
| Bare `palm_assist()` → alias `operator-entry/start`. Settings `load_example_definitions` default True. | Example pack is the operator door. Floor may keep one process default. Principal doors are later (§5). |
| Coconut is the MCP card “run a flow.” | Dogfood entitled as product identity. Replace the pack; do not compost Palm to lose the NPC. |

Fat MCP catalog, CLI REPL-as-chat, Portal FAB/paint, and `session_id` on walk handles are [VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md). Empty host/docs costume is [VISION-0.68](closed/VISION-0.68.md) (**closed**). Residual [SD-023](../../TECH-DEBT.md#sd-023). Do not invert guidance as 0.68 leftover.

---

## 5. Locked (José 2026-09-15–16)

These are named. Theme [0.69](VISION-0.69.md) executes them.

| Cut | Law |
|-----|-----|
| **Guidance home** | Guidance instance stays attached. Focus leaves and returns. Product handoff after terminal is not the path. Nested BT child is optional composition, not required for the home. |
| **Dashboard model** | Guidance **job** is a chooser **shell**: operator-wait on “what next?”, spawn named work, stay parked, sit idle while focus is elsewhere. Spawned instances are **peers** (session attach list), not wait-plane targets of home. Home button is `focus(guidance_instance_id)`. Start is execution start + session-side attach; focus steals. Job state worth keeping: parked step + optional pack answers. Do not store the attach list or sibling ids on the guidance job. Real `WaitInterest` only for targets **this** job needs (e.g. a download), never for “the title you are playing.” Spoken: console dashboard / Home / title — not types. |
| **Kit-contributed settings** | Kits **extend** process config when they install. Core `PalmSettings` stays engine (storage, scheduler, snapshots, `structure_definition_id`, `session_strict_attribution`). **`palm.kits.present`** contributes **`guidance_definition_id`** (`str \| None`). Unset → no empty-handed start. Kit **reads** that fragment; empty-handed `start()` uses it. Do not flatten the key onto core `PalmSettings`. Do not overload `load_example_definitions` or `structure_definition_id`. Constructor override is later growth. Env spelling and nested-on-`PalmSettings` vs sibling kit-settings object wait for a theme. `server` host/port on core today is the same leak; move later, not this floor. |
| **Floor (degenerate principal)** | One anonymous **outside** subject. One default operator-guidance definition for empty-handed start. Definitions loaded in this process are startable. The adapter does not filter the catalog. |
| **Entry and visibility** | Not this invert’s floor. They belong to **principal policy** on the later **user plane** ([ADR-027](../adr/027-session-plane.md) D8 · D11). |
| **Fail-closed later** | If a gate is required, publish a **system interface**. Do not put the filter on the adapter, the surface, **admission**, or structure definition. This invert’s stamp uses that seam (walk writes). |
| **Not first** | Do not open the user plane to ship this invert. Do not grow `AuthEngine`’s ambient runtime principal into that plane. |
| **Kit** | **`palm.kits.present`**. Uses `SessionService` and execution present. Not a `PresentService`. Not `palm.kits.server`. |
| **Kit-as-composition** | The kit is a **library object** that holds **one** `BoundSurface` and walks existing doors: bind, present (turn invert), submit, start, **attach** (session side), focus. It composes `SessionService` + execution. Start does **not** put `session_id` on the job. Not a product service and not a dispatch table. No pattern verbs on the adapter. A pattern that wants kit ergonomics **registers** them. Phenotype: `CompositionProfile.embedded()`. Engine: `EmbeddedRuntime`. Later MCP / CLI / WS call the **same** object. Handle class name unnamed. |
| **Surface process** | First dogfood (and this invert) is **in-process**: surfaces in the same OS process as the engine. A later out-of-process surface is client scale, not a second catalog. Two clients that share one catalog and one job path share one engine process. |
| **First adapter** | **Embedded library surface**: Python in-process calls the kit. Phenotype `CompositionProfile.embedded()` (session, execution, definitions, inspect — no Assist, no HTTP/MCP/WS). **`EmbeddedRuntime` is the engine**, not the adapter. Tests and later embedders are the same client. MCP / CLI / WS are later adapters of the same kit. |
| **Turn invert** | Kit **walks**. Pattern **fills**. Present is `JobInspectable.inspect_job` → `JobContext` plus wait plane `waiting_on`. Submit is `InputCapable` when the pattern registered it. Backtrack is interactive hooks when registered. The kit does **not** switch on `pattern`. It does not call `compact_wizard_inspect` vs `compact_job_inspect` by name. Empty optional fields mean that pattern offered no such ergonomic. Wizard is the richest **fill**, not a kit branch. Do not copy Assist `question_text` / `handoff_ready` / CTA chips. `prompt` may be aliased only at the kit boundary. Protocol type names stay unnamed. |
| **Pack** | New **wizard** operator-guidance definition **beside** `examples/definitions/operator_entry.py` (not migrate in place). It starts named work as a **same-session sibling** of **any** catalog definition / pattern. The guidance instance stays `WAITING_FOR_INPUT` (no `__end__` after naming work; nested park is **not** the home). Return is `focus` of **`guidance_instance_id`**. Empty-handed start names **this** definition (kit-contributed **`guidance_definition_id`** / explicit id), not `operator-entry`. Do not copy `handoff_map`, coconut/design as product doors, Assist scenario façade, or stay-open only for `inspect-only`. Engine holes until a theme: session-side attach after start (`0.69.2`); spawn without nested park (`0.69.3`); stamp **`guidance_instance_id`** (seam `0.69.1`; kit caller `0.69.5`). |
| **Job is session-ignorant** | The job does not know the walk. Session owns **instances**; orchestration owns **jobs**. Attach is a **session** write (`SessionService` / plane after start), not `session_id` on job metadata. `SessionOwnershipHook` and inherit-or-service on the job are leftover, not floor. Continue uses owner gate + focus, not `job.metadata["session_id"]`. Park stays on the job (pattern wait). Stamp stays on the session. |
| **`guidance_instance_id`** | Session **metadata** key ([ADR-027](../adr/027-session-plane.md) D14): which attached instance is this walk’s operator-guidance run. Not a typed field on `SessionRecord` in the floor (promote later only if every session must have a guidance walk). Not `active_instance_id` (continue focus; sibling attach steals it). Not kit RAM. Not job/instance metadata. Not **root** (attach list is flat). Stamp if absent when empty-handed start — or an explicit start of the process’s guidance definition — attaches. Replace is **explicit** (change main guidance on the fly). **Replace predicate (locked):** present kit asks; instance already attached; instance **definition id equals** the kit’s **`guidance_definition_id`**. Titles cannot become Home. SessionService does not decide “is guidance.” Pack does not replace. Absent when the client named work with no guidance. Kit **reads** it and `focus`es that id. **Stamp caller (locked):** the **present kit** asks after session-side attach, if the started definition id equals its **`guidance_definition_id`**. `SessionService` writes (walk-write interface → `merge_metadata`). Attach stays geometry — it does not stamp and does not read kit settings. Pack does not stamp. Starting a second guidance definition as a title does not steal the pointer. Raw start+attach without the kit does not stamp. **Discriminator:** always-on plane geometry is a hardcoded field; optional walk roles are named session-metadata keys. |
| **Walk writes** | Session-context writes (named metadata keys, stamp/replace **`guidance_instance_id`**, later grants / impersonation / principal↔session) go through a **system interface**. `SessionService` is the product door; the interface is the gate; the plane stores. Floor: degenerate allow (owner + attached instance). User plane **installs** later. Type name unnamed. **Not** a `SessionEffects` product. **Not** `JobHookAdapter`. **Not** kit verbs. **Off the board (geometry):** attach list, `active_instance_id`, `focus`, owner **check**, execution cancel. Geometry attach is still a **session** call after start, not a job hook. As-built that should later **call** the walk-write interface: bind’s kind/origin merge, unused `merge_metadata`, `AuthMiddleware` principal on the job. Inherit-or-service on job metadata is leftover under **job is session-ignorant**. |

A process may still name which guidance definition empty-handed start uses (pack / seed). That is a **degenerate chooser**, not the law of doors.

`BoundSurface.kind` (`outside` / `service` / `host`) is how the session was born. It is not who the principal is.

---

## 6. Scout harvest (José 2026-09-16)

Harvest the **job path**, not Assist. Read-only. Do not invent a `PresentService`. Scout is closed. Execute is [VISION-0.69](VISION-0.69.md).

Unnamed contracts the harvest must close (or name as holes):

| Unnamed | Close |
|---------|--------|
| **Turn** | **Locked** (§5 turn invert). Harvest closed the keep/exclude; Protocol type still unnamed. |
| **Start sibling** | **Law locked** (§5 pack + job is session-ignorant). Glue: attach from the session after start — named hole. Do not copy `session_id` onto the child job. |
| **Park / home** | **Law locked** (§5 dashboard model): operator-wait chooser, no interest on siblings. As-built `0.69.3`: `FlowExecutionService.spawn_sibling`. Nested park leftover stays. |
| **Library door** | **Locked** (§5 kit-as-composition): the kit object holds `BoundSurface`. As-built `0.69.4`: in `INSTALLED_KITS`; `bind(host)` walks existing doors. Handle class unnamed. |
| **Empty-handed start** | **Locked** (§5 pack + kit-contributed settings): **`guidance_definition_id`** on the present kit, not core `PalmSettings`. Unset → no empty-handed start. As-built `0.69.5`: kit-owned fragment; empty-handed `start()` uses it by id. Phenotype seed stays later. |
| **Anti-requirements** | **Locked** (kit + pack refuse lists in §6.1 exclude). |

If a job-path mechanism is missing, that is a **named hole**, not a new product domain.

**Four parallel explore agents** (no `src/` edits):

| Agent | Domain | Return |
|-------|--------|--------|
| **Envelope** | Execution present, operator compact, flow wait payload. List Assist enricher leaks; do not copy them. | Candidate turn fields; exclude list |
| **Pack mechanics** | Resource leaf, Palm invoke, nested flow, attach-on-start, wizard wait / `__end__` | One as-built start-sibling + stay-home path, or hole |
| **Embedded dogfood** | `CompositionProfile.embedded()`, `EmbeddedRuntime`, test host without Assist, `SessionService`, execution submit/input | Smallest bind → start → submit → focus chain; wiring gaps |
| **Negative spine** | `AssistService.dispatch`, `inspect_catalog`, `operator_entry` handoff / auto-start, empty `palm_assist()` | Refuse list for kit and for a **new** pack (beside `operator_entry`) |

Session geometry is **not** a fifth agent. Embedded dogfood already walks bind / focus.

**After harvest:** this session merges reuse / exclude / hole. **Turn invert**, **kit-as-composition**, and **pack** locked (José 2026-09-16). Protocol + failing tests: [VISION-0.69](VISION-0.69.md) execute (`0.69.1+`).

Not in this harvest: user plane, MCP as first client, Portal/CLI compost order.

### 6.1 Harvest return (2026-09-16)

Four read-only scouts: Envelope, Pack mechanics, Embedded dogfood, Negative spine. Merge below. **Turn invert**, **kit-as-composition**, and **pack** are law (§5).

#### Reuse (job path)

| Piece | As-built |
|-------|----------|
| **Turn source** | Pattern-agnostic `JobInspectable.inspect_job` → `JobContext` → `compact_job_inspect` (and `FlowSession.context()`). Wizard also has a richer read model / `compact_wizard_inspect` (mutation, collection). Builtins are `powertool` + `verbose`. `assistant` is Assist registration. |
| **Ids** | Continue: `instance_id`. Orchestration: `job_id`. System subject: `session_id` only if `sess-…`. Definition: `flow` / `flow_id` / `flow_name`. Compact has **no** `definition_id`. |
| **Copy / choices** | `prompt` + `prompt_title`. `choices` as `list[str]`. `field_type` / `step_kind`. |
| **Wait** | `status` = `WAITING_FOR_INPUT`. `waiting_on[]` (+ compact `child`). List rows may add `waiting_on_summary`. |
| **History / verbs** | `answers` / `answers_preview`. Drive: `next_commands` (`input`, `backtrack`, `resume`, `cancel`). Slim `next_actions` **names**. Wizard `mutation` minus `agent_hint`. |
| **Submit** | `InputCapable.provide_input` via `provide_interactive_input_for_instance` (registry hooks per pattern). `FlowSession.input` / `host.provide_input`. Live **value** is submit, not a present field. Wizard and **parallel** register hooks. Pipeline / DAG do not. |
| **Bind / focus** | `SessionService.bind_surface` → `BoundSurface` (`kind` default `outside`). `attach_instance` / `focus` / `set_active_instance`. First attach steals continue focus. `BoundSurface` is a frozen snapshot; rebuild after start/submit. |
| **Attach glue** | As-built leftover: `SessionOwnershipHook` reads `session_id` from **job** metadata. Floor `0.69.2`: `SessionService.attach_after_start` after start. Job stays session-ignorant. Kit `start()` as-built `0.69.4`. |
| **Start work** | Catalog does not start. `host.submit_flow(..., session_id=)` or `execution.flows.run_wizard` with that id. Omit id → no attach, or `run_wizard` mints a **new** `sess-…`. |
| **Spawn another instance** | Floor `0.69.3`: `FlowExecutionService.spawn_sibling`. Kit `start()` as-built `0.69.4` walks that door. Leftover: resource leaf → Palm invoke → `runtime.submit_flow`. Default wait: fire-and-forget. `until_input` opens **nested park** (parent waits on child terminal). |
| **Embedded phenotype** | `ApplicationHost.for_mode("test"\|"safe")` uses `CompositionProfile.embedded()` + collapsed `EmbeddedRuntime`. Services: inspect, session, definitions, execution. No Assist, no surfaces. `PalmSettings.for_tests(load_examples=False)`. |
| **Session geometry on Assist** | Continuity **does** pass parent `sess-…` into `flows/{id}/create` — **after** parent complete. Focus door exists (`system/session/{id}/focus`). |

#### Exclude (must not enter kit or new pack)

| Kind | Do not copy |
|------|-------------|
| Assist envelope | `question` (humanize), `hint`, `handoff_ready`, `compose` / `refs`, `scenario_id`, `operator_mode`, humanized `{n,label,value}` choices, human `waiting`/`complete` status, Portal `input` schema, terminal blurbs |
| Fake turns | `inspect_catalog` (`status: "catalog"`, no job). Menu / discover / doctor / waiting-list **pages**. `format=assistant` on `shape_flow_session_view` |
| Compact leaks | Default `operator_hint` (`palm_assist` / `palm_system_doctor`). `mutation.agent_hint`. `collection_actions` MCP aliases |
| Product spine | `AssistService.dispatch` table (list/start/inspect, doctor/top/vitality, discover/menu/open, `handoff`). Auto-start / intro skip / design pre-answer. Bare `palm_assist()` → `operator-entry/start`. `AssistSession.session_id` **is** instance (SI-001) |
| Anti-pack | `operator_entry` `route_on_answer` → `__end__`. `handoff_map` / `handoff_flows`. Coconut/design as home doors. `assistant_enricher`. Assist scenario façade. Stay-open only for `inspect-only` |
| Wrong dogfood | `tests/test_session_kit_door_0_58_17.py` (`DeploymentProfile.all_in_one()`, Assist). `EmbeddedRuntime` as adapter. `palm.kits.server` as this kit |

#### Named holes (not a new product domain)

| Hole | Fact |
|------|------|
| **Start sibling** | As-built `0.69.2`: `SessionService.attach_after_start` after start — **not** inherit `session_id` onto the child job. Kit `start()` as-built `0.69.4`. |
| **Park / home** | As-built `0.69.3`: `FlowExecutionService.spawn_sibling` — stay WAITING; no interest on siblings. Leftover nested park waits **on child success**, then parent **advances**. Kit `focus` as-built `0.69.4`. Stamp home pointer as-built `0.69.5`. |
| **Library door** | **Holder locked** (§5): the kit object holds `BoundSurface`. As-built `0.69.4`: `palm.kits.present` in `INSTALLED_KITS`. Handle class unnamed. |
| **Empty-handed start** | As-built `0.69.5`: present kit owns `guidance_definition_id`. Unset refuses empty-handed `start()`. Set starts that definition by id. Phenotype seed and constructor override stay later. |
| **definition_id** | Compact publishes `flow` only. |
| **value on present** | No current-step draft on inspect/compact. |
| **mutation on job compact** | `compact_job_inspect` has no `mutation`. Wizard compact does. Shared turn should not require the wizard-only compact. |
| **Pattern invert incomplete** | Installed: `wizard`, `parallel`, `pipeline`, `dag`. `JobInspectable` today: wizard + parallel. `InteractiveRuntimeHooks` + read-model builder: **wizard only**. Pipeline / DAG: empty `JobContext` fallback + wait plane. Intention: `etl` (not installed). Kit must not paper this with a pattern `if`. |
| **Bind-aware start** | As-built `0.69.2`: `SessionService.attach_after_start` on the bound session. Kit `start()` as-built `0.69.4` walks `spawn_sibling`. Putting `session_id` on the job is leftover, not the floor. |
| **Kit Protocol** | Handle class unnamed. Package `palm.kits.present` as-built `0.69.4`. Do not stub `PresentService`. |
| **`guidance_instance_id` stamp** | Name + metadata-key + walk-write seam + **kit caller** locked (§5). As-built `0.69.1`: plane/SessionService stamp/replace (degenerate allow). As-built `0.69.5`: kit stamps after attach iff definition id equals; replace predicate on the kit. Interface type unnamed. |

Harvest locks in §5 are complete (including **job is session-ignorant**). Engine work in **0.69**: session-side attach after start (`0.69.2` door); spawn without nested park (`0.69.3` door); stamp **`guidance_instance_id`** (seam `0.69.1`; kit caller `0.69.5`). New pack remains `0.69.6`.

---

## 7. Open (not locked)

Homing, dashboard model, turn invert, kit-as-composition, pack, **`guidance_instance_id`**, **walk writes**, **job is session-ignorant**, **kit-contributed settings**, **stamp caller**, and **replace predicate** (kit definition-id check) are locked (§5). Protocol type names, kit handle class, walk-write interface type, and env spelling stay unnamed. Session-side attach glue is as-built (`0.69.2`). Park glue is as-built (`0.69.3`). Library door is as-built (`0.69.4`). Kit-contributed `guidance_definition_id` + stamp caller + replace predicate are as-built (`0.69.5`). New wizard pack stays later (`0.69.6`).

---

## 8. Non-goals (not 0.69’s subject)

Theme non-goals live in [VISION-0.69](VISION-0.69.md). This seed still refuses:

- A `GatewayService` or `TerminalService` product domain.
- Stretch admission into authorization.
- Encode application menus in structure definition (DNA ≠ catalog).
- Rewrite Assist / CLI / Portal in place.
- Implement user plane, impersonation, or catalog ACL as Navigator slices.
- Split the surface into a separate OS process as this invert’s floor.
- Use MCP, CLI, or Portal as the first kit consumer.
- Treat `EmbeddedRuntime` as the presentation adapter.

---

## 9. Related debt

| ID | Role |
|----|------|
| **SD-022** | Law docs treat talk/metaphor as types — clean when touched |
| **SD-010** | STE density rewrite (different care) |
| **SU-*** / **SI-002** | Surface compost — [VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md) |
| [VISION-0.68](closed/VISION-0.68.md) | Costume compost (**closed**). Residual [SD-023](../../TECH-DEBT.md#sd-023). Not the invert. |
| [VISION-TINY-LLM](VISION-TINY-LLM.md) | Model as resource · context as flow. **Not** this seed’s floor. A guidance pack may include a translator child after the invert is real. |
| User plane + impersonation | Principal policy (entry, visibility, act-as). Later seed. Not this invert. [ADR-027](../adr/027-session-plane.md) D11. |

*Guidance is a definition. The adapter only walks.*
