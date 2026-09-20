# VISION 0.71 — Place registry (adopt)

**Status:** 📋 **Theme open** (José 2026-09-20). Execute `0.71.0`–`0.71.11` landed. Names locked (`adopt` / `adopt:` / empty `runtime` / `Workload` rows). Remaining: José exit judgment. Package stamp stays `0.68.0` (no embedded release).  
**Language:** ASD-STE100 Simplified Technical English.  
**Map:** [PALM.md](../PALM.md) — read first.  
**ADR:** [039-place-registry-adopt.md](../adr/039-place-registry-adopt.md) **Proposed**.  
**Scout (engine):** [VISION-0.56](VISION-0.56.md) · [ADR-024](../adr/024-workload-engine.md) **Accepted**.  
**Assembly hands (spawn already):** [VISION-0.63](closed/VISION-0.63.md) `0.63.16` `workload:` · [ADR-032](../adr/032-organism-assembly.md) **Accepted**.  
**Theme law:** [VERSIONING.md](../VERSIONING.md) (floor · growth · exit judgment).  
**Prior closed:** [VISION-0.70](closed/VISION-0.70.md) Authoring · [ADR-038](../adr/038-authoring-adapter.md) **Accepted**.  
**Needs later:** [VISION-TINY-LLM](VISION-TINY-LLM.md) — model body is a place; speak is not this theme.  
**Not this theme:** [VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md) · [VISION-TUNNELS](VISION-TUNNELS.md).  
**North star:** [VISION-GROVE](VISION-GROVE.md).

Teaching name (once): **place book remainder**.  
Law: **place registry** — named places Palm may mean (spawn or adopt); lifecycle + readiness. Home: workload plane.

**Open:** José named **0.71** (2026-09-20). Floor: **adopt**. Spawn via `WorkloadEngine` is already `0.63.16`. Do not reopen `0.56`.

---

## 1. Goal

[PALM.md](../PALM.md) says the **place registry** lives on the workload plane. Structure may **require** places. Tiny LLM needs a named body Palm did not necessarily start.

As-built is two books:

| Home | What it does |
|------|----------------|
| **Workload plane** | Engine, runners (`local` / `host` / `neonroot`), `execution.workloads`, WorkloadLeaf. Isolation is real. |
| **Structure (0.63)** | `InProcessPlaceRegistry` + `PlaceSpawnPort`. `workload:` **spawns** through `WorkloadPlaceSpawn` (`0.63.16`). Bare ids still succeed **in-process** (no body). |

A place Palm **adopts** is missing. “The server is already up” has no honest row. Structure copies readiness. It does not own body truth.

| Piece | Role |
|-------|------|
| **Place registry** | Truth home of **bodies** (spawned or adopted). Workload plane. |
| **Adopt** | Record an existing body. Do not start a runner. |
| **Spawn** | Already `workload:` → `WorkloadEngine`. Do not duplicate. |
| **Structure hand** | `PlaceSpawnPort` / `RegisteredPlaceSpawn` routes. Projection of readiness. Not a second book. |

**Success (floor):**

- Adopt a named place with a handle (`WorkloadHandle.base_url` is enough).  
- The workload book records it **ready**. No runner `start`.  
- Structure `ENSURE_PLACE` / `places_required` for that place converges.  
- Missing handle → **fail closed**. Not in-process success.

### 1.1 Ambition and floor

| Concept | Meaning |
|---------|---------|
| **Floor** | One adopt proves the registry can mean an existing body (see §2). |
| **Growth line** | Theme may grow while José keeps it open — projection, release-as-unbind, spawn-on-same-book honesty. |
| **Exit** | **José’s** judgment when the home is proper and residual is honest. |

**Who decides:** José Gabriel Gruber — [VERSIONING.md](../VERSIONING.md) *Who decides*.

---

## 2. Floor

The registry is **real** when tests prove this chain:

1. Adopt a named place. Handle at least `base_url` (existing `WorkloadHandle`).  
2. The **workload** book holds a **ready** record. No `WorkloadRuntime.start`.  
3. Structure `ENSURE_PLACE` for that place returns ready. `places_required` converges. Admission may run business.  
4. Adopt without a handle, or with an empty id, **fails closed**.

**Floor function:** that adopt. Not Tiny LLM. Not ssh. Not MCP. Not compost of bare in-process ids.

