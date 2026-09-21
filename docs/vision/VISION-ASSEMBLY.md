# VISION — Assembly (organism truth · tree scale)

**Status:** 📗 **Seed essay (normative law)** — [VISION-0.64](closed/VISION-0.64.md) closed · [VISION-0.63](closed/VISION-0.63.md) closed · [ADR-032](../adr/032-organism-assembly.md) **Accepted**. Named **2026-08-05** · refined **2026-08-07** · theme posture **2026-08-08** · progress honesty **2026-08-08**.  
**Language:** ASD-STE100 (practical).  
**Map:** [PALM.md](../PALM.md) · [VERSIONING.md](../VERSIONING.md) (floor · growth · exit · **José** decides)  
**Intended architecture:** [docs/architecture/](../architecture/README.md) (Palm-wide; structure management is one component).  
**Active plan:** none. Costume [VISION-0.68](closed/VISION-0.68.md) (**closed**). Dependents [VISION-0.67](closed/VISION-0.67.md) and admission face [VISION-0.66](closed/VISION-0.66.md) are **closed**. Residual [SD-023](../../TECH-DEBT.md#sd-023). This file keeps **roles · ports · citizenship · modules**.  
**Spine we keep:** [VISION-0.57](closed/VISION-0.57.md)+ system · [VISION-0.56](VISION-0.56.md) workload scout · [VISION-0.55](closed/VISION-0.55.md) reactive · [VISION-0.62](closed/VISION-0.62.md) capacity  
**Horizon order:** assembly → [VISION-TUNNELS](VISION-TUNNELS.md) → [VISION-GROVE](VISION-GROVE.md). Surface compost [VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md) may interleave.  
**Debt:** [SD-020](../../TECH-DEBT.md#sd-020) · [SD-021](../../TECH-DEBT.md#sd-021) · [SD-019](../../TECH-DEBT.md#sd-019) · [SD-016](../../TECH-DEBT.md#sd-016)

**Code now (2026-08-17).** This essay keeps **assembly**. Identifiers moved. Chronicle is not rewritten.

| This essay / 0.63 | Now in code |
|-------------------|-------------|
| DNA / `PALM_ASSEMBLY_DNA_ID` | Structure definition / `PALM_STRUCTURE_DEFINITION_ID` / `structure_definition_id` |
| `palm.core.assembly` / `palm.system.assembly` | `palm.core.structure` / `palm.system.structure` |
| `AssemblyDefinition` / `AssemblyEngine` / `AssemblyStatus` / `AssemblySeat` | `StructureDefinition` / `StructureEngine` / `StructureStatus` / `StructureSeat` · also `StructurePhase` / `StructureEngineError` / `StructureError` |
| `system.assembly.assemble` | `system.structure.assemble` |
| Shell / runtime `.assembly` | `.structure` |
| `assembly_*` options | `structure_definition` · `structure_skip` · `structure_bind_workload` · `structure_max_ticks` |
| Vitality seat `assembly` | `structure` (`SEAT_STRUCTURE`) |
| Assembly effect port | `EffectPort` |
| Household hands | `StructureEffectPort` |
| Place book | Place registry (`PlaceEffectPort` / `InProcessPlaceRegistry`) |
| Citizen / pretender inventory | `GATED_PATHS` / `READINESS_EDGES` / `open_residual_edges` |

§7 layout below is **vision shape**. Paths there stay `*/assembly/` as the essay. Code homes are the table. Glossary: [architecture/glossary.md](../architecture/glossary.md).

**Remainder.** 0.63 mapped the citizen contract. 0.64 / 0.65 did the work. **Step 3** is [VISION-0.66](closed/VISION-0.66.md) (**closed**): admission reads installed capabilities. **Step 4** is [VISION-0.67](closed/VISION-0.67.md) (**closed**): dependents require the organ. Costume is [VISION-0.68](closed/VISION-0.68.md) (**closed**). Residual [SD-023](../../TECH-DEBT.md#sd-023). Sequence: [VISION-0.64](closed/VISION-0.64.md).

---

## 0. Progress honesty (2026-08-08)

Theme work so far did real work — and it is easy to over-read it.

| Built (roughly) | Not built yet (roughly) |
|-----------------|-------------------------|
| **Readiness dashboard** — admission snapshot, fail-closed doors on many business paths, surface honest refuse, residual cartography | **Structure manager** — desired structure that **materializes** organ/place membership and only wires allowed life (essay once said “services-ish”; **code:** organs via hands — services stay `CompositionProfile`) |
| Pure reconciler + system seat + thin DNA seed map | Structure definition as organ/place **enablement law** after load (not the plugin-package install set; packages unpaid under latch @ HEAD) |
| Gate-first purge of market-day pretenders | Bootstrap/host freelancing replaced by structure plan → materialize → admit |

**Dashboard** means: we can see readiness, refuse business when admission is down, and map dual paths. That is necessary. It is **not** the full seed goal.

**Manager** means: Palm takes care of its own structure the way an OS-shaped system must — definition drives what exists; trial-and-error at the door is not the only control.

Engineering language for the target lives in the [architecture vault](../architecture/README.md) (structure definition · reconciler · manager · admission). Teaching metaphor is transitional — [appendix](../architecture/appendix/metaphor.md).

Exit remains **José’s** judgment when organism readiness feels proper — including how deep the manager must be before the theme may close.

---

## 1. Why this note exists

Palm can boot a **system**. Palm can run **business** (flows, start, continue).  
Between those two cares, structure is still **glue**: profiles, host enrich, catalog load order, soft “definitions ready,” future spawn scripts.

That glue multiplies when Palm scales past one process.

This file names the **missing home** and the **reassembly of the organism** around it.  
It names **roles**, **ports**, and **what every layer must change**.  
**Theme closed:** [VISION-0.64](closed/VISION-0.64.md). This essay remains the deep law.  
It does **not** replace boot, orchestration, or the workload plane.

**Duty:** write the structure Palm will grow into — realistic, named, honest about what we cannot do yet.  
**Posture (from 0.57+):** plan the home; engine then alternate path; validate; migrate; clean. Prefer 80/20. Complete what is open. Put debt where a theme can own it. Prefer proper over hot glue.

**Refinement (2026-08-07):** assembly is not only a pure package bolted on. It is the season to **assemble Palm**: single desired structure, single readiness truth, port-only clients, composition root as wire only. Prior seasons built the body. This seed is when the body gets one reconciler and wrong hops die.

Palm is **experimental** and **pre-1.0**. There is **no long-term support** promise. See [README](../../README.md). Break for truth.

---

## 2. The missing care (lifecycle)

| Care | Owner today | Job |
|------|-------------|-----|
| **System up** | Boot + seats + supervisor | Machine lives: planes, ports, continuous loops |
| **Organism ready** | **Missing home** (scattered glue) | Desired structure holds; ground and places honest; business may start only when admission allows |
| **Business runs** | Orchestration + work/wait planes | Flows, jobs, start, continue |
| **Places exist** | Workload plane (scout) | Named bodies: spawn or adopt; health; stop |

**Assembly** is the name for **organism ready**: a **desired-state reconciler** for structure, not a second job orchestrator.

| Prefer | Avoid |
|--------|--------|
| One reconciler after system, before business pretends | Stuff assembly into boot forever |
| One **assembly definition** from **authority** (or local seed) | Encode every role only as profile flags |
| Workload as **place book** | Workload as second business orchestrator |
| Flows as **business rules** only | Encode cluster topology as a customer flow |
| Product depends on **admission** and **ports** | Product digs the **composition root** (host) for structure |
| Structure effects on **assembly effect** ports | Grow every structure verb onto `ExecutionPort` |

**Lifecycle sense:** assembly coordinates *becoming* Palm.  
**Orchestration (engine sense):** runs business once admission allows.  
Do not fight the word “orchestrator” as a **profile role** (light center). That role is topology. Assembly is the **lifecycle phase** and the **reconciler**.

---

## 3. Roles (normative)

Name the split. Do not collapse it.

| Role | Computer-science term | Duty |
|------|----------------------|------|
| **Authority** | Author of desired structure | Publishes the **assembly definition**. Does not stand at every gate for clients. |
| **Assembly definition** | Desired state (declarative) | Versioned DNA (essay field set — teaching). **Code now:** `StructureDefinition` fields are `id` / `version` / `role_intent` / `refuse` / **`capabilities`** (seven **organs**) / `places_required` / `meta`. Services stay composition. Do **not** treat the essay field list as the current StructureDefinition API. |
| **Assembly engine** | Pure reconciler | Holds definition + **assembly status**; emits **effect intents**; folds **observations**. No sockets. No OS spawn. No business jobs. |
| **Assembly status** | Local readiness / status model | This process’s reflection under the current definition. Not a second definition. |
| **System loop** | Apply + observe cycle | Loads definition; ticks engine; applies intents via ports; feeds observations; publishes admission. |
| **Subsystem** | Organ with a **contract** | Must provide, report, and refuse under the definition (place book, ground faces, planes, supervisor, vitality, …). |
| **Client** | Product, surface, edge | Uses the organism. Depends only on **published interfaces**. Never on the composition root for structure or readiness. |
| **Composition root** | Host | Wires once. Not a runtime API for product. |

**Admission** is how the reconciler **gates** work that needs a true organism (for example business start). Authority does not wave that flag for every client. The assembly path does.

**New definition → reassemble.**  
Load the new desired state. Reset readiness under the old law. Emit intents to converge. Invalidate stale projections. Status must not claim ready under a definition that is no longer in force.

### 3.1 Teaching picture (metaphor — not law)

The table above is **normative**. This subsection is **teaching only**. It helps humans and agents *feel* the split before they implement ports and packages. Spirit also: [PHILOSOPHY.md](../../PHILOSOPHY.md).

Think of one Palm process as a **kingdom** that must be true before market day.

| Metaphor | Role in Palm | What it protects |
|----------|--------------|------------------|
| **King** | **Authority** | Issues the law of structure. Does not waste the day showing thumbs to every petitioner. |
| **Royal decree** | **Assembly definition** | The written law of what this kingdom **shall** be (DNA). Versioned. Replaceable. |
| **Steward** | **Assembly engine + system loop** | Receives the decree. Assembles the kingdom. Keeps the **ledger**. Shows **thumbs** (admission) so peasants do not pretend the realm is whole when it is not. |
| **Local ledger** | **Assembly status** | Faithful reflection of *this* kingdom under *this* decree. Not a second king. Not a second decree. |
| **Manors** | **Subsystems** with contracts | Great houses (place book, ground faces, planes, supervisor, vitality, …). Each has **manorial duties**: provide, report, refuse under the decree. |
| **Peasants** | **Clients** (product, surfaces, edges) | Use the kingdom. They swear an **oath of fealty**: approach only through published ports and admission — never dig the host as if packaging were the crown. |
| **Hands of the steward** | **Assembly effect port + handlers** | Do the work the steward requests. The pure steward does not open sockets or spawn bodies himself. |
| **New decree** | **New definition** | The steward must **reassemble**. The ledger must not claim ready under a dead law. |

Why this picture matters:

- **Authority** and **admission** are different duties. Confusing them is how host glue becomes a false king.  
- **Subsystems** without named duties are manors that freestyle — the source of spaghetti.  
- **Clients** without fealty reopen private tunnels into the composition root.  
- A living kingdom can **know when it is not whole** (ledger, thumbs, eyes of vitality) even before an outside tester arrives.

When you write code or ADRs, use the **computer-science terms** in §3 and §4. Keep the metaphor when you teach, negotiate scope, or explain why a hop is illegal.  
Implementation posture (citizen · household · pretender · purge · one gate): **§6.4**.

---

## 4. Normative terms

Define once. Reuse. Map: [PALM.md §3](../PALM.md).

| Term | Meaning |
|------|---------|
| **Assembly definition** | Declarative desired structure (DNA). Single truth when loaded from authority or accepted local seed. |
| **Assembly engine** | Pure reconciler: definition + observations → status + effect intents. Lives under core purity law. |
| **Assembly status** | Local phase and readiness under the current definition (including definition-ready / blocked / invalidated). |
| **Effect intent** | Closed set of structure actions the engine requests (ensure place, release place, invalidate projection, …). System applies. |
| **Observation** | Fact folded into the engine (place ready, truth home down, projection loaded, …). |
| **Admission** | Read surface: may business that needs ground run? Snapshot of assembly status for clients and planes. |
| **Assembly control** | Lifecycle surface: load definition, tick / run until steady. **Not** injected into product. |
| **Assembly effect port** | System protocol that **applies** effect intents (handlers / adapters). Peer of execution — different subject. |
| **Execution port** | Business **run** effects (resource, workload for jobs, job drive). Not the structure reconcile door. |
| **Truth home** | Place that is **authoritative** for durable meaning this process projects. |
| **Projection** | Local view of authoritative state. Cache allowed. Source of truth stays at truth home. |
| **Invalidate** | Drop or seal projection when truth home is not ready or definition changes. Refuse work that needs that truth. |
| **Place book** | Workload registry of named places (spawn or adopt). Lifecycle + readiness. |
| **Control home** | Who assigns work and whose surfaces this process uses for control (may equal truth home or sit above it). |
| **Light center** | Composition **rule**: refuse heavy job body and/or durable ground on purpose; place weight; stay efficient. Not “unable.” |
| **Work place** | Place whose role is to execute work the light center will not carry. |
| **Support place** | Place whose role is to hold durable ground or other weight the center will not hold. |
| **Tree topology** | Each node depends **up** for authority/control. Not full mesh first. |
| **Profile** | Local bootstrap **seed** and defaults. Maps into or is overridden by assembly definition. Not a parallel structure king. |
| **Subsystem contract** | What a major organ must provide, report, and refuse under the current definition. |
| **Composition root** | Host wiring. Not product’s path to structure. |
| **Citizen** | Act that needs the organism whole; may pass only through **admission**. |
| **Household** | Boot / assemble / apply path; not a market-day citizen; not forced through business admission. |
| **Pretender** | Path that pretends readiness without admission; purge when the gate is law. |

These names stay. Code now: `EffectPort` (assembly effect port); place registry (`PlaceEffectPort` / `InProcessPlaceRegistry`); `PALM_STRUCTURE_DEFINITION_ID` (DNA seed); `StructureEffectPort` (household hands); inventory `GATED_PATHS` / `READINESS_EDGES`.

**Invocation** (call another Palm’s door) ≠ **projection** (represent their truth as part of *our* readiness).  
**CQRS projection** (product read model) ≠ **assembly projection** (organism view of truth home).

---

## 5. Law (intent)

1. **Boot** cares for the **system** (machine able to assemble).  
2. **Assembly** cares for **organism truth** so business can be honest.  
3. **Orchestration** cares for **business rules** after admission allows.  
4. **Workload** cares for **places**. Assembly **requests** places via intents; it does not reimplement runners.  
5. **Authoritative first.** Accept definition from authority or local seed → reconcile (intents + observations) → admission → then drain and flows that need that truth.  
6. **Truth home is a place in the book.** Not ready → invalidate → do not pretend.  
7. **Single readiness truth.** Only assembly status (via admission) answers definition-ready. No hand-set host flags as a second king.  
8. **Tree first.** Home points up. Relays may exist later with hop limits.  
9. **Two axes.** Vertical = meaning and home. Horizontal = place book. Tunnels ([VISION-TUNNELS](VISION-TUNNELS.md)) add **reach** later; they do not redefine the axes.  
10. **Recursive support.** Org/realm speech maps to support with children — assembly-native, not Grove-only.  
11. **Do not kill what works.** All-in-one remains valid. Light center is a **chosen rule**, not the only shape.  
12. **Business BT ≠ assembly tree.** Same grammar may tick assembly later. Different subject. Different home.  
13. **Clients use ports.** Product and surfaces depend on admission and published effect ports. They do not dig the composition root for structure.  
14. **Structure ports ≠ execution port.** Do not grow every organism verb onto business execution.  
15. **New definition → reassemble.** Status must not lie under a stale definition.  
16. **Pre-1.0:** break glue; name residual; no LTS theater. Prefer reassembly over dual-path forever.  
17. **One admission gate for business that needs ground.** Fail closed. No corridor police as architecture.  
18. **Purge pretenders** when the gate is law. Do not staff permanent checkpoints around illegal hops.

---

## 6. Ports and access (transformation law)

### 6.1 Split subjects

| Port / surface | Subject | Who holds it |
|----------------|---------|--------------|
| **ExecutionPort** | Business run effects (resource, job workload, job drive/list) | Graphs + product for **jobs** |
| **Assembly effect port** | Apply **effect intents** from the reconciler | System loop + handlers only |
| **Admission** | Read assembly status / may-run-business | Product, work plane, inspect, vitality present |
| **Assembly control** | Load definition; tick / run until steady | Boot/assemble phase and authority refresh — **not product** |
| **InstallInterface** | Collaborator board for subsystem install | Boot / seat bind |

### 6.2 Dependency law

```text
Authority / seed  →  assembly definition
                         │
                         ▼
              assembly engine (core, pure)
                         │ intents + status
                         ▼
         system loop + assembly effect port
                         │ hands (place book, projection, policy, …)
                         ▼
              admission snapshot on shell
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
     work plane / start         product / surfaces
     (respect admission)        (admission + execution only)
```

**Composition root** injects ports and starts the loop. Then it gets out of the way.

### 6.3 Guarantees against pain

| Do | Do not |
|----|--------|
| Closed **effect intent** ADT; grow by theme | Stringly ops and silent host paths |
| Registry of **handlers** (one duty each) | One god method with every structure chore |
| Pure engine unit tests with fake observations | Engine imports host or product |
| Budgeted reconcile loop (max ticks / time) | Infinite assemble hang |
| Idempotent ensure/release where possible | Double-spawn chaos on re-tick |
| Product constructors take **admission**, not control | Product marks ready by hand |
| One readiness truth | Soft ready on host + assembly status |
| Stage migrate and **kill** dual glue | Permanent dual hop “for compatibility” pre-1.0 without named residual |

### 6.4 Citizenship and purge (implementation posture)

This section is **normative** for how the theme lands. It is not optional soft migration culture.  
Code inventory: admitted paths `GATED_PATHS`; assemble hands `StructureEffectPort`; residual `open_residual_edges`. This section keeps the vision names.

#### Who is a citizen?

**Citizen** = any act whose truth **requires the organism to be whole** (ground, projection, definition truth). Examples: work-plane starts that need the catalog; product doors that claim definitions are ready or run flows against ground; surfaces and tests that assert the same.

Citizens **may pass only through admission** (and the ports that mean).  
They do **not** earn a tunnel because they are old, useful, or green in CI.

#### Who is household (not a market-day citizen)?

**Household** = work that **is** the assemble path or makes assemble possible. Examples: boot until the machine can apply intents; assembly control, tick, apply, observe; place-book hands **as effect of assemble**; vitality *seeing* status.

Household is not “skipping the gate.” It is not a peasant.  
Do **not** force household through business admission — that deadlocks the kingdom.  
Do **not** let household smuggle business starts without admission.

#### Who is a pretender (purge)?

**Pretender** = any path that pretends business readiness without admission. Examples: host soft-ready flags; product digging the composition root for structure; dual “catalog loaded enough”; tests that start business with admission down.

When the gate is law, pretenders **break** until they obey or die.  
That is the opportunistic purge. Half-assembly with host still king wastes this season.

#### One gate — not guards and checkpoints

| Gate (law) | Guards / checkpoints (rot) |
|------------|----------------------------|
| One admission: may business that needs ground run? | Many special cases and “this path is ok for now” |
| Fail **closed** when admission is down | Fail open with a warning |
| Citizens only through that door | Patrol residual hops; document them as lifestyle |
| Household has its own phase (assemble) | Force assemble through business admission |
| Residual = kill-dated debt in the theme | Career for corridor police |

**Staging** (floor path, then widen) means: build steward and gate, then force **the same law** across remaining pretenders.  
Staging does **not** mean: leave side doors so CI stays green.  
Staging does **not** mean: a permanent watch of illegal corridors.

#### Testing law

- Engine: fake observations; no host.  
- Loop / handlers: fake effect port or thin doubles.  
- Product and planes: inject admission (`ready` true/false). Never mark ready by reaching into the composition root.  
- Integration: only the assemble path makes admission true.  
- A test that starts **citizen** work with admission down is a **wrong test** — fix it or delete it.  
- Assert bypasses **do not** work.

#### Residual honesty

If a pretender cannot move in the same slice, **name it** with a residual row and a theme-owned kill intent.  
Do not promote it to architecture. Do not staff guards around it.

---

## 7. Engine and system modules (implementation shape)

Not open code yet. This is the intended shape when the theme lands.

### 7.1 Core (pure)

Vision tree (essay). **Code now:** `palm/core/structure/` — see the box at the top.

```text
palm/core/assembly/
  definition.py      # assembly definition (desired state)
  status.py          # phase, definition-ready, reasons
  intent.py          # EffectIntent closed set
  observation.py     # Observation closed set
  ledger.py          # in-engine status under current definition
  result.py          # AssembleResult (status + intents + flags)
  engine.py          # AssemblyEngine
  exceptions.py
```

**Engine verbs (illustrative):** `receive_definition` · `observe` · `tick` · `status`.  
**Floor intent set (illustrative):** ensure place · release place · invalidate projection · refresh projection · apply structure policy · request structure seed (after ready).  
**Floor observation set (illustrative):** place observed · truth home up/down · projection loaded/failed · structure seed finished · seat bound (optional).

Invariant: **nothing in `palm.core` imports outside `palm.core`.**

### 7.2 System (hands + gate + phase)

Vision tree (essay). **Code now:** `palm/system/structure/` — see the box at the top.

```text
palm/system/assembly/   # name may adjust at theme open
  loop.py               # load → tick → apply → observe until steady | blocked
  effects.py            # EffectPort (protocol; was AssemblyEffectPort)
  admission.py          # snapshot for clients and planes
  handlers/             # ensure_place, projection, policy, …
```

**Lifecycle:** after boot makes the machine able to apply, **assemble** until steady or honest blocked; then continuous serve. Supervisor may later re-observe truth home or accept a new definition.

### 7.3 What other modules must do

| Module | Duty under assembly |
|--------|---------------------|
| **Place book (workload)** | Target of ensure/release/status; report readiness as observation |
| **Catalog / ground faces** | Projection load and invalidate; truth-home signal |
| **Work plane / drain** | Respect **admission** before starts that need ground |
| **ExecutionPort** | Unchanged subject (jobs). Does not apply structure intents |
| **InstallInterface** | Bind engine, effect port, admission onto the shell |
| **Vitality** | Report assembly phase and ready (eyes only) |
| **Inspect (product)** | Present admission snapshot; not control |
| **Host (composition root)** | Supply seed definition or authority pointer; start loop; inject ports |
| **DeploymentProfile / composition** | Become **seed** of definition for a path — not parallel structure king |
| **Product services** | Depend on admission + domain ports; remove host digs for readiness |
| **CQRS** | Optional status queries. No command that sets ready outside the loop |

**Org (product speech) vs support (organism law):**  
Support and sub-support are place/projection structure.  
Organization and realm as **business** meaning (catalog, trust, journeys) run on the job path **inside** that structure. Assembly DNA may shape seats and places so an org can take place. It does not encode sector process law.

---

## 8. Workload refined (scale without a second panic)

Workload is not only “run a container.”

| Workload is | Workload is not |
|-------------|-----------------|
| Named places and availability | Claim law for WorkIntents (that is work plane + store) |
| Spawn **or adopt** | The assembly definition itself |
| Gate: dependency down → do not start that work yet | A second business orchestrator |
| How multi-process becomes **controlled** | Magic concurrency without readiness |

**Job path vs assembly path to places:**  
- Job: “run this isolation for this job” → **ExecutionPort**.  
- Assembly: “this place must exist for the organism” → **effect intent** → place book.  
Same book underneath. Two doors. Two duties.

In-process multi-claimer capacity remains [0.62](closed/VISION-0.62.md). Multi-writer shared store remains [SD-019](../../TECH-DEBT.md#sd-019). Assembly does not erase that residual.

**Light center dogfood (rule, not universal law):** ensure support place + work place; project from support; then Palm-as-known. The center may still place ordinary workloads (e.g. postgres) without every dependency becoming its own Palm.

---

## 9. Profiles and dynamic structure

Profiles today capture part of assembly (roles, flags, deployment shape). Keep them as **seeds**.

With assembly:

1. Process boots far enough to find authority (or run all-in-one local DNA).  
2. Load **assembly definition** (authority or seed map from profile).  
3. Engine + loop reconcile until steady or blocked.  
4. Admission published.  
5. Business works when admission allows.

Structure becomes **data-driven from one truth**. Glue of “if profile then install…” moves into definition + handlers, then migrates off host spaghetti.

---

## 10. Two axes and recursive support (scale meaning)

### 10.1 Vertical and horizontal

| Axis | Assembly’s care | Workload’s care |
|------|-----------------|-----------------|
| **Vertical** | Who is truth home / control home; what to project; when to invalidate; hop home | Places that *are* truth home must be in the book |
| **Horizontal** | Which places the DNA requires | Spawn/adopt, health, readiness of bodies across hosts |

**Physical** workers and resources may stay horizontal.  
**Logical** supports and sub-supports grow vertical.  
Both axes must agree before business pretends the world is whole.

### 10.2 Tree of processes (near scale)

```text
        Light center (optional rule)
        control + claim + surfaces
                 │
     places / readiness (workload book)
        ┌────────┴────────┐
        ▼                 ▼
  Support place      Work place(s)
  (truth home)       (job body)
        │
   projection up when ready
```

- Worker may use center as **control home**.  
- Truth home may be support place, or center after it projects. Choose explicitly; do not blur.  
- Mid nodes that **propagate** authority need not be thin “worker profile.” Any Palm may depend on another Palm.

### 10.3 Recursive support (org / realm)

| Speech | Assembly meaning |
|--------|------------------|
| **Organization** | Support (or light center over support) with DNA; may **project** child realms |
| **Realm** | Sub-support / mid; local ground; home still up |
| **Multi-org** | Several supports under one root, or several trees — same law |

Grove ([VISION-GROVE](VISION-GROVE.md)) still owns **org crown conversation** at federation scale.  
Assembly owns **whether a node can be that support and become definition-ready**.

**Palm slogan:** genome + roles + place book + assembly + home up. Workers are full genome under a rule, not dumb slaves.

---

## 11. What other systems do (lineage, not copy)

| Elsewhere | Palm mapping |
|-----------|--------------|
| K8s desired state + controllers + status | Definition + reconcile loop + assembly status |
| Control plane vs data plane | Authority/definition vs running jobs and traffic |
| Hexagonal ports and adapters | Core intents + system effect port; clients on admission |
| OTP supervision / start phases | Boot then assemble then serve |
| Composition root (DI) | Host wires; clients never take root as API |
| Workflow products’ worker fleets | Often **ops outside** the product soul |

Palm’s rare packaging: **assembly** next to **orchestration** and **workload**, in a BT-native organism. The *need* is common. The *named organ* is the ambition.

---

## 12. Growth path (theme **0.64** open)

Same rhythm: **engine → alternate path → validate → migrate · clean**.  
Closed 0.63 chronicle: [VISION-0.63](closed/VISION-0.63.md) §9 (history, not a queue). Summary:

| Stage | Spirit |
|-------|--------|
| **Floor** | Core types + thin engine; **embedded** DNA; system admission; one citizen fail-closed; coherence suite (red = map) |
| **Growth** | cli/server DNA; more citizens; profiles/env as seed only; intents/handlers; projection; vitality/inspect; reassemble |
| **Unplanned** | Break inventory and unknown impact — reserved slices |
| **Later / Grove** | Multi-host tree, tunnels, org crown |
| **Non-goals for 0.63** | Full mesh; replace orchestration; force light-center every boot; CAS (SD-019 unless natural); full surface purge; product-owned reassemble |

Order is **how the wall is built**, not permission for side doors. See §6.4.

**80/20:** one real fail-closed path under embedded DNA beats a perfect cluster brochure.

**Boy scout:** when assembly touches host glue or catalog wire, move truth toward definition + handler — do not only relocate menus ([AGENTS §1.1](../../AGENTS.md)).

---

## 13. What we keep (spine)

Do not redesign these to invent assembly:

- Job path and pure core  
- Start / continue (work plane + wait plane)  
- Session law  
- Workload plane foundation (place / exec / runners)  
- Supervisor continuous seats  
- Vitality + Inspect  
- In-process exclusive claim (0.62)  
- Registry extension and seat DI direction  
- ExecutionPort for **business** effects  

Assembly **removes future glue** and **absorbs scattered become-Palm glue**. It does not erase the seasons that made the tree possible.

---

## 14. Structure seed (business structure, not business rules)

Assembly does **not** run sector workflows. It may still **carry a seed**: a declared bootstrap (often a flow or definition pack) that **installs base business structure** after the organism is ready.

| Assembly definition | Structure seed (optional) |
|---------------------|---------------------------|
| Role, truth home, places, refuse, projection | Flow or pack that **authors** initial **business definitions** |
| Organism ready | Shelves ready for authors to grow rules |

Seed runs **after** definition-ready (or as the last step of assemble). It is scaffolding — not the company process.

---

## 15. Horizon (dream, not floor)

Palm is a strong home for **datasets**, **training automation**, and **workloads** that run TinyML or larger models. Those bodies are places in the book. Assembly and light-center rules keep the center efficient so small runtimes can live well under Palm.

A living organism can **know when it is not whole** (status, admission, vitality) even before an external suite says so.

**After assembly tool:** [VISION-TUNNELS](VISION-TUNNELS.md) — trusted reach, neighborhood maps, cloud↔device, offline sector honesty.  
**After tunnels:** [VISION-GROVE](VISION-GROVE.md) — many palms, org crown, continuous interface.

*There is no place like home.*

---

## 16. Honesty and honor

| Do | Do not |
|----|--------|
| Name what we cannot ship yet | Fake green for absent assembly |
| Plan debt into a theme home | Hot-glue mid-slice with no residual row |
| Prefer completing open intent | Leave half-homes because speed felt good |
| Prefer **reassembly** of access and readiness | Bolt-on engine with host still structure king |
| **Purge pretenders**; one admission gate; fail closed | Guards, checkpoints, fail-open dual hops |
| Wrong tests that bypass the gate: fix or delete | Green bar that encodes the old lie |
| Say experimental / no LTS out loud | Imply enterprise support pre-1.0 |
| Increase start cost for structure | Pay forever in glue when speed matters most |

Palm did not always know what it wanted. Past code is history and teacher — not always the prime example.  
**Duty now:** know better, do what we can, say what we cannot, plan the opportunistic moment. That is organic. That is honorable.

---

## 17. Success picture (for a future theme exit — not a checklist today)

1. A reader can point to **assembly** as the reconciler between boot and business.  
2. An assembly definition shapes what a process has without open-coded profile soup for that path.  
3. Truth home is tracked; down means invalidate; dependent work does not pretend.  
4. **Single readiness truth** via admission; composition root is not a second king.  
5. Product and surfaces use **ports**; they do not dig host for structure.  
6. Structure effect port and execution port stay separate subjects.  
7. **Citizens** only through admission; **household** assembles without deadlock; **pretenders** purged.  
8. One gate — not guards/checkpoints; fail closed; wrong bypass tests gone.  
9. Workload remains the place book; business flows remain business.  
10. All-in-one still works; light center is optional rule.  
11. New definition reassembles; status does not lie under a stale definition.  
12. Docs and ADR match code; residual kill-dated if any; José judges exit.

---

## 18. Open decisions (theme open — close in slices)

**Closed at 0.63.0:** packages prefer `palm.core.assembly` + `palm.system.assembly`; first DNA **embedded**; env = seed + packaging; ADR-**032**; coherence suite as truth instrument; full-in law / staged purge; exit = José’s feel.

**Still open (learn in slices):**

1. Exact admission snapshot and DNA id type names.  
2. First citizen path lock (work plane preferred if honest).  
3. How thin floor DNA fields are before place intents.  
4. Whether cli DNA is required before José’s exit feel.  
5. Authority pull and definition storage (not floor).  
6. Worker truth home / ensure-plan grammar (growth).

---

## 19. One sentence

**After the system is up, assembly reconciles authoritative desired structure into a tracked organism with one readiness truth and port-only access; only then business runs — so Palm lives as a tree of named places without mesh theater, host as king, or glue as architecture.**

---

*Seed essay. Not a theme open. Prefer tool before dream. Prefer place readiness before multi-writer myth. Prefer reassembly over dual-truth theater. Prefer one gate over guards. Prefer purge of pretenders over soft green. Prefer honor over sparks.*  
*José decides when this becomes a minor.*
