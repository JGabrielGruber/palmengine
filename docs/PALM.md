# Palm — System definition

**Status:** Canonical high-level definition.  
**Language:** ASD-STE100 Simplified Technical English (project rule from 0.57).  
**Role:** This file is the **map of Palm as a whole**. Use it first.  
**Detail:** Link out. Do not replace this map with a second full copy.

**Related:** [architecture/](architecture/README.md) (**intended architecture** · C4 SE vault) · [VISION-0.62](vision/closed/VISION-0.62.md) (multi-claimer capacity **closed** `0.62.8`) · [ADR-031](adr/031-multi-claimer-work-drain.md) **Accepted** · [VISION-0.61](vision/closed/VISION-0.61.md) (vitality **closed** `0.61.13`) · [ADR-030](adr/030-system-vitality.md) **Accepted** · [VISION-0.60](vision/closed/VISION-0.60.md) (supervisor + work plane **closed**) · [ADR-029](adr/029-system-supervisor.md) **Accepted** · [VISION-0.59](vision/closed/VISION-0.59.md) (boot **closed**) · [ADR-028](adr/028-system-boot.md) **Accepted** · [VISION-0.58](vision/closed/VISION-0.58.md) (session **closed**) · [ADR-027](adr/027-session-plane.md) **Accepted** · [VISION-0.64](vision/closed/VISION-0.64.md) (**closed**) · [VISION-0.63](vision/closed/VISION-0.63.md) (assembly **closed**) · [ADR-032](adr/032-organism-assembly.md) **Accepted** · [VISION-ASSEMBLY](vision/VISION-ASSEMBLY.md) (seed law) · [VISION-0.66](vision/closed/VISION-0.66.md) (**closed**) · [VISION-0.67](vision/closed/VISION-0.67.md) (**closed**) · [VISION-0.68](vision/closed/VISION-0.68.md) (**closed**) · [VISION-0.69](vision/closed/VISION-0.69.md) (**closed** Navigator) · [ADR-037](adr/037-navigator-invert.md) **Accepted** · seed [VISION-NAVIGATOR](vision/VISION-NAVIGATOR.md) · [VISION-SURFACE-DEFLATION](vision/VISION-SURFACE-DEFLATION.md) (queue) · [VISION-TINY-LLM](vision/VISION-TINY-LLM.md) (queue) · [VISION-VITALITY](vision/closed/VISION-VITALITY.md) (seed essay) · [VISION-0.57](vision/closed/VISION-0.57.md) · [ADR-026](adr/026-palm-system-layer.md) · [WRITING.md](WRITING.md) · [VISION-GROVE](vision/VISION-GROVE.md) · [AGENTS.md](../AGENTS.md) (mode router) · [src/palm/AGENTS.md](../src/palm/AGENTS.md) (development) · [architecture/AGENTS.md](architecture/AGENTS.md) (intended architecture) · [ARCHITECTURE.md](../ARCHITECTURE.md) · [STATUS.md](../STATUS.md)

---

## 1. What Palm is

Palm is an **orchestration engine**.

Palm coordinates **work** that must stay **honest**:

- A **definition** says what work may do.
- A **job** is one run of that work.
- An **instance** is the durable record of that run.
- **State** lives on a pluggable blackboard.
- **Control flow** is a **Behavior Tree** (BT), not hidden callbacks.

A person or an agent may:

- start work,
- answer questions mid-flight,
- step back,
- pause and resume later,
- inspect what waits and why.

Palm is **not** only a REST API.  
Palm is **not** only a wizard product.  
Palm is **not** a container platform that happens to run Python.

Palm is a **system**: pure machines, a running kernel shape, plugins, product façades, and thin surfaces.

### 1.1 Operating-system picture

Use this picture to place every new piece:

| OS idea | Palm idea |
|---------|-----------|
| Hardware / ISA | **Core** — pure engines and contracts |
| Kernel | **System** — one running Palm: engines bound, **ports** open, **planes** live |
| Drivers | **Plugins** — patterns, providers, runners, storages |
| Shared libraries | **Shared** — reusable glue that is not the system |
| User programs | **Product** — services for operators and agents |
| Terminals / sockets | **Surfaces** — CLI, HTTP, MCP, WebSocket, … |
| Boot image | **App host** + composition / deployment profiles |
| Files / records | **Definitions** and **instances** |

If a piece has no home in this table, the design is incomplete. Name the home before you add the piece.

---

## 2. What Palm is for

| Aim | Meaning |
|-----|---------|
| **Human-first** | Wizards, choices, backtrack, resume after interruption |
| **Truth-seeking** | Explicit job status, durable instances, visible failures |
| **Agent-operable** | Assist and MCP drive the same work path as a human |
| **Extensible** | New capability by **registry**, not by editing core contracts (Open/Closed · dependency inversion). Law: [architecture principles §6](architecture/principles.md). |
| **Seat DI** | Inject **interfaces** and **subsystems**; do not inject the system instance as ambient DI |
| **Local maturity, Grove horizon** | One Palm is complete; many Palms talk later by the same laws |

Palm optimizes for **long clarity**, not for short cleverness.

**Extension shape:** put participation **law** in a **definition at the edge**.  
Consumers (subsystems, schedule, walk, product door) **hold and run** members.  
They do not grow a private menu of concretes.  
When you touch old open-coded menus, move them toward that shape when the touch is natural.

**DI shape:** the system instance is a **shell** that owns seats.  
Call sites take the seat they need (`execution`, `install`, planes, supervisor).  
Surfaces depend on system; system does not depend on surfaces.