**Locked prefix:** `adopt:`. Same table as `workload:` / `os:` (`RegisteredPlaceSpawn`). Not a new `if`.

**As-built `0.71.1`:**

- `WorkloadEngine.adopt(id, handle)` records `READY` with `WorkloadHandle.base_url`. No `WorkloadRuntime.start`. Empty id or missing `base_url` raises `WorkloadSpecError`.
- Adopted row uses empty `runtime` (no runner). `stop` unbinds. `exec` fails closed. Status refresh does not poll.
- `AdoptPlaceSpawn` registers prefix `adopt:` on `RegisteredPlaceSpawn` and on `combined_structure_spawn_port`.
- ENSURE / `places_required` converge when the book already holds that place id. Missing handle fails closed (`adopt_handle_missing`), not in-process ready.
- Tests: `tests/test_place_adopt_0_71_1.py`.

**As-built `0.71.2`:**

- `InProcessPlaceRegistry.places` is a view. Bound `WorkloadEngine` rows win for `structure_place` / workload id.
- Adopted unbind (`stop`, empty runtime → `STOPPED`) drops ready from the view without a `RELEASE_PLACE` intent.
- Overlay keeps bare in-process ids and failed ensures that never entered the book.
- Tests: `tests/test_place_registry_projection_0_71_2.py`.

**As-built `0.71.3`:**

- `AdoptPlaceSpawn` / `WorkloadPlaceSpawn` do not keep a `place_id` → `workload_id` map. Place id is the workload id.
- `PlaceEffectPort` does not write overlay for `adopt_*` / `workload_*` outcomes. Failed adopt is an observation, not a registry row.
- Overlay remains for bare in-process and `os:` (named residual).
- Tests: `tests/test_place_maps_compost_0_71_3.py`.

**As-built `0.71.4`:**

- `RegisteredPlaceSpawn.register_bind` / `BookBindPort` — typed book binds. `host_bind` / `place_registry` walk binds; they do not duck-walk `handles` for workload/adopt hands.
- Tests: `tests/test_spawn_bind_invert_0_71_4.py`.

**As-built `0.71.5`:**

- `place_registry` / `workload_place` read typed `Workload` / `WorkloadHandle` fields. They do not getattr duck-type book rows.
- Tests: `tests/test_workload_row_reads_0_71_5.py`.

**As-built `0.71.6`:**

- `host_bind` takes typed `WorkloadBearingShell` / `WorkloadEngine` / `StructureEffectPort`|`PlaceEffectPort` / `RegisteredPlaceSpawn.workload_bind`. No getattr or Protocol-isinstance duck nests for bind discovery.
- Tests: `tests/test_host_bind_typed_0_71_6.py`.

**As-built `0.71.7`:**

- `place_registry.engine_from_spawn` matches typed `RegisteredPlaceSpawn` (same invert as `host_bind.book_bind_port`). No Protocol `isinstance(spawn, BookBindPort)`.
- Tests: `tests/test_place_registry_typed_spawn_0_71_7.py`.

**As-built `0.71.8`:**

- `AdoptPlaceSpawn` / place→engine boundary takes typed `WorkloadHandle` only. No dict | `base_url` coercion in `_handle_from_payload`.
- Tests: `tests/test_handle_payload_invert_0_71_8.py`.

**As-built `0.71.9`:**

- No `overlay` dict beside the workload book. Bound: `places` is book projection only. Unbound: one local register for bare / `os:` ready. Failed ensures stay observations.
- Tests: `tests/test_place_overlay_compost_0_71_9.py`.

**As-built `0.71.10`:**

- `RegisteredPlaceSpawn.register_body` / `body` / `forget_body` — typed place-id body register. `os_registry` is typed. No `handles` bag. No `__os_registry__` magic key.
- Tests: `tests/test_spawn_handles_invert_0_71_10.py`.

**As-built `0.71.11`:**

- StructureEngine binds place-registry `ready(place_id)` for assemble / admission. PLACE_READY does not accumulate a second body book when that hand is bound. Bound bare / `os:` acks live on the registry local register; `places` stays book projection only.
- Tests: `tests/test_place_observations_invert_0_71_11.py`.

**As-built to keep:**

