# VISION 0.71 — Place registry (adopt)

**Status:** 📋 **Theme open** (José 2026-09-20). Floor execute `0.71.1` landed. Package stamp stays `0.68.0` (no embedded release).  
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

**Working prefix** until José locks a name: `adopt:`. Same table as `workload:` / `os:` (`RegisteredPlaceSpawn`). Not a new `if`.

**As-built `0.71.1`:**

- `WorkloadEngine.adopt(id, handle)` records `READY` with `WorkloadHandle.base_url`. No `WorkloadRuntime.start`. Empty id or missing `base_url` raises `WorkloadSpecError`.
- Adopted row uses empty `runtime` (no runner). `stop` unbinds. `exec` fails closed. Status refresh does not poll.
- `AdoptPlaceSpawn` registers prefix `adopt:` on `RegisteredPlaceSpawn` and on `combined_structure_spawn_port`.
- ENSURE / `places_required` converge when the book already holds that place id. Missing handle fails closed (`adopt_handle_missing`), not in-process ready.
- Tests: `tests/test_place_adopt_0_71_1.py`.

**As-built to keep:**

- `0.63.16` `workload:` spawn via `WorkloadPlaceSpawn` / `combined_structure_spawn_port`.  
- Fail closed when `workload:` has no engine.  
- `os:` fail closed until a body strategy exists.  
- Bare place ids: in-process success. **Named residual.** Do not compost on the floor.

---

## 3. Growth

While the theme stays open, slices may:

- Make structure `InProcessPlaceRegistry` a **projection** of the workload book for adopted and `workload:` ids.  
- Keep spawn on the same book. Do not add a second spawn path.  
- Leave room for Tiny LLM: a long-lived small **service** as a place. Speak stays a later provider.

`adopt:` is on `combined_structure_spawn_port`. Adopted `stop` unbinds (no runner `stop`).

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
| Bare in-process place ids | Named residual — not floor compost |

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
| **Prefix** | Working `adopt:` until José locks. |
| **Handle** | Existing `WorkloadHandle` (`base_url` enough). |
| **Stamp** | `0.68.0`. No embedded release at open. |

---

## 8. Slice guide (ordered intent, not a sealed contract)

| Slice | Intent |
|-------|--------|
| **0.71.0** | Plan. This file. ADR **Proposed**. STATUS. PALM one-line pointer. |
| **0.71.1** | Floor: adopt into the workload book; structure ENSURE; fail closed without handle. **landed**. |
| **0.71.2+** | Growth: projection of `InProcessPlaceRegistry`; José locks names. |

Cheaper execute is allowed **from 0.71.1** only, inside a kill-box (file list, forbidden list, stop on workaround `if`). José or a judgment model writes that box. A cheaper model does not open slices or rename law words.

---

## 9. Names still unnamed

| Working | Who locks |
|---------|-----------|
| Prefix `adopt:` | José |
| Engine / registry method spelling for adopt | José after 0.71.1 proposes as-built |
| Whether adopted records share `Workload` or a thinner place row | Propose in 0.71.1; José locks if contested |

Do not invent a Protocol type name for the registry.

---

## 10. Debt budget

| Pay or leave | Note |
|--------------|------|
| Adopt missing | **Pay** on floor (`0.71.1`). |
| Structure copy of readiness | **Leave** if floor still converges; pay as projection on growth. |
| Bare in-process ids | **Leave** named. |
| 0.56 ssh/k8s/peer/blueprints | **Leave** on the scout. |
| SD-025 invoker invert | **Leave**. Other organ. |

---

## 11. Residual (open)

- Structure `InProcessPlaceRegistry` still **copies** readiness. It is not a projection of the workload book (`0.71.2+`).
- Working names: method `adopt`, prefix `adopt:`, empty `runtime` on adopted rows. José locks.
- Reuse `Workload` for adopted rows. Contested only if José wants a thinner place row.

Do not claim projection paid unless tests show one book.