---

## 3. Primary concepts

These words are **stable**. Use them with one meaning only.

| Concept | Meaning |
|---------|---------|
| **Definition** | Declared contract of work (flow, process, resource, …). Versionable. Also: participation law at the edge. |
| **Pattern** | How a flow shape runs (wizard, parallel, pipeline, dag, …). Plugin. |
| **Behavior Tree (BT)** | Control-flow model: nodes tick; composition is explicit. |
| **Job** | Live unit of execution under the orchestration engine. |
| **Instance** | Durable process record for one definition run; survives restart when storage is shared. |
| **Session** | Outside subject (system plane): one coherent external walk; may own **many** instances. Not who the person is. |
| **Principal** | Who is walking (identity). Not the walk. Not admission. |
| **User plane** | Later identity policy (entry, visibility, impersonation, grants) over principal ↔ session. Does not own jobs. Seed: [ADR-027](adr/027-session-plane.md) D11 · [VISION-NAVIGATOR](vision/VISION-NAVIGATOR.md) (seam named; not Navigator floor). |
| **State** | Blackboard data for the run (`BaseState` and schemas). |
| **Resource** | Named way to **speak** to an external or internal system (provider + action). |
| **Provider** | Plugin that implements resource speak. (Not a DI “provider.”) |
| **Workload** | Isolated **place** for foreign work (run or long service). Entry in the **place registry**. Not “just another resource.” |
| **Place registry** | Named places Palm may mean (spawn or adopt); lifecycle + readiness. Workload plane is the home of this registry. (Vision still says place book.) |
| **Runner** | Plugin that implements a workload runtime (host, neonroot, …). |
| **Event** | Signal on a bus. Completers describe themselves. |
| **Interest** | Explicit want: **start** (trigger) or **continue** (wait). |
| **Interface** | Named contract on the system shell that others call (`execution`, `install`, and later assembly admission / structure effects). Code may still say **port**. |
| **Subsystem** | Membership + lifecycle region on the shell (planes, supervisor). Under assembly: organ with a **subsystem contract**. |
| **Shell** | System instance that owns interfaces and subsystems. Not the default call argument. |
| **InstallInterface** | Living collaborator board for subsystem install (peer of execution). |
| **Port** | Named interface for **effects** or **admission** the system may perform or expose. |
| **Plane** | System path for one kind of traffic (event, start, continue, session, …). |
| **Surface** | Transport only. |
| **Product** | Operator/agent domain API (policy + envelope). **Client** of the system: depends on published ports, not the composition root. |
| **System** | Running Palm that holds engines and exposes ports. |
| **Shared** | Code reused by many layers that is not system and not product. |
| **Composition root** | Host wiring. Not product’s path to structure or readiness. |
| **Truth home** | Place that is **authoritative** for durable meaning this process projects. |
| **Projection** | Local view of authoritative state. Not a second source of truth. (Not a CQRS product board.) |
| **Control home** | Who assigns work and whose doors this process uses for control. |
| **Light center** | Role rule: refuse heavy body and/or ground on purpose; place weight; stay efficient. |
| **Support place** | Place that holds ground (or weight) another node projects from. **Org / realm** are recursive supports when they have children of the same kind. |
| **Work place** | Place that executes work a light center will not carry. |
| **Authority** | Author of desired structure (publishes structure definition). |
| **Structure definition** | Declarative desired structure for this process. Code: `StructureDefinition` / `structure_definition_id`. Vision still says **assembly definition**. |
| **Structure reconciler** | Desired-state **reconciler** for **organism ready** (after boot, before business pretends). Code: `StructureEngine` (`palm.core.structure`) + manager (`palm.system.structure`). Vision still says **assembly** — [VISION-ASSEMBLY](vision/VISION-ASSEMBLY.md). Theme: [VISION-0.64](vision/closed/VISION-0.64.md) (closed). |
| **Structure status** | Local readiness under the current definition. Code: `StructureStatus`. Single readiness truth. Vision: assembly status. |
| **Admission** | Read gate for work that needs a true organism (definition-ready). Business-rule face — business does not talk to system lower layers. Should sit on **capability**. Sequence: [VISION-0.64](vision/closed/VISION-0.64.md). |
| **Effect intent** | Structure action the reconciler requests; system applies via `EffectPort`. |
| **Tunnel** | Trusted path between places after home is known. Seed: [VISION-TUNNELS](vision/VISION-TUNNELS.md). |
| **Vertical axis** | Authority and meaning climb the tree (home up, hop home, projection). |
| **Horizontal axis** | Bodies spread in the place registry (many hosts, workers, resources). |

---

## 4. Path of one unit of work

This path is the spine. Ports and planes exist **for** this path.

```text
1. Definition exists in the catalog
        │  (optional: Design propose → impact → commit → revision)
        ▼
2. Someone submits work
        │  product / surface / nested pattern / WorkIntent drain
        ▼
3. System materializes a pattern from the definition
        │  (BT + leaves bound to ports / engines today)
        ▼
4. Orchestration accepts a Job
        │  instance may be created or resumed
        ▼
5. Scheduler drives the job (inline or queued)
        │  BT ticks
        │  ├── ask human/agent  → wait for input
        │  ├── invoke resource  → effect (speak)
        │  ├── start workload   → effect (isolate) + optional wait
        │  ├── open wait interest → park until event matches
        │  └── transform / branch / child flow …
        ▼
6. Completer emits self-events on runtime.event
        │
        ├── Start path:  trigger matches → WorkIntent → new job
        └── Continue path: wait matches → resume or fail owner
        ▼
7. Terminal status
        │  persist instance; compensate if needed; projections update
        ▼
8. Operator or agent may inspect, resume, or design the next change
```

