# Palm — Boot inventory (0.59.1)

**Status:** Characterization of **today’s** boot (stamp `0.58.20` + theme open).  
**Theme:** [VISION-0.59](vision/closed/VISION-0.59.md) (**closed**) · [ADR-028](adr/028-system-boot.md) **Accepted** · stamp `0.59.8`  
**System log plan:** [SYSTEM-LOG.md](SYSTEM-LOG.md) (0.59.1a) — runtime tape for these phase ids when seats land  
**Debt:** [SD-014](../TECH-DEBT.md#sd-014) · [BI-*](../TECH-DEBT.md#bi-boot-impact-inventory) · [BI-015](../TECH-DEBT.md#bi-015)  
**Language:** ASD-STE100 (practical).  
**Rule:** This file is **truth about current code**. Phase ids here are **provisional names** for the future table — not a public API yet.

---

## 1. Why this document

Theme 0.59 needs a shared picture:

- what already runs,
- in what order,
- what membership already controls,
- what is still soup,
- what the **green bar** is for the whole theme.

Without this, stubs and refactors fight ghost expectations.

---

## 2. Entrypoints (who starts Palm)

| Path | Code | What it does |
|------|------|----------------|
| **Library host** | `ApplicationHost(...).start()` | Full composition root |
| **CLI** | `create_cli_host()` → host + `all_in_one` deployment | Collapsed embedded `main` |
| **run_host** | `run_host(profile=…)` | Host + signal block |
| **Kernel only** | `PalmKernel.bootstrap()` + `create_runtime(..., autostart=True)` | Infra + system instance; **no** CQRS/product wire |
| **ServerRuntime** | `ServerRuntime.start` → `BaseRuntime.start` | System schedule; HTTP later via host attach |
| **Standalone ServerContext** | `ServerContext(runtime)` host-less | Lean product services + standalone buses (**no** host schedule) |
| **MCP in-process** | often runtime.start(http=False) | May bypass full host (BI residual) |
| **Tests** | many `ApplicationHost` + profiles; conftest calls `ensure_core_plugins()` at import | Green bar must pin named shapes |

**Dual root residual (BI-003):** `ApplicationHost` vs host-less `ServerContext` share `core_service_registry()` but not one boot schedule.

---

## 3. Host schedule (today — imperative)

Source: `ApplicationHost.start` + collaborators.

| # | Provisional id | What runs | Notes |
|---|----------------|-----------|--------|
| H0 | `host.init` | `__init__`: settings, deployment, composition, kernel, buses, facades | Not in `start()`; still “boot assembly” |
| H1 | `kernel.bootstrap` | `PalmKernel.bootstrap()` → `ensure_plugins()` → `ensure_core_plugins()` | Plugin load **first** time; again in system start (idempotent) |
| H2 | `host.event` | Host `EventEngine.initialize()` + `HostEventRecorder.attach` | Host bus ≠ job bus |
| H3 | `workers.note` | `WorkerCoordinator(profile, host.event)` | Readiness later in recover |
| H4 | `system.spawn` | `RuntimeSpawner.spawn_runtimes` → `create_runtime(..., autostart=True)` | **Enters system schedule** per runtime |
| H5 | `definitions.load` | `PalmKernel.load_definitions()` | After system instances exist |
| H6 | `product.wire` | `_wire_cqrs()` | Commands, projections/capability, **services from composition**, workplane wire, service CQRS |
| H7 | `surfaces.mount` | `_start_server_surface()` if `profile.server` | attach_host + start_http |
| H8 | *(composted 0.68.1)* | — | Empty `host.projections.attach` dropped. DNA hand attaches; host slots alias in H6. Not in `HOST_PHASES`. |
| H9 | `recover` | `RecoveryCoordinator.recover()` | workers_ready, compensation, outbox, projection rebuild |
| H10 | `host.ready` | emit STARTED; `_started = True` | |
| H11 | `background.work_drain` | optional `workplane.start_background()` | composition **or** deployment OR (BI-006) |

### H4 spawn detail (`RuntimeSpawner`)

| Deployment | Runtimes created | Scheduler default |
|------------|------------------|-------------------|
| collapsed / all_in_one | `main` embedded | inline |
| master | `command` embedded | inline |
| worker (no server) | `worker`, `worker-N` daemon | queued |
| server | `server` ServerRuntime | queued; `http=False` at spawn (HTTP in H7) |

Each created runtime with `autostart=True` runs the **full system schedule** before host continues.

### H6 product wire detail (`_wire_cqrs`)

1. `wire_command_bus`  
2. If DNA `has_capability("projections")`: host slots alias the install organ + pattern extras + `wire_query_bus`; else `wire_standalone_query_bus` on primary  
3. `core_service_registry().build_all(..., only=composition.services)`  
4. Assign system/session/definitions/execution/assist/design/analytics  
5. assist↔analytics bind; dashboard store; workplane: work_drain, journal, inbound  
6. design contributors; `wire_all_service_cqrs`

**Membership already partial truth:** `composition.services` and several `composition.has(...)` gates.  
**Still OR soup:** work_drain background (H11), outbox activation (composition + deployment + profile flags).

---

## 4. System schedule (today — imperative)

Source: `BaseRuntime.start` (`palm.system.runtime.base`).

| # | Provisional id | What runs | Notes |
|---|----------------|-----------|--------|
| S1 | `plugins.ensure` | `plugin_install` when `composition_packages` is set | No key: install nothing. The system phase does not import the stroke. The standard host passes `ensure_core_plugins` |
| S2 | `engines.core` | context, event initialize | |
| S3 | `engines.resource` | resource.initialize (+ cache options) | |
| S4 | `engines.workload` | `initialize_workload_engine` | host runner opt-in via options |
| S5 | `engines.auth` | auth.initialize + authenticate_runtime | |
| S6 | `storage.select` | StorageFactory if not initialized | default memory |
| S7 | `events.outbox` | OutboxStore + wire_reliable_events if enabled | |
| S8 | `hooks.install` | build job hooks list | observability, auth, persist, session ownership, outbox drain, snapshots |
| S9 | `orch.init` | orchestration.initialize(scheduler, hooks, …) | |
| S10 | `bt.init` | behavior_tree.initialize | |
| S11 | `instances.init` | instance_manager.initialize | |
| S12 | `orch.start` | orchestration.start() | accepts jobs |
| S13 | `plane.wait` | WaitPlaneService attach | continue law |
| S14 | `plane.session` | SessionPlaneService attach + ensure_host_session | outside subject |
| S15 | `system.ready` | `_started = True`; optional palm provider bind | |

**Not in system schedule today:**

- Work **start** drain / WorkIntent — **host** workplane (H6).  
- Product services / CQRS — **host** (H6).  
- Surfaces — **host** (H7) or ServerRuntime HTTP.  
- Projection rebuild — **host** recover (H9).

**Ports:** `ExecutionPort` is structural on BaseRuntime (live after engines exist). No separate “open ports” step yet (future S3-style phase may name it).

---

## 5. Axes today (what controls what)

| Axis | Controls today | Gap |
|------|----------------|-----|
| **CompositionProfile.services** | Which services `build_all` builds | Membership truth (0.59.5) |
| **CompositionProfile.surfaces** | Mount when `deployment.server` **and** non-empty surfaces; factory `only=` filters | BI-010 residual chrome |
| **CompositionProfile.capabilities** | Sole runtime gate for projections, compensation, journal, work_drain background, … | Outbox still available×activated (role) |
| **DeploymentProfile** | Which runtimes spawn; server host/port; outbox service activation; worker count | True role axis |
| **PalmSettings** | storage, flags → composition capabilities via resolver; runtime_start_options | Triple override risk (BI-009) |
| **start(**options)** | Merged into system start | Can fight settings |

---

## 6. Double plugin ensure

```text
Host H1: ensure_core_plugins()
System S1: ensure_core_plugins()  # no-op if already loaded
Tests: conftest import-time ensure_core_plugins()
```

Idempotent (`_loaded` flag). Not wrong — but **order dependency** if something assumes plugins only after S1.

---

## 7. Theme expectations (locked for 0.59)

### 7.1 Green bar (theme-wide)

| Track | Expectation |
|-------|-------------|
| **Spine host** | Collapsed `ApplicationHost` with test settings: start → submit/continue path available; session plane + wait plane present |
| **Spine system** | `BaseRuntime`/`EmbeddedRuntime` start alone: plugins, storage, wait, session, orchestration |
| **Declared modes** | **`safe`/`test` ✅ 0.59.6** + **shapes ✅ 0.59.7** + default fixture **`all_in_one` ✅ 0.59.8** |
| **Legacy dual roots / heavy surfaces** | May fail mid-theme; BI-* required; not spine |

**0.59.1 green bar:** characterization tests in `tests/test_boot_inventory_0_59.py` + existing host tests remain green.  
**0.59.6 green bar:** `tests/test_mode_dogfood_0_59_6.py` — safe + test phenotype, log levels, spine.  
**0.59.7 green bar:** `tests/test_shape_dogfood_0_59_7.py` — dev/prod + shapes phenotype; collapsed spine SUCCEEDED; queued shapes accept submit.  
**0.59.8 residual:** conftest `host` → `for_mode("all_in_one")`; dead `options={"name":"quick"}` DAGs → `tests/helpers/flows.py` spine wizard.

### 7.2 End of theme (reminder)

- Phase tables walk in code.  
- `safe`/`test` ✅ + full modes/shapes dogfood ✅ 0.59.7.  
- Membership truth on migrated path.  
- Residual chrome named.

### 7.3 Break / harvest (reminder)

If a later slice breaks a path: classify → harvest rule → BI-* → do not restore import-order magic.  
Spine regressions fix in-slice.

---

## 8. Target phase mapping (spirit → today’s steps)

| Future spirit (VISION) | Maps from today |
|------------------------|-----------------|
| Host: bootstrap | H1 |
| Host: host event | H2–H3 |
| Host: spawn system | H4 → system schedule |
| Host: definitions | H5 |
| Host: product services | H6 (services part) |
| Host: surfaces | H7 (+ composition.surfaces truth later) |
| Host: projections/outbox | H6 (host slot alias) + H9 recover rebuild |
| Host: recover/drain | H9 + H11 |
| System: plugins | S1 |
| System: engines/storage | S2–S6 |
| System: ports open | implicit (name later) |
| System: planes | S13–S14 (+ workload init S4) |
| System: job hooks | S8–S9 |
| System: orch start / ready | S12, S15 |

**Locked in code:** `palm.system.boot` — `HOST_PHASES` / `SYSTEM_PHASES`.  
**System (0.59.3):** all `SYSTEM_PHASES` walked by `BaseRuntime.start` (`system_schedule`).  
**Host (0.59.4):** all `HOST_PHASES` walked by `ApplicationHost.start` (`palm.app.host.boot.host_schedule`).  
**Membership (0.59.5):** composition sole switch; deployment feeds settings resolver only; PhaseSkip `composition_off:*`.

---

## 9. Known lies / smells (feed BI-*)

| Id | Smell |
|----|--------|
| BI-001 | Two schedules: tables locked 0.59.2; full walk still 0.59.3–.4 |
| BI-002 | Membership truth paid 0.59.5 (residual surface chrome BI-010) |
| BI-003 | ServerContext host-less path has no host schedule |
| BI-004 | Plugin ensure appears host + system + tests |
| BI-005 | Job hooks built as inline list in S8 |
| BI-006 | work_drain background OR composition/deployment |
| BI-007 | Tests use many host shapes without mode names (modes exist; not yet forced) |
| BI-008 | Doctor `control_plane.boot` reports tables + mode (0.59.2) |
| BI-009 | settings / profile / start options triple |
| BI-010 | Surface mount ≠ composition.surfaces alone |
| — | Work **start** plane lives on **host**, not system schedule (law may stay; must be **named**) |
| — | Session host session ensure swallows Exception (silent) |

---

## 10. Characterization tests

| File | Pins |
|------|------|
| `tests/test_boot_inventory_0_59.py` | Host start collaborator order; system post-start contracts; spine services; dual ensure idempotent |
| `tests/test_boot_schedule_0_59_2.py` | Locked tables; walker skip honesty; modes; early log seats; doctor boot |
| Existing `tests/test_application_host.py` | Deployment spawn shapes |
| Existing composition / status tests | Profile presets; status reports |

Walker dry-run and early seats are pinned. Full start cutover updates inventory tests in 0.59.3–.4.

---

## 11. How to update this file

- After inventory-changing slices: refresh tables from code.  
- When phase ids freeze in code: mark provisional → **locked**.  
- Do not invent phases that do not exist yet without a stub seat row.  
- Link new BI rows here when discovery adds them.

---

*Name what boots. Then walk it on purpose.*