- `0.63.16` `workload:` spawn via `WorkloadPlaceSpawn` / `combined_structure_spawn_port`.  
- Fail closed when `workload:` has no engine.  
- `os:` fail closed until a body strategy exists.  
- Bare place ids: in-process success via registry `ready` when book-bound (`places` stays book projection).

---

## 3. Growth

While the theme stays open, slices may:

- Make structure `InProcessPlaceRegistry` a **projection** of the workload book for adopted and `workload:` ids.  
- Keep spawn on the same book. Do not add a second spawn path.  
- Leave room for Tiny LLM: a long-lived small **service** as a place. Speak stays a later provider.

`adopt:` is on `combined_structure_spawn_port`. Adopted `stop` unbinds (no runner `stop`). Structure registry projects the book for adopted and `workload:` ids (`0.71.2`).

**Not floor:** product CQRS `workload.adopt`. MCP. New runners. Invert of `LocalPalmInvoker`. Assist compost.

---

## 4. Why now

1. **0.70** closed land. Consume and land exist. A model body still has no honest place.  
2. **0.56** landed the engine. STATUS called the rest a scout remainder. That remainder is **adopt**, not ssh/k8s/peer mesh.  
3. **0.63.16** already spawns `workload:`. Reopening 0.56 would relitigate runners.  
4. José named **0.71** (2026-09-20). Floor phenotype: adopt.

**Thesis:** Mean a body that already exists. Spawn stays the other verb on the same registry.

---

## 5. Non-goals (other seeds — not forever bans)