### 4.1 Job status (honest lifecycle)

A job moves through explicit statuses (orchestration).  
Typical shape: **pending → running → waiting → running → terminal**  
Terminal means success, failure, or cancelled — not a silent hang.

**Waiting** is first-class. Waiting may mean:

- human or agent input,
- child work,
- external signal,
- workload readiness or completion.

### 4.2 Two clients on the same spine

| Client | Role on the path |
|--------|------------------|
| **Graph (pattern / BT)** | Ticks the job. Needs fast, injectable **ports**. |
| **Operator / agent / HTTP** | Starts and drives from outside. Needs product + CQRS + **same ports**. |

Truth is the **job path**.  
Product is not a second engine.  
Raw engines as the only graph API is an incomplete contract.

---

## 5. What Palm contains

### 5.1 Core — pure machines (`palm.core`)

Core has **no** imports from other Palm packages.

| Engine / area | Purpose |
|---------------|---------|
| **BehaviorTreeEngine** | Run BT nodes and patterns |
| **OrchestrationEngine** | Job lifecycle, drive, hooks, results · membership `RLock` · exclusive drive per job (0.62) |
| **ContextEngine** | Scopes and state wiring |
| **StorageEngine** | Persistence backend coordination |
| **ResourceEngine** | Invoke providers (speak) |
| **EventEngine** | In-process event bus |
| **AuthEngine** | Auth primitives and principals |
| **TransformEngine** | Data transform rules |
| **Wait** (types) | Pure continue-interest vocabulary |
| **Work** (types) | Pure start-plane intent types |
| **WorkloadEngine** | Pure workload lifecycle (place / exec / status / stop) |

Core also holds **registries** (pattern, provider, storage, …) as pure registration points.  
Higher layers **register downward** into them.

### 5.2 Definitions and instances

| Package | Purpose |
|---------|---------|
| **`palm.definitions`** | Flow, process, resource, schema, dashboard contracts |
| **`palm.instances`** | Durable process instance, snapshots, status history |

Definitions may **revise** (append-only history).  
Instances **pin** a revision and hold resume state.  
**Design** (product) proposes and commits definition change. It does not replace the catalog.

### 5.3 Plugins — register, do not fork core

| Plugin family | Purpose | Package |
|---------------|---------|---------|
| **Patterns** | Control-flow shapes (wizard, parallel, pipeline, dag, …) | `palm.patterns` |
| **Providers** | Speak backends (rest, kv, file, palm, neonroot-as-provider legacy, …) | `palm.providers` |
| **Runners** | Workload isolation backends (host, neonroot, …) | `palm.runners` |
| **Storages** | Storage backends (memory, filesystem, postgres, …) | `palm.storages` |

Patterns, providers, and storages follow an **app + registry** layout.  
Runners autoload packages into `workload_runtime_registry`.  
Capability is added at the edge. Core contracts stay stable.

**Flagship pattern today:** **wizard** — interactive steps, validation, backtrack, commit, resource and workload leaves.  
Other patterns exist at different maturity. Maturity is not the same as purpose.

**Turn invert (Navigator, locked):** `palm.kits.present` walks. The pattern fills `JobInspectable` / `InputCapable` (and wait plane). The kit does not switch on pattern name.

**Kit-as-composition (Navigator, locked):** that kit is one library object that holds `BoundSurface` and composes `SessionService` + execution. Not a product service. As-built `0.69.4`: `palm.kits.present.bind(host)` walks bind / present / submit / start / attach / focus. Handle class unnamed.

**Pack (Navigator, locked):** wizard **`navigator`** beside `operator_entry` (`examples/definitions/navigator.py`). Same-session sibling start; guidance stays waiting; return is `focus` of **`guidance_instance_id`**. As-built `0.69.6`. Leftover `operator_entry` still ends. Floor dogfood as-built `0.69.7`: empty-handed start of **`navigator`** on `CompositionProfile.embedded()` (no Assist).

**`guidance_instance_id` (Navigator, locked):** session **metadata** key — which attached instance is this walk’s operator-guidance run. Present kit owns the string (`0.69.8`). Not continue focus. Not kit RAM. Not root. Not a `SessionRecord` field in the floor.

**Walk writes (Navigator, locked):** session-context writes go through a **system interface** (`SessionService` door, plane store). Floor degenerate. As-built `0.69.8`: `SessionService.stamp` / `replace` take a named instance-id key. Present kit owns **`guidance_instance_id`**. Interface type unnamed. User plane later installs. Not a product domain.

**Job is session-ignorant (Navigator, locked):** the job does not know the walk. Attach is a session write after start, not `session_id` on job metadata. As-built `0.69.2`: `SessionService.attach_after_start`. Leftover hook still reads job metadata.

**Dashboard model (Navigator, locked):** guidance job is a staying chooser shell (operator wait). Spawned work is session-owned peers, not wait-plane targets of home. As-built `0.69.3`: `FlowExecutionService.spawn_sibling`. As-built `0.69.4`: kit `start()` walks that door; kit `focus` among owned instances. Leftover `until_input` nested park stays.

**Kit-contributed settings (Navigator, locked):** kits extend process config. Present owns **`guidance_definition_id`** (`str | None`). As-built `0.69.5`: unset default; empty-handed `start()` uses the key (by id). Not a field on core `PalmSettings`. As-built `0.69.7`: dogfood sets the key after bind (`"navigator"`). Constructor override and env spelling stay later.

