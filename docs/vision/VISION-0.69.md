# VISION 0.69 — Navigator

**Status:** 📋 **Theme open** (José 2026-09-17). Plan `0.69.0` · execute `0.69.2` landed (session-side attach after start). Package stamp stays `0.68.0`.  
**Language:** ASD-STE100 Simplified Technical English.  
**Map:** [PALM.md](../PALM.md) — read first.  
**ADR:** [037-navigator-invert.md](../adr/037-navigator-invert.md) **Proposed**.  
**Seed (law):** [VISION-NAVIGATOR](VISION-NAVIGATOR.md) §5–6.  
**Migration:** [MIGRATION-0.69](../migrations/MIGRATION-0.69.md) (stub).  
**Theme law:** [VERSIONING.md](../VERSIONING.md) (floor · growth · exit judgment).  
**Prior closed:** [VISION-0.68](closed/VISION-0.68.md) costume · residual [SD-023](../../TECH-DEBT.md#sd-023) · [SD-024](../../TECH-DEBT.md#sd-024).  
**Compost later:** [VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md).  
**Not this theme:** [VISION-TINY-LLM](VISION-TINY-LLM.md) · [VISION-0.56](VISION-0.56.md) · user plane.  
**North star:** [VISION-GROVE](VISION-GROVE.md).

Teaching name: **Navigator**.  
Law: operator-guidance **definition** + presentation kit **`palm.kits.present`**.

---

## 1. Goal

Move the empty-handed walk out of `AssistService` and into the **job path**.

| Piece | Role |
|-------|------|
| **Operator-guidance definition** | Catalog flow. Lists, selects, and starts other work. The instance **stays**. |
| **Presentation kit** | `palm.kits.present`. Geometry only: bind, present, submit, start, attach, focus. |
| **First adapter** | Embedded library surface. Phenotype `CompositionProfile.embedded()`. |
| **Walk fact** | Session metadata `guidance_instance_id`. |

**Success:**

- A client that does not know a definition id starts the process guidance definition.  
- Named work is a **sibling instance** on the same session.  
- The guidance job stays `WAITING_FOR_INPUT`. Return is `focus`.  
- The job does not carry `session_id`. Attach is session-side.  
- Assist, CLI forest, and Portal stay. This theme **grows beside** them.

### 1.1 Ambition and floor

| Concept | Meaning |
|---------|---------|
| **Floor** | One embedded walk proves the invert (see §2). |
| **Growth line** | Theme may grow while José keeps it open — glue, pack, kit install, pattern fill. |
| **Exit** | **José’s** judgment when the home is proper and residual is honest. |

**Who decides:** José Gabriel Gruber — [VERSIONING.md](../VERSIONING.md) *Who decides*.

---

## 2. Floor

The invert is **real** when tests on `CompositionProfile.embedded()` (no Assist) prove this chain:

1. Bind an outside session.  
2. Empty-handed `start()` uses kit-contributed `guidance_definition_id`.  
3. The guidance instance attaches. The kit stamps `guidance_instance_id`.  
4. The guidance job stays `WAITING_FOR_INPUT` (chooser shell).  
5. Named work starts as a **same-session sibling**. Attach is **session-side**. The child job has **no** `session_id`.  
6. Focus moves to the sibling. Focus returns with `focus(guidance_instance_id)`.  
7. Replace stamps only when the started definition id equals `guidance_definition_id`.

**Floor function:** that walk. Not MCP. Not CLI. Not Portal. Not user plane.

**Engine holes that the floor must close** ([VISION-NAVIGATOR](VISION-NAVIGATOR.md) §6.1):

| Hole | Floor glue |
|------|------------|
| **Start sibling** | ✅ `0.69.2` `SessionService.attach_after_start`. Not inherit `session_id` onto the job. Kit `start()` later. |
| **Park / home** | Spawn without nested park. Home stays operator-wait. No `WaitInterest` on siblings. |
| **Stamp** | Walk-write interface (degenerate allow). Kit asks after attach. `SessionService` writes. |

---

## 3. Growth

While the theme stays open, slices may:

- Install the kit (`INSTALLED_KITS`).  
- Seed `guidance_definition_id` for embedded / test phenotypes.  
- Fill pattern inspect/input so the kit has no pattern `if`.  
- Name Protocol / handle / walk-write types when José locks them.  
- Add a second guidance definition as a **title** (must not steal Home).

**Not floor:** env spelling of kit settings. Nested-on-`PalmSettings` vs sibling object. MCP / CLI / WS adapters. Compost of Assist.

---

## 4. Why now

1. **0.68** closed costume. Residual duals stay named. They are not this invert.  
2. Harvest locks in [VISION-NAVIGATOR](VISION-NAVIGATOR.md) §5 are complete.  
3. José named **0.69** (2026-09-17).  
4. Further surfaces on Assist grow the wrong home.

**Thesis:** Guidance is a definition. The kit only walks.

---

## 5. Non-goals (other seeds — not forever bans)

| Out of this theme’s *subject* | Home |
|-------------------------------|------|
| Compost Assist / CLI forest / Portal | [VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md) |
| Tiny model body / typed speak | [VISION-TINY-LLM](VISION-TINY-LLM.md) |
| Workload place book | [VISION-0.56](VISION-0.56.md) |
| User plane, impersonation, catalog ACL | [ADR-027](../adr/027-session-plane.md) D8 · D11 |
| Out-of-process surface | Client scale later |
| Host wizard-named flats | [SD-024](../../TECH-DEBT.md#sd-024) — do not pay as Navigator |
| 0.68 leftover duals | [SD-023](../../TECH-DEBT.md#sd-023) |

**Forbidden always (layer law):**

- A `GatewayService` / `TerminalService` / `PresentService` / `BotService` product domain.  
- Rewrite Assist / CLI / Portal **in place**.  
- Copy `session_id` onto the job as attach law.  
- Pattern `if` in the kit (`compact_wizard_inspect` vs `compact_job_inspect` by name).  
- Menus in structure definition.  
- Stretch admission into authorization.  
- Treat `EmbeddedRuntime` as the presentation adapter.  
- Fake catalog turns (`inspect_catalog` with no job).  
- Handoff after guidance **completes** as the Home path.

---

## 6. Principles

Bind to [PALM.md](../PALM.md), [ADR-027](../adr/027-session-plane.md), and [ADR-037](../adr/037-navigator-invert.md).

1. **Purpose is a definition.** Geometry is the kit.  
2. **Birth, then delete.** Grow beside Assist. Compost later.  
3. **Job is session-ignorant.** Session owns instances. Orchestration owns jobs.  
4. **Dashboard model.** Chooser shell. Session-owned titles. No wait on siblings.  
5. **Turn invert.** Kit walks. Pattern fills inspect/input.  
6. **Walk writes** go through a system interface. Floor allow. User plane installs later.  
7. **Kit-contributed settings.** `guidance_definition_id` lives on the present kit, not core `PalmSettings`.  
8. **One anonymous outside subject** on the floor. The adapter does not filter the catalog.  
9. **STE** for theme docs. Spoken words are teaching only ([VISION-NAVIGATOR](VISION-NAVIGATOR.md) §2).  
10. **Theme exit is José’s judgment** when the home is proper.

**Spirit:** Do not grow a second spine. Use the job path.

---

## 7. Locks (carried from the seed)

José locked these on **2026-09-15–16**. Detail: [VISION-NAVIGATOR](VISION-NAVIGATOR.md) §5.

| Cut | Law |
|-----|-----|
| **Guidance home** | Instance stays attached. Focus leaves and returns. |
| **Dashboard model** | Operator-wait chooser. Spawned work is peer titles. |
| **Kit** | `palm.kits.present`. Kit-as-composition. One `BoundSurface`. |
| **First adapter** | Embedded library surface. Engine stays `EmbeddedRuntime`. |
| **Turn invert** | Kit walks. Pattern fills. No pattern `if`. |
| **Pack** | New wizard **beside** `operator_entry`. Stay waiting. Return is `focus`. |
| **Job is session-ignorant** | Attach after start on the session. |
| **`guidance_instance_id`** | Session metadata. Stamp caller = kit after attach. |
| **Replace predicate** | Kit; attached; definition id equals `guidance_definition_id`. |
| **Walk writes** | System interface. Floor degenerate allow. |
| **Kit-contributed settings** | Present owns `guidance_definition_id`. Unset → no empty-handed start. |
| **Principal** | Entry and visibility are later user plane. Not this floor. |

**Still unnamed (José locks later):** Protocol type names, kit handle class, walk-write interface type, env spelling.

[ADR-006](../adr/006-assist-domain.md) stays **Accepted** as as-built Assist. This ADR does **not** supersede it. Surface compost may supersede later.

---

## 8. Target shape

```text
  CLIENT (embedded Python)
    palm.kits.present  — holds BoundSurface; walks doors
            │
  PRODUCT — SessionService · execution present / start / input
            │
  SYSTEM  — session plane (attach, focus, metadata)
            — walk-write interface (stamp / replace keys)
            — wait plane · work plane
            │
  CATALOG — new operator-guidance wizard (stays waiting)
          — any other definition as a sibling title
```

Assist remains a parallel as-built spine until [VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md).

---

## 9. Guide slices (not a sealed contract)

Execution starts at `0.69.1`. Protocol + failing tests belong in execute, not this plan file.

| Slice | Intent |
|-------|--------|
| **0.69.0** | Plan + ADR-037 Proposed + this floor. José locked floor + slice guide. |
| **0.69.1** | ✅ Walk-write seam (degenerate allow) + `guidance_instance_id` stamp/replace. Interface type unnamed. |
| **0.69.2** | ✅ Session-side attach after start. Job stays session-ignorant. `SessionService.attach_after_start`. |
| **0.69.3** | Spawn without nested park. Guidance stays operator-wait. |
| **0.69.4** | `palm.kits.present` kit-as-composition (bind, present, submit, start, attach, focus). |
| **0.69.5** | Kit-contributed `guidance_definition_id` + stamp caller + replace predicate. |
| **0.69.6** | New wizard pack beside `operator_entry`. |
| **0.69.7** | Empty-handed start dogfood on embedded — **floor proof**. |

Merge or extend when review stays clear. Do not skip the three engine holes.

---

## 10. Debt budget

| ID | Motion |
|----|--------|
| Engine holes (attach / park / stamp) | **Pay** in this theme |
| [SD-022](../../TECH-DEBT.md#sd-022) | Clean talk-as-type when a law file is touched |
| [SD-023](../../TECH-DEBT.md#sd-023) | **Name** — not this theme |
| [SD-024](../../TECH-DEBT.md#sd-024) | **Name** — do not grow the kit on host wizard flats |
| [SU-*](../../TECH-DEBT.md) / SI-002 | Surface deflation later |
| [ADR-006](../adr/006-assist-domain.md) | Stays until compost |

---

## 11. Exit judgment

Exit when José judges:

- The floor walk holds in code and tests.  
- ADR-037 Accepted (or waived honestly).  
- Residual named.  
- Spine green on declared modes.

Do not close because the slice table is ticked.  
Do not keep the theme open to compost Assist.

---

*Guidance is a definition. The adapter only walks.*