| Out of this theme’s *subject* | Home |
|-------------------------------|------|
| Tiny model inference / schema muzzle | [VISION-TINY-LLM](VISION-TINY-LLM.md) |
| Compost Assist / CLI forest / Portal | [VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md) |
| Full 0.56.7–13 list (ssh, k8s, peer, blueprints) | [VISION-0.56](VISION-0.56.md) remainder — not this floor |
| Tunnels / Grove | [VISION-TUNNELS](VISION-TUNNELS.md) · [VISION-GROVE](VISION-GROVE.md) |
| Authoring names / `palm` catalog write | [SD-025](../../TECH-DEBT.md#sd-025) |
| Host wizard-named flats | [SD-024](../../TECH-DEBT.md#sd-024) |
| 0.68 leftover duals | [SD-023](../../TECH-DEBT.md#sd-023) |
| Bare in-process place ids (body strategy) | Later — `0.71.9` removed the overlay dual; `0.71.11` bare ready when book-bound is registry `ready`, not a second engine book |

**Forbidden always (layer law):**

- A `PlaceService` / `AdoptService` / `BotService` product domain.  
- A fat model-driver provider (isolation + I/O + prompt).  
- A one-name `if` on `LocalPalmInvoker` or on `PlaceSpawnPort`.  
- Structure registry as a second truth home for bodies.  
- Adopt that calls a runner `start`.  
- Release of an adopted place as SIGKILL.  
- New MCP / CLI / Portal surfaces.  
- Reopen `0.56` numbering.  
- Bump the package stamp.

---

## 6. Principles

Bind to [PALM.md](../PALM.md), [ADR-024](../adr/024-workload-engine.md), [ADR-032](../adr/032-organism-assembly.md).

1. **Two axes stay split.** Vertical = home / structure. Horizontal = place registry.  
2. **Allocate vs speak.** Workload places bodies. Providers speak. Do not collapse.  
3. **Spawn or adopt.** Same book. Different origin.  
4. **Hands route.** `RegisteredPlaceSpawn` is the table. New member = register.  
5. **Fail closed.** Missing body is not in-process ready.  
6. **Palm did not create it.** Adopted release is unbind.  
7. **STE** for theme docs. Spoken “place book” is teaching only.  
8. **Theme exit is José’s judgment** when the home is proper.

**Spirit:** Do not grow a third registry. Use the workload book.

---

## 7. Locks (José 2026-09-20)

| Cut | Law |
|-----|-----|
| **Theme** | **0.71**. Not a reopen of 0.56. |
| **Law word** | **Place registry** (not place book as a type). |
| **Floor** | **Adopt** a named place with a handle. |
| **Spawn** | Already `0.63.16`. Not the floor. |
| **Method** | `WorkloadEngine.adopt` (locked). |
| **Prefix** | `adopt:` (locked). Same table as `workload:` / `os:`. |
| **Runtime** | Empty `runtime` on adopted rows. No fake runner name. |
| **Row type** | Adopted rows stay `Workload`. |
| **Handle** | Existing `WorkloadHandle` (`base_url` enough). |
| **Stamp** | `0.68.0`. No embedded release at open. |

---

## 8. Slice guide (ordered intent, not a sealed contract)

| Slice | Intent |
|-------|--------|
| **0.71.0** | Plan. This file. ADR **Proposed**. STATUS. PALM one-line pointer. **landed**. |
| **0.71.1** | Floor: adopt into the workload book; structure ENSURE; fail closed without handle. **landed**. |
| **0.71.2** | Growth: `InProcessPlaceRegistry` projects the workload book. **landed**. |
| **0.71.3** | Compost extra maps. Place id is the book id. **landed**. |
| **0.71.4** | Typed book binds. No handles duck-walk for bind discovery. **landed**. |
| **0.71.5** | Typed `Workload` / `WorkloadHandle` book-row reads. **landed**. |
| **0.71.6** | Typed `host_bind` shell / engine / effects / spawn hands. **landed**. |
| **0.71.7** | Typed `place_registry` spawn / book bind (no Protocol isinstance). **landed**. |
| **0.71.8** | Typed adopt payload handle (no dict \| `base_url` coercion). **landed**. |
| **0.71.9** | Compost overlay; bare / `os:` no second map beside the book. **landed**. |
| **0.71.10** | Invert `handles`; typed `register_body` / `os_registry`. **landed**. |
| **0.71.11** | Invert StructureEngine place observations onto registry `ready`. **landed**. |

Names are locked. Remaining is José exit judgment. Leftovers in §11 stay **named residual**.

---

## 9. Names (locked José 2026-09-20)

| Locked | Spelling |
|--------|----------|
| Method | `adopt` |
| Prefix | `adopt:` |
| Adopted runtime | empty (no fake runner name) |
| Adopted row | `Workload` (not a thinner place row) |

Do not invent a Protocol type name for the registry.

---

## 10. Debt budget

| Pay or leave | Note |
|--------------|------|
| Adopt missing | **Pay** on floor (`0.71.1`). |
| Structure copy of readiness | **Pay** on growth (`0.71.2` projection, `0.71.3` compost). |
| Handles duck-walk for bind hands | **Pay** on invert (`0.71.4` typed `BookBindPort`). |
| Book-row getattr duck-type | **Pay** on invert (`0.71.5` typed `Workload` / `WorkloadHandle` reads). |
| Host bind getattr / isinstance duck nest | **Pay** on invert (`0.71.6` typed shell / effects / `workload_bind`). |
| place_registry Protocol isinstance on spawn | **Pay** on invert (`0.71.7` typed `RegisteredPlaceSpawn`). |
| EffectIntent payload handle coercion | **Pay** on invert (`0.71.8` typed `WorkloadHandle` only). |
| Bare in-process ids / `os:` overlay | **Pay** on compost (`0.71.9` — no overlay beside the book). |
| `RegisteredPlaceSpawn.handles` | **Pay** on invert (`0.71.10` typed `register_body` / `os_registry`). |
| StructureEngine place observations | **Pay** on invert (`0.71.11` registry `ready` hand). |
| `workload_place` remaining `isinstance` | **Leave** named. Env dict (~L198); typed `WorkloadHandle` accept at Mapping body (~L341). |
| `WorkloadEngine` remaining `isinstance` | **Leave** named. Runtime bind dict / `WorkloadRuntime` (~L71/L73); argv-must-not-be-str (~L273). |
| 0.56 ssh/k8s/peer/blueprints | **Leave** on the scout. |
| SD-025 invoker invert | **Leave**. Other organ. |

---

## 11. Residual (open)

Theme stays **open**. Execute `0.71.0`–`0.71.11` landed. Names locked. Next is José exit judgment.

| Residual | Truth |
|----------|-------|
| `workload_place` remaining `isinstance` | Env dict gate (~L198); typed `WorkloadHandle` accept at Mapping body (~L341). Payload shape / fail-closed. **Not** honest compost now. |
| `WorkloadEngine` remaining `isinstance` | Initialize runtime bind dict / `WorkloadRuntime` (~L71/L73); argv-must-not-be-str (~L273). Fail-closed. **Not** honest compost now. |