**Stamp caller (Navigator, locked):** present kit asks `SessionService.stamp` with its walk-role key after attach if the started definition is that chooser. As-built `0.69.5` caller · `0.69.8` key on the kit. Attach does not stamp.

**Replace predicate (Navigator, locked):** kit asks; instance attached; definition id equals `guidance_definition_id`. As-built `0.69.5`. Titles cannot become Home. [VISION-NAVIGATOR](vision/VISION-NAVIGATOR.md) §5.

### 5.4 System — the running Palm

**Purpose:** Hold engines for **one** started runtime, expose **ports**, run **planes**, accept definition-driven jobs.

**Today (honest):** This role is **split**:

| Piece | Holds |
|-------|--------|
| **`BaseRuntime`** | Engines, start wiring, executor, wait plane attach, outbox hooks |
| **`palm.system`** | Wait plane service, work drain, workload bootstrap, runtime hooks, definition executor |
| **`palm.common`** | Still fat. Lazy-exports system types. Not the home of wait/work/workload/runtime hooks/`DefinitionExecutor`. |
| **`RuntimeHost` protocol** | Incomplete: orchestration + event + resource only |
| **`PalmKernel`** | Storage, instance manager, **runtime registry** — multi-runtime infra, not the effect port table |

**Target:** One clear **system** boundary. Same purpose. Cleaner home. Named ports.

#### Ports

A **port** is a named effect surface.  
Graphs and product both bind ports.

| Effect family | Meaning | Notes |
|---------------|---------|--------|
| **Resource / speak** | Invoke provider actions | Dual path today (leaf → engine; service → engine) |
| **Workload / isolate** | Start, exec, stop, status | Scouted in 0.56; must share the port model |
| **Job / drive** | Submit, drive, input, inspect as system allows | Orchestration-facing; keep explicit |

A port is **not** CQRS alone.  
A port is **not** one engine class name as the public graph contract.  
A port is **not** “everything is a flow.”

#### Planes

A **plane** is system traffic of one kind.

| Plane | Verb / role | Home (intent) |
|-------|-------------|----------------|
| **Event** | Signals; completers speak of self | `runtime.event` (orchestration bus) |
| **Work (start)** | Trigger → WorkIntent → new job | **0.60 closed:** `runtime.work_plane` + session attr + inbound under `planes.work` · continuous services on **supervisor** — [VISION-0.60](vision/closed/VISION-0.60.md) · [ADR-029](adr/029-system-supervisor.md) Accepted. |
| **Wait (continue)** | Interest → resume or fail parked work | Wait plane on system (`runtime.wait_plane`) |
| **Session** (0.58 **closed**) | Outside subject + service attribution + surface context | System `planes.session`: bind; exclusive attach; **active focus**; **owner gate**; **strict attribution**; **inherit-or-service** reactive start. **Product** `SessionService` / kit `resolve_session_service` is the surface door. **BoundSurface**. **Operate:** focus / list waiting / cancel-owned. **Vocabulary:** `session_id` = system subject (`sess-…`); `instance_id` = continue; path segment `instance`. Navigator walk fact **`guidance_instance_id`** (kit-owned key `0.69.8`; stamp/replace `0.69.1`; kit caller `0.69.5`). Floor attach after start: **`SessionService.attach_after_start`** (`0.69.2`; job stays session-ignorant). Session metadata ≠ job metadata. Active ≠ foreign pass. Active ≠ guidance. Plane remains law. Theme: [VISION-0.58](vision/closed/VISION-0.58.md) · [ADR-027](adr/027-session-plane.md) Accepted. Surface compost residual: [VISION-SURFACE-DEFLATION](vision/VISION-SURFACE-DEFLATION.md). |
| **Workload** | Isolation lifecycle events and placement | Workload engine + runners |

**Supervisor** (0.60 **closed**): not a plane. Continuous system services (work drain, outbox, inbound workers) live under **`SystemSupervisor`** on the system instance. Planes carry traffic; supervisor runs loops. See [VISION-0.60](vision/closed/VISION-0.60.md) · [ADR-029](adr/029-system-supervisor.md) Accepted.

**Host bus** (`host.event`) is for host coordination (start, shutdown, outbox process).  
**Do not** put job lifecycle only on the host bus. See [EVENT-PLANE](EVENT-PLANE.md).

#### Reactive law (start and continue)

1. Completers emit **self-events**.  
2. Palm matches **interest**.  
3. **Start** creates or enqueues work.  
4. **Continue** resumes work that already exists.  
5. Same bus may feed both verbs. Verbs stay distinct.

This law is **system law**. It is not a feature flag.  
Detail: [VISION-GROVE](vision/VISION-GROVE.md) §4 · [ADR-025](adr/025-reactive-interests.md).

### 5.5 Shared — not the system dump

**Purpose:** Reusable coordination and libraries that:

- many layers need,
- are not a product domain,
- are not the running kernel itself.

**Examples of true shared work:** transform rule packs, schema helpers, persistence repositories used by system and product, CQRS bus **primitives**, small operator view helpers.

**Today (honest):** wait, work, workload, runtime hooks, and `DefinitionExecutor` live under **`palm.system`**, not `palm.common`. `palm.common` is still fat and still lazy-exports system types. That mix remains structural debt.

