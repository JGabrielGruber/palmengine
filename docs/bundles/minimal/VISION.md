# Minimal bundle

**Status:** Sketch. This file is the bundle note. It is not a theme plan and it does not accept an ADR.  
**Map:** [PALM.md](../../PALM.md) — read first.  
**System law:** [ADR-026](../../adr/026-palm-system-layer.md) **Accepted** · [SYSTEM-LOW-LEVEL](../../SYSTEM-LOW-LEVEL.md).  
**Open theme beside this sketch:** [VISION-0.72](../../vision/VISION-0.72.md) · [ADR-040](../../adr/040-composition-plugin-membership.md) **Proposed**. Measure **not pass**.  
**Code:** `src/bundles/minimal/`. Tests: `tests/bundles/minimal/`.

José Gabriel Gruber keeps this bundle as the place that asks how much an application must implement. The answer uses `palm.system`. It does not copy the standard host.

---

## 1. Rule for this bundle

The saved composition record and `palm.common.plugins.ensure_core_plugins` are the current standard-host workaround. They are not the composition model.

The minimal app uses a **constrained start**:

| The start sets | The start leaves out |
|----------------|----------------------|
| `storage_backend=memory` | `composition_packages` |
| `structure_definition_id=local.embedded` | `plugin_install` |
| One `BaseRuntime` subclass, inline scheduler | Product services, surfaces, host schedule |

`system.plugins.ensure` installs nothing when `composition_packages` is absent. It does not import the stroke. A mapping without a callable `plugin_install` fails closed. The standard host still passes `ensure_core_plugins`. That call stays on the standard host.

---

## 2. What the system already is

`palm.system` is the running kernel of one Palm: engines, ports, planes, the supervisor, vitality, and structure with admission. `BaseRuntime` is that instance. `start()` with no package key walks the system schedule. The default structure definition is `local.embedded` (thin body, no surfaces, empty capabilities).

Accepted law this bundle treats as fixed:

| The system owns | The bundle owns |
|-----------------|-----------------|
| System schedule, planes, supervisor, structure, admission, vitality, system log, `ExecutionPort` | Process entry, the start options above, shutdown |
| Plugin install only when the caller passes names and an installer | Whether any installer exists. This bundle passes none |
| `local.embedded` as the floor organism | Settings beyond the two start options |

Plugins are not planes. Boot mode is order. Composition installs packages. Structure enables organs and places. [ADR-028](../../adr/028-system-boot.md) · [ADR-032](../../adr/032-organism-assembly.md) · [ADR-040](../../adr/040-composition-plugin-membership.md).

The purity guard passes. `palm.system` does not import `palm.services`, patterns, or `bundles`.

---

## 3. What tests already showed

Many tests construct `BaseRuntime` and never import the standard host: assembly, supervisor, work and wait planes, vitality, place and spawn, and the system import boundary. One coherence test submits a flow on that runtime.

`tests/conftest.py` imports `ApplicationHost` and calls `ensure_plugins()` at import for tests outside `tests/core/`. A file that looks system-only still runs in a process that already installed the fat package set. The cold test under `tests/bundles/minimal/` uses a fresh interpreter.

No suite shows a useful job path under a smaller package set than the saved records. That is observable O3 in [VISION-0.72](../../vision/VISION-0.72.md). Measure stays **not pass**.

---

## 4. What stays unpaid on the system

These items are not this bundle’s job.

| Item | Home |
|------|------|
| Plugin membership as composition law | ADR-040 **Proposed**. Every saved record still names the same package set |
| A package carrier after load | Unpaid. Structure definitions are the source of truth for organs |
| Session user plane | ADR-027 residual |
| Richer system-log catalog, dual host root, ambient shell injection | BI-015, BI-003, SD-016 |
| Monitoring agent, homeostasis | Named later. Seat walk and projection shipped |
| `local.cli` and `local.server` as floor organisms | Floor organism is `local.embedded` |

Product knowledge still sits inside the system. Later refactor, not this sketch: `submit_wizard` on the shell, structure seed that reads host mode, `HOST_PHASES` declared in `palm.system`, structure hands that wire journal, projections, compensation, and analytics.

---

## 5. What this app implements

`MinimalApp` (`src/bundles/minimal/app.py`):

1. Construct `MinimalRuntime` (`BaseRuntime`, inline scheduler).
2. `start(storage_backend="memory", structure_definition_id="local.embedded")`.
3. `stop()` on the way out.

Memory storage resolves in `StorageFactory` to `plugins.storages.memory`. That import is the storage seat. It is not the plugin stroke. The living map still says `palm.storages` ([PALM.md](../../PALM.md) §5.3). The tree package is `plugins.storages`.

The standard host schedule stays the picture of a full application: system log, kernel bootstrap, host events, workers, spawn, definition load, product wire, surfaces, recovery, ready. Spawn is the phase that enters the system. This app does not walk that schedule.

---

## 6. Residuals this sketch leaves named

| Residual | Where |
|----------|--------|
| Standard runtime is still `EmbeddedRuntime` with the same two class facts | `src/bundles/standard/runtimes/embedded/runtime.py`. The kernel still builds that class |
| Fat install on the standard host, twice | Kernel bootstrap and `plugin_install` on spawn |
| Root test latch | `tests/conftest.py` calls `ensure_plugins()` |
| Map names `palm.patterns` / `palm.storages` | Code lives under `src/plugins/` and `src/bundles/` |
| `examples/todo` | Probe through `ApplicationHost`. It is not the direction of this bundle |
