# ADR-028 — System boot schedule + composition truth

**Status:** Accepted  
**Date:** 2026-08-01  
**Accepted:** 2026-08-01 (theme exit `0.59.8`)  
**Theme:** [VISION-0.59](../vision/closed/VISION-0.59.md) (**closed**)  
**Inventory:** [BOOT-INVENTORY.md](../BOOT-INVENTORY.md)  
**System log:** [SYSTEM-LOG.md](../SYSTEM-LOG.md) (seats live; richer catalog residual **BI-015**)  
**Map:** [PALM.md](../PALM.md)  
**Debt:** [SD-014](../../TECH-DEBT.md#sd-014) ✅ closed at exit · residual **BI-***  
**Release:** [RELEASE-0.59.8](../releases/RELEASE-0.59.8.md) · [MIGRATION-0.59](../migrations/MIGRATION-0.59.md)  
**Related:** [ADR-019](019-composition-profiles.md) · [ADR-018](018-application-host-decomposition.md) · [ADR-026](026-palm-system-layer.md) · [ADR-017](017-import-seams.md)

---

## Context

1. Palm has a named **system** layer ([ADR-026](026-palm-system-layer.md)) and a **session** plane ([ADR-027](027-session-plane.md)).  
2. **CompositionProfile** and **DeploymentProfile** declare shape ([ADR-019](019-composition-profiles.md), [ADR-020](020-living-capabilities.md)).  
3. Boot order still lives in imperative code: `ApplicationHost.start`, `BaseRuntime.start`, plus dual root residual (`ServerContext`).  
4. Plugin load (`INSTALLED_*` + autoload) is correct for **plugins**. It is the **wrong** model for **planes**.  
5. Session work (0.58) forced the split: plugins vs planes vs surface bind. The remaining pain is **scattered boot** and **implicit order** ([SD-014](../../TECH-DEBT.md#sd-014)).  
6. Palm is pre-1.0. Temporary phenotype breaks are acceptable when they **harvest isolation**. Silent dual paths are not.

---

## Decision

### D1 — Two schedules, one story

Palm boots at two levels. Name both.

| Schedule | Owner | Role |
|----------|-------|------|
| **System schedule** | System instance (`BaseRuntime` today) | Engines, ports, planes, job hooks, ready |
| **Host schedule** | Composition root (`ApplicationHost` today) | Kernel bootstrap, spawn, definitions, product wire, surfaces, recover/drain |

The host schedule **calls** the system schedule when it spawns a system instance.  
Modules do **not** invent private boot order via import side effects.

### D2 — Phase table, not soup

Each schedule is a **phase table** walked by one driver.  
Phases have stable ids. Handlers may start as **stubs** and gain bodies over slices.  
A phase table is **not** a second plugin framework.

### D3 — Three orthogonal axes

| Axis | Answers |
|------|---------|
| **CompositionProfile** | *What* is installed (services, surfaces, capabilities) |
| **DeploymentProfile** | *Where* / which roles run |
| **Boot mode + schedule options** | *Order* and *strictness* (safe / test / dev / prod / shape presets) |

Do **not** merge axes into one god-object.  
Modes are **presets** over the axes (and phase options), not a fourth competing composition root.

### D4 — Composition is membership truth

On the migrated path, **CompositionProfile** (with settings resolver) is the only switch for:

- which product services build,  
- which surfaces mount,  
- which capabilities attach (outbox, work_drain, projections, …).

Host code must not grow parallel `if` forests that ignore the profile.  
**DeploymentProfile** still selects roles and deployment-facing activation.

**0.59.5 (implemented):** runtime gates read composition only. Settings resolver may
fold deployment `enable_work_drain_service` into membership once; explicit
`CompositionProfile` always wins. PhaseSkip reasons `composition_off:*`;
`boot.start` and doctor `boot.membership` report phenotype.

**Succession (organs — post-0.64 / StructureDefinition):** D4’s organ examples
(`outbox`, `work_drain`, `projections`, …) are **historical**. Those organs now
live on `StructureDefinition.capabilities` → `LOCAL_CAPABILITY_HANDS` (hands /
materialize). Composition `capabilities` remain **workloads** only (phenotype
plane flag). Do **not** re-wire organs onto `CompositionProfile`. Current law:
[VISION-ASSEMBLY](../vision/VISION-ASSEMBLY.md) · structure definition + hands.
Composition still owns product **services**, **surfaces**, and workload
membership on the phenotype path.

### D5 — Plugins vs planes (preserve)

1. **Plugins** — settings / `INSTALLED_*` declare membership; packages self-register downward.  
2. **Planes** — not plugins; not on install lists; system schedule owns attach order.  
3. Do **not** add a second dynamic-import layer on top of autoload.

### D6 — Keep stacks separate

Do **not** collapse into one global middleware list:

- surface request filters,  
- job hooks,  
- plane law (start / continue / place / session),  
- event consumers.

Each stack has its own phase or attach story.

### D7 — Stub-first seats

Implement the full schedule **shape** early.  
Stubs remind intent. Stubs must not report fake success for unmigrated work.  
Prefer structured “not migrated” over silent fallthrough that hides holes.

### D8 — Break / harvest (theme method)

Mid-theme, not every phenotype must stay green.  
When boot migration breaks a path:

1. Classify: accidental dependency · misplaced rule · true owner · out of theme · spine regression.  
2. **Harvest** the rule: re-home it to the correct phase, port, product door, or registry.  
3. Record residual as **BI-*** with owner and kill condition if dual path is temporary.  
4. Prefer a **smaller honest mode** over restoring import-order magic.

**Spine regressions** (job path, wait law, session law) fix in-theme.  
Do not re-litigate closed plane law under “boot.”

### D9 — Declared green bar

Each slice states which **modes** are in the green bar.  
Unmigrated modes may fail. Do not claim they are supported.  
Theme exit requires: spine + declared modes green; residual chrome named.

### D10 — Package homes (intent)

| Concern | Home (target) |
|---------|----------------|
| System phase protocol | `palm.system.boot` |
| Host phase handlers | `palm.app.host.boot` |
| Mode presets | `palm.app.host.boot.modes` (beside composition / deployment) |

System schedule must not import product or surfaces.  
**0.59.2:** tables, walker, modes, early log seats live under these homes.  
**0.59.3:** system handlers live under `palm.system.boot.system_schedule`.  
`BaseRuntime` is the assembly shell — it does not own start order.  
`palm.system.runtime` package init must not eagerly import `BaseRuntime` (keeps boot → collaborator edges acyclic).  
**0.59.4:** host handlers live under `palm.app.host.boot.host_schedule`.  
`ApplicationHost` is the composition-root shell — it does not own start order.

### D11 — Non-goals locked by this ADR

- Surface deflation purge.  
- Shared plane-store framework.  
- Grove mesh.  
- Planes as install-list plugins.  
- Permanent dual boot paths for comfort.

### D12 — System log is observation (not control)

Boot **control** is the phase table.  
Boot **observation** is a **system log** — ordered narrative of system life.

System log is **not** the domain event bus, **not** EventJournal, **not** a telemetry product.  
Implementation: `palm.system.log` · plan [SYSTEM-LOG.md](../SYSTEM-LOG.md) · [BI-015](../../TECH-DEBT.md#bi-015).  
Do not make system log the wait/work path.

---

## Consequences

### Positive

- Boot becomes **testable and reportable** (phase dump, mode pins).  
- Tangled order becomes **visible** phase boundaries.  
- Safe / test / dev / prod control becomes real.  
- CompositionProfile stops being a partial lie.  
- Isolation harvest turns red tests into better shape.  
- System log gives an ordered tape without reading source (0.59.1a).

### Negative / risk

- Mid-theme red on legacy host paths and heavy surfaces.  
- Host and runtime start are hot files — slices must stay small.  
- Risk of over-frameworking — mitigated by “table + walker only.”

### Residual

- Dual root (`ServerContext`) folds only when schedule makes it cheap (BI-*).  
- Surface compost remains a later theme.  
- Exact phase names lock after inventory (0.59.1+), not in this ADR’s prose sketches.  
- System log may ship partial (BI-015 residual) if phase control finishes first.

---

## Acceptance (theme exit) — **met at 0.59.8**

- [x] ADR status → **Accepted**.  
- [x] SD-014 closed; residual re-homed as honest **BI-***.  
- [x] Phase tables walk in code for system + host.  
- [x] `safe`/`test` + full shapes dogfooded (**0.59.6**–**0.59.7**).  
- [x] Membership truth on migrated path (**0.59.5**).  
- [x] System log seats live; richer catalog residual **BI-015**.  
- [x] [VISION-0.59](../vision/closed/VISION-0.59.md) closed with residual named.

---

## Notes

Illustrative phase lists live in [VISION-0.59](../vision/closed/VISION-0.59.md) and [SD-014](../../TECH-DEBT.md#sd-014).  
They are **spirit**, not frozen public API, until inventory freezes ids.