| In common today | Likely class |
|-----------------|--------------|
| Lazy-export of system types | **System** (home is `palm.system`) |
| Transform builtins, some resolvers | **Shared** |
| CQRS buses | **Shared primitive**; wiring is host/product |
| Operator presenters | **Shared support** for product/surfaces — watch bulk |
| Full product domains | **Must not** live here |

**Rule:** If you do not know where code goes, do not put it in shared by default. Name system, product, or plugin first.

### 5.6 Product — userland (`palm.services`)

**Purpose:** Domains for operators and agents.  
Policy, validation, envelopes, CQRS contributors.  
Then call **system ports** (target). Today many paths call engines on a resolved runtime.

| Domain | Purpose |
|--------|---------|
| **Definitions** | Catalog read/write of definitions |
| **Design** | Propose → impact → commit definition change |
| **Execution** | Run flows, processes, provider invoke, workloads |
| **Assist** | As-built operator conversation (discover, drive, present). Intended: guidance is a **catalog definition** that **stays** as session home; present/bind is **`palm.kits.present`** (**turn invert:** kit walks, pattern fills inspect/input). First adapter: **embedded library surface**. Entry and visibility are later **principal / user-plane**. Theme: [VISION-0.69](vision/closed/VISION-0.69.md) (**closed**). Seed: [VISION-NAVIGATOR](vision/VISION-NAVIGATOR.md). Compost: [VISION-SURFACE-DEFLATION](vision/VISION-SURFACE-DEFLATION.md). |
| **Inspect** (product door) | Doctor / top / list / cancel present — **not** the kernel layer (**SD-007** paid 0.61.4) |
| **Analytics** | Datasets and dashboards |

**Name law (tell the truth):**  
Product package **`palm.services.inspect` / `InspectService`** is the operator present door.  
**System layer** in this map is the **kernel shape** (`palm.system`).  
Supervisor continuous loops keep protocol name **`SystemService`** under `palm.system.subsystems.supervisor` — different concept.  
Import/host aliases (`palm.services.system`, `host.system`) are temporary migration only.

**CQRS** is how many edges ask product.  
CQRS is transport and schema discipline.  
CQRS is not the definition of all Palm power.

### 5.7 Surfaces (`palm.runtimes`)

**Purpose:** Map a wire protocol to product (or a controlled system entry).  
Stay thin.

| Surface family | Examples |
|----------------|----------|
| Embedded | In-process library surface. First **`palm.kits.present`** adapter (named). `EmbeddedRuntime` is the engine, not the adapter. Phenotype `CompositionProfile.embedded()`. [VISION-NAVIGATOR](vision/VISION-NAVIGATOR.md). |
| Daemon | Long-lived worker |
| Server | HTTP, Explorer SSR, WebSocket assist |
| CLI | Stdio / REPL surface (command forest is compost — [VISION-NAVIGATOR](vision/VISION-NAVIGATOR.md)) |
| MCP | Agent tools and resources |

Surfaces must not invent a second semantic model.

### 5.8 App host (`palm.app`) and boot

**Purpose:** Compose a **phenotype** of Palm and boot it.

| Piece | Role |
|-------|------|
| **PalmKernel** | Infra: shared storage, instance manager, runtime registry |
| **ApplicationHost** | Composition root: roles, CQRS wiring, recovery, service façades, workers |
| **CompositionProfile** | Membership: services, surfaces, capabilities (*what*) |
| **DeploymentProfile** | Roles and deployment activation (*where*) |
| **Boot schedule + mode** | Order and strictness (*how start runs*) — **0.59 closed** |
| **System log** | Ordered narrative of system life (observation) — [SYSTEM-LOG](SYSTEM-LOG.md) |
| **Settings** | Configuration resolver into the axes above |

The host is **not** a second port table.  
The host **wires** system instances and product.

#### Boot (0.59 closed)

| Level | Status |
|-------|--------|
| **System schedule** | **Walked** — `BaseRuntime.start` → `SYSTEM_PHASES` + boot handlers |
| **Host schedule** | **Walked** — `ApplicationHost.start` → `HOST_PHASES` + host boot handlers |
| **Membership** | **Truth on migrated path** — profile sole switch; PhaseSkip reasons; deployment feeds resolver only |
| **Modes** | `BootMode` + `for_mode` dogfood (safe/test + shapes); residual suite force **BI-007** |
| **System log** | Seats live — [SYSTEM-LOG](SYSTEM-LOG.md); richer catalog residual **BI-015** |

**Law:** plugins stay on `INSTALLED_*`. Planes are **not** plugins.  
**Law:** one composition root walks the host phase table — no private boot via import side effects.  
**Law:** system log is **observation**; event buses remain **reaction**; EventJournal remains **durable domain facts**.  
**Theme closed:** [VISION-0.59](vision/closed/VISION-0.59.md) · [ADR-028](adr/028-system-boot.md) **Accepted** · [SD-014](../TECH-DEBT.md#sd-014) ✅ · residual **BI-*** · [RELEASE-0.59.8](releases/RELEASE-0.59.8.md).

### 5.9 Reliability and truth aids

These are part of Palm’s honesty, not optional polish:

| Aid | Role |
|-----|------|
| **Instance persistence** | Resume after restart |
| **State snapshots** | Bounded history for inspect (optional) |
| **Outbox** | Reliable event publication |
| **Compensation** | Undo on failed commit paths where registered |
| **Projections** | Read models for status and dashboards |
| **Doctor** | Health and registry visibility |

---

## 6. Layers — purpose table

Each top-level part has **one purpose**.

| Layer | Purpose (one sentence) | Must not |
|-------|------------------------|----------|
| **Core** | Pure engines and contracts | Import outside `palm.core` |
| **System** | Running Palm: bind engines, ports, planes | Be a product domain or a surface |
| **Shared** | Reusable non-system, non-product glue | Absorb “no home” code |
| **Plugins** | Extend by registry | Own host lifecycle or product envelopes |
| **Product** | Operator/agent domains over ports | Hold engines as the public truth |
| **Surfaces** | Transport adapters | Call engine class names as policy |
| **App host** | Boot and compose phenotypes | Replace system ports |
| **Definitions / instances** | Contracts and durable records | Execute effects |

### 6.1 Names (current truth)

| Name | Role now | Residual |
|------|----------|----------|
| `PalmKernel` | Infra: storage + system-instance registry | Not the effect API |
| `BaseRuntime` | **System instance** under `palm.system.runtime` | Import from `palm.system` |
| `RuntimeHost` | Thin legacy protocol for executions | Prefer `SystemInstance` + ports |
| `PatternBuildContext` | Carries `execution` port (+ engines for unit tests) | Engine fields for tests only |
| `ExecutionService.*` | Product over **ports** for effects | list/doctor residual |
| `palm.system` | System home: runtime, planes, ports | — |
| `palm.common` | Shared libraries (plans, CQRS, transforms, …) | — |
| `palm.kits` | Surface kits (`server`, **`present`**, …). **`palm.kits.present`** as-built `0.69.4` (**turn invert** + **kit-as-composition**); `0.69.5` owns **`guidance_definition_id`** and is the stamp/replace caller. Handle class unnamed. Theme: [VISION-0.69](vision/closed/VISION-0.69.md) (**closed**). Seed: [VISION-NAVIGATOR](vision/VISION-NAVIGATOR.md). | SD-011 ✅ |
| `services.inspect` | Operator present **product** (`InspectService`) | Do not call it the kernel; not supervisor `SystemService` |

---

## 7. How Palm grows

| You want to add… | You add it as… |
|------------------|----------------|
| New pure algorithm or engine | **Core** |
| New effect family | **System port** (+ core engine if pure) |
| New isolation backend | **Runner** plugin |
| New speak backend | **Provider** plugin |
| New control-flow shape | **Pattern** plugin |
| New storage backend | **Storage** plugin |
| New operator domain | **Product** service + CQRS |
| New transport | **Surface** |
| New deployment shape | **Composition / deployment profile** |
| New boot mode or phase | **Boot schedule** (host or system) — not import-order side effects ([VISION-0.59](vision/closed/VISION-0.59.md)) |
| New event reaction | **Trigger or wait interest** on the event plane — not a private hook web |

**Growth rule:** extend **kinds** and **registries**.  
Do not invent a second integration grammar.

**Registry extension (aim):**

| Do | Do not |
|----|--------|
| Register a definition; core walks the registry | Edit hub / schedule / vitality with a new concrete branch |
| Keep install and observe law next to the subject | Relocate the same closed list and call it architecture |
| Boy-scout open menus when you touch them | Leave dual truth because “only a small switch” |

---

## 8. Scale: two axes · recursion · horizon path

This section **updates older scale talk**. It does not replace the job path (§4) or planes (§5).  
It names how Palm grows past one process **without** a second soul.

### 8.1 Two axes (always together)

| Axis | What it is | Home of the law |
|------|------------|-----------------|
| **Vertical** | Authority and meaning. Home points **up**. Truth home, projection, hop home, light center, recursive support. | [VISION-ASSEMBLY](vision/VISION-ASSEMBLY.md) · this map |
| **Horizontal** | Bodies and capacity. Place registry: spawn or adopt; readiness; many hosts. | Workload ([VISION-0.56](vision/VISION-0.56.md)) |

**Horizontal placement. Vertical ownership.**  
Physically, workers and resources may sit side by side. Logically, meaning still climbs home.  
Children may have children; ownership of meaning still belongs under the **root** palm of that tree.

### 8.2 Recursion (org and realm are not a second product)

**Support place** holds ground another node projects from.  
When a support may have **children of the same kind**, that is organization shape:

| Name (product speech) | Scale meaning |
|-----------------------|---------------|
| **Organization** | Support (or light center over support) with an assembly definition; may project realms |
| **Realm** | Sub-support (or mid that propagates home); local ground; home still up |
| **Multi-org** | Several such supports under one root, or several independent trees |

Same genome. Recursive support. Not mesh self-discovery as first law.

### 8.3 Horizon path (tool before dream)

```text
boot (system)
  → assembly (reconcile desired structure · admission · optional structure seed)
       → business (flows)           ← living today
       → tunnels (trusted reach)    ← after assembly
            → Grove (many palms · continuous interface)
```

| Seed | Role |
|------|------|
| [VISION-ASSEMBLY](vision/VISION-ASSEMBLY.md) | Organism truth; roles; ports; definition-ready admission; vertical law |
| [VISION-0.66](vision/closed/VISION-0.66.md) | **Closed** — admission snapshot publishes installed capabilities |
| [VISION-0.67](vision/closed/VISION-0.67.md) | **Closed** — dependents require the organ (step 4) |
| [VISION-0.68](vision/closed/VISION-0.68.md) | **Closed** — the great cleansing (costume compost) · residual [SD-023](../TECH-DEBT.md#sd-023) |
| [VISION-TUNNELS](vision/VISION-TUNNELS.md) | Reach and neighborhood after home is known; mesh *feel*, tree *law* |
| [VISION-GROVE](vision/VISION-GROVE.md) | Multi-Palm organization crown; continuous interface |

**Assembly:** authority issues definition; pure engine reconciles; system applies effect intents; **admission** gates business that needs ground and publishes installed capabilities; an act that needs an organ uses `require_capability`; work-plane `able` (kernel and host start ports) is drain membership, wait stays ready; surfaces speak `capability_refused` for the organ door; schedule fire uses the same able as tick; vitality `work_cycle` drain proofs pin DNA that installs the organ; clients use ports; composition root only wires. New definition → reassemble. Theme: [VISION-0.68](vision/closed/VISION-0.68.md) (**closed**) · residual [SD-023](../TECH-DEBT.md#sd-023) · law: [VISION-ASSEMBLY](vision/VISION-ASSEMBLY.md).

**Tunnels do not own vertical/horizontal law.** They own **reach** on top of it.  
**Grove does not invent recursion.** It grows org conversation once assembly and tunnels are boring.

**This file** still defines **one Palm** as a living system.  
Grove does not replace local structure. Local structure + two axes + path above make Grove possible.

*There is no place like home.*

---

## 9. Laws

1. **One purpose per module.** If two purposes fit, split.  
2. **Core stays pure.**  
3. **Register downward.**  
4. **Registry extension.** Add peers by definition at the edge. Consumers walk registries or live membership. Do not teach consumers a private menu of concretes when a register fit exists.  
5. **The job path is the spine.** Features must say where they sit on that path.  
6. **Effects use named ports (interfaces).** Graphs and product share them.  
7. **Planes are system.** Product may expose; product does not own.  
8. **Product is userland.** Policy and envelopes, then ports.  
9. **Surfaces stay thin.** Surfaces depend on system; system does not depend on surfaces.  
10. **Shared is not a dump.** No `system.common` dump either.  
11. **Completers emit self-events.** Palm starts or continues by interest.  
12. **Waiting is first-class.** Do not hide waits in call stacks.  
13. **Definitions declare; instances remember; jobs run.**  
14. **Coherence is enforced** (guards, CI).  
15. **Break for truth before 1.0.** Record residual debt. Do not keep a structural lie for comfort.  
16. **Incomplete maps are false maps.** When structure changes, update this file in the same theme of work.  
17. **Boy-scout extension shape.** When you touch open-coded peer menus, move them toward registry extension if suitable; do not only relocate the menu.  
18. **Seat DI.** Inject interfaces and subsystems. Do not pass the system instance as ambient DI when a seat suffices.  
19. **Two axes of scale.** Vertical = home and meaning. Horizontal = place registry. Do not collapse them. Do not market multi-process without readiness and home.  
20. **Business BT ≠ organism topology.** Flows are business rules. Assembly (and later tunnels) are organism cares.  
21. **Assembly is structure reconciliation.** Desired definition + status + effect intents + admission. Not a second job orchestrator. Not host glue as architecture.  
22. **Clients use published ports.** Product and surfaces do not dig the composition root for structure or readiness. Structure effect ports stay separate from business execution.  
23. **Admission is one gate for business that needs ground.** Fail closed. Admitted paths go through the gate. The assemble path is not a business start. Dual readiness is purged or named — not a permanent checkpoint. Detail: [VISION-ASSEMBLY](vision/VISION-ASSEMBLY.md) §6.4.

---

## 10. Documentation rule

From theme **0.57** onward:

- Write new and revised project docs in **ASD-STE100** ([WRITING.md](WRITING.md)).  
- Prefer short sentences and one idea per sentence.  
- Use the **same word** for the same idea (see §3).  
- Prefer active voice and tables.  
- Do not add marketing text.  
- **Link this map.** Do not paste a second full map into AGENTS or README.

---

## 11. Where to look next

| Need | Open |
|------|------|
| **This map** | `docs/PALM.md` |
| System low-level (package, ports, moves) | [SYSTEM-LOW-LEVEL](SYSTEM-LOW-LEVEL.md) |
| Live debt (SD/SU/ST/CS) | [TECH-DEBT.md](../TECH-DEBT.md) |
| Intention stubs | [STUBS.md](STUBS.md) |
| Debt archive (PD era) | [audit/TECH-DEBT-ERA-0.45.md](audit/TECH-DEBT-ERA-0.45.md) |
| Theme plan | none open · closed [VISION-0.69](vision/closed/VISION-0.69.md) · seed [VISION-NAVIGATOR](vision/VISION-NAVIGATOR.md) |
| Structural ADR | [ADR-026](adr/026-palm-system-layer.md) |
| Start / continue law | [VISION-0.55](vision/closed/VISION-0.55.md) · [ADR-025](adr/025-reactive-interests.md) |
| Event buses | [EVENT-PLANE](EVENT-PLANE.md) |
| Start drain | [WORK-DRAIN](WORK-DRAIN.md) |
| Workload scout | [VISION-0.56](vision/VISION-0.56.md) · [ADR-024](adr/024-workload-engine.md) |
| Session plane (closed) | [VISION-0.58](vision/closed/VISION-0.58.md) · [ADR-027](adr/027-session-plane.md) Accepted · residual [VISION-SURFACE-DEFLATION](vision/VISION-SURFACE-DEFLATION.md) |
| System boot (closed) | [VISION-0.59](vision/closed/VISION-0.59.md) · [BOOT-INVENTORY](BOOT-INVENTORY.md) · [SYSTEM-LOG](SYSTEM-LOG.md) · [ADR-028](adr/028-system-boot.md) Accepted · residual **BI-*** |
| Supervisor + work plane (closed) | [VISION-0.60](vision/closed/VISION-0.60.md) · [ADR-029](adr/029-system-supervisor.md) Accepted · residual host product wire |
| System vitality (**0.61 closed**) | [VISION-0.61](vision/closed/VISION-0.61.md) · [ADR-030](adr/030-system-vitality.md) Accepted · package `palm.system.vitality` · schema `palm.seat_report/1` · inspect present · stamp `0.61.13` · seed [VISION-VITALITY](vision/closed/VISION-VITALITY.md) |
| Multi-claimer capacity (**0.62 closed**) | [VISION-0.62](vision/closed/VISION-0.62.md) · [ADR-031](adr/031-multi-claimer-work-drain.md) Accepted · exclusive claim + multi-claimer + Queued pool · stamp `0.62.8` · residual multi-process CAS [SD-019](../TECH-DEBT.md#sd-019) |
| Assembly (**0.63** closed) · first capability (**0.64** closed) · outbox proof (**0.65** closed) · admission on capabilities (**0.66** closed) · dependents (**0.67** closed) · costume (**0.68** closed) | [VISION-0.68](vision/closed/VISION-0.68.md) · [ADR-036](adr/036-require-capability.md) Accepted · seed [VISION-ASSEMBLY](vision/VISION-ASSEMBLY.md) · residual [SD-023](../TECH-DEBT.md#sd-023) · [SD-021](../TECH-DEBT.md#sd-021) |
| Tunnels (queue seed) | [VISION-TUNNELS](vision/VISION-TUNNELS.md) — reach after assembly, before Grove; not open |
| Multi-Palm horizon | [VISION-GROVE](vision/VISION-GROVE.md) — org crown; path: assembly → tunnels → Grove |
| Dense layer detail | [ARCHITECTURE.md](../ARCHITECTURE.md) |
| Agent rules | [AGENTS.md](../AGENTS.md) — points here for structure |
| Version and theme status | [STATUS.md](../STATUS.md) |
| Spirit | [PHILOSOPHY.md](../PHILOSOPHY.md) |

If a document fights this map, **this map wins** until an ADR changes it.

---

## 12. Truth about completeness

A map that only names **pain** is incomplete.  
A map that only names **ideals** without today is also incomplete.

| Area | State |
|------|--------|
| Core purity and engines | **Real and strong** |
| Definitions, instances, resume | **Real** |
| BT + orchestration job path | **Real** — spine of Palm |
| Patterns / providers / storages registries | **Real** |
| Wizard and Assist product loops | **Real** (product maturity varies by surface). Navigator invert **closed 0.69** — `palm.kits.present` on embedded; Assist stays until [VISION-SURFACE-DEFLATION](vision/VISION-SURFACE-DEFLATION.md) |
| Reactive start / continue law | **Landed** (0.55) |
| Workload plane (place registry) | **Scout** (0.56) — engine, runners, product path; multi-process **control** via named places — remainder + [VISION-ASSEMBLY](vision/VISION-ASSEMBLY.md) |
| Named system layer in packages | **Live** — `palm.system` holds shell, `interfaces/`, `subsystems/` (planes, supervisor), boot, vitality, executions (**0.57+**; seat DI **0.61**) |
| Unified execution port | **Live** — product + graphs + edges for effects and catalog inspect |
| Shared vs system split in tree | **Deflated** (0.57.6–13); kits exposed (`palm.kits.server`); plans DTO shared |
| Live debt register | **Real** — residual **BI-*** / **SU-*** / **SI-*** / **SD-019** — [TECH-DEBT.md](../TECH-DEBT.md) · [STUBS.md](STUBS.md) |
| Surface thinness | **Law** — bulk/bypass as SU-*; compost seed [VISION-SURFACE-DEFLATION](vision/VISION-SURFACE-DEFLATION.md) |
| Session plane | **Theme closed 0.58.20** — [VISION-0.58](vision/closed/VISION-0.58.md) · multi-instance system glue (not user plane) |
| Boot schedule + composition truth | **Theme closed** at `0.59.8` — [VISION-0.59](vision/closed/VISION-0.59.md) · residual **BI-*** |
| Supervisor + work plane (start) on system | **Theme closed** at `0.60.9` — [VISION-0.60](vision/closed/VISION-0.60.md) · [ADR-029](adr/029-system-supervisor.md) Accepted |
| Living-kernel vitality | **Theme closed** at `0.61.13` — `palm.system.vitality` + Inspect present — [VISION-0.61](vision/closed/VISION-0.61.md) · [ADR-030](adr/030-system-vitality.md) Accepted |
| Multi-claimer work drain | **Theme closed** at `0.62.8` — exclusive claim + drain N + exclusive drive + Queued pool — [VISION-0.62](vision/closed/VISION-0.62.md) · [ADR-031](adr/031-multi-claimer-work-drain.md) Accepted · residual [SD-019](../TECH-DEBT.md#sd-019) |
| Assembly (organism truth) | **0.63–0.68 closed** — [VISION-0.68](vision/closed/VISION-0.68.md) · seed [VISION-ASSEMBLY](vision/VISION-ASSEMBLY.md) · residual [SD-023](../TECH-DEBT.md#sd-023) |
| Grove multi-Palm | **Horizon** — tree path first; org crown later |

**Incomplete structure is stated here on purpose.**  
Hiding it would make the map a lie.  
Stating only limits without purpose would make the map a shackle. Both truths stay.

---

*Palm grows where the sun meets the sea.*  
*Name the whole tree. Then grow the branch.*
