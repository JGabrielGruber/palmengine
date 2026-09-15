# Glossary — intended architecture

**Status:** Living engineering vocabulary for this vault.  
**One meaning per term.** Prefer these words in architecture notes.  
**Living map (may lag or dual-name):** [PALM.md §3](../PALM.md) — link; do not fork forever.  
**Metaphor / teaching words:** [appendix/metaphor.md](appendix/metaphor.md) — not law here.  
**Agent mode:** [AGENTS.md](AGENTS.md).

**How to use:** When two words fight, this glossary wins for **intended design**. Code names below are **now**. Vision/ADR essays may still say assembly.

---

## 1. Layers and packages

| Term | Intended meaning | Do not use for |
|------|------------------|----------------|
| **Core** | Pure engines and pure types under `palm.core`. No I/O. No imports outside core. | Host packaging; product policy |
| **System** | Running Palm: shell, engines, interfaces, subsystems (planes, supervisor), boot, vitality, structure manager. | Product business rules; HTTP surface code |
| **Shared** | Reusable code that is not system and not product (common helpers, kits that many layers use carefully). | A place to hide layer violations |
| **Plugin** | Registry extension (pattern, provider, storage, runner, …) installed at the edge. | Ad-hoc `if type ==` menus in hubs |
| **Hand** | Function that fills or drops one **named** organ. Lives next to the organ; listed in an explicit table. | Import-time self-register; host `if` |
| **Walker** | Live code that performs one duty (install, start, stop, apply). Something in `src/` must call it. [ADR-033](../adr/033-one-walker.md). | Helper that only names an unused branch |
| **Fill site** | The one place that installs or registers a member. Dual fill = two walkers still live. | Host `if` next to the hand |
| **Product** | Userland services (assist, execution façades, domain APIs). Client of system ports and admission. | Transport adapters; composition root digs |
| **Surface** | Transport edge only (`palm.runtimes`: CLI, REST, MCP, SSR, WebSocket, …). Depends on system — never reverse. | Structure law; business policy |
| **Host** | Composition root: seed choice, wire seats once, package settings. Not a public structure API. | Readiness king after structure definition load |
| **Composition root** | Same duty as host in wiring terms — the place that assembles the object graph once. | Runtime bag product digs for readiness |
| **Package** | Installable Python package / package family under `palm.*` (architecture C4 code altitude). | Business “package” of work for a customer |
| **Layer law** | Allowed dependency direction between core, system, product, surface, host. | Theme process rules |

---

## 2. Structure management (organism ready)

Between **machine up** (boot) and **business runs** (job path). Component note: [c3-components/structure-management.md](c3-components/structure-management.md).

| Term | Intended meaning | Do not use for |
|------|------------------|----------------|
| **Structure management** | Whole care: definition, reconcile, materialize, admission. Intended component name. | Job orchestration |
| **Structure definition** | Declarative desired structure for this process (roles, refuse, places, membership intent). **Structure law after load.** | Business flow / process definition; env flag soup as peer law |
| **Structure reconciler** | Pure engine: definition + observations → status + effect intents. No sockets, no OS spawn, no business jobs. | System hands that apply intents |
| **Structure status** | Local record under the current definition (phase, places, block reasons). | A second structure definition |
| **Structure manager** | System loop: load definition, tick reconciler, apply effect intents, fold observations, **materialize** membership, publish admission. | Admission-only dashboard; host soft-ready flags |
| **Effect intent** | Closed-set structure action the reconciler requests (ensure place, release place, policy, projection, …). System applies. | Business side effects on ExecutionPort |
| **Observation** | Structure fact folded into the reconciler (place ready/failed, truth home down, policy violation, …). | Business events on the job path |
| **Materialize** | Make the process match the definition: resolve membership units, wire only allowed life, ensure places, refuse illegal installs. | Only flipping `may_run_business` after freelanced boot |
| **Admission** | Published read gate: **may this act run?** Business-rule face. Business does not talk to engines / supervisor / structure seat. Reads **installed capabilities** (and ready / refuse). Not a second membership walker. Ready door: `require_business_admission`. Organ door: `require_capability`. Dependents [VISION-0.67](../vision/closed/VISION-0.67.md) (**closed**) · face [VISION-0.66](../vision/closed/VISION-0.66.md). | Authn / authz; product dig into lower layers; copy of `LOCAL_CAPABILITY_HANDS` |
| **Admission snapshot** | Immutable view of admission (`may_run_business`, phase, definition id, reasons, **installed** `capabilities` / `has_capability`). | Live mutable seat as the only API forever |
| **Seed** | How packaging chooses which structure definition (or membership input) to load: mode, profile, env. **Chooser, not king after load.** | Peer structure law after load |
| **Refuse** | Definition tokens for shapes this process must not carry (e.g. server surfaces, background drain). | Business validation errors |
| **Capability** | Named system membership unit (journal, outbox, work_drain, …) — machine organs, not product domains. Structure fact: listed → hand installs → it runs. Omitted → it does not run. | Product feature flag marketing; a second `may_run_business` |
| **Membership unit** | One installable structure entry: a **plugin**, **product** service, **surface**, or **capability** the definition may list. | A running job |
| **Membership section** | Grouping in the structure definition (intended: `plugins`, `products`, `surfaces`, `capabilities`, plus refuse/places). Like `INSTALLED_APPS` families. | Business catalog sections |
| **Composition** | Capability / membership set declared present on a process. Intended: driven by structure definition + seed, not freelanced OR of settings. | Docker Compose the product |
| **Membership source** | Where a unit or definition package is obtained: **local** (already on machine) or **provider** (Palm protocol), later **cache**. Attribute of membership, not a second manager. | Ad-hoc curl/git as architecture |
| **Structure source resolver** | Hands that obtain definition/membership artifacts for a given source, then hand them to materialize. Local resolver first; provider resolver later. | Business resource providers in general |
| **Local (source)** | Units already importable as Python packages / local definition on this system. Materialize installs/wires them. | Remote provide |
| **Palm provider** (structure) | Remote path: **provide** definition packages / membership via Palm protocol (not freestyle download-as-law). Same materialize step after provide. | SQL/HTTP product providers only |
| **Definition package** | Portable bundle of structure or membership definitions a resolver can make local enough to materialize. Schema open. | Business flow zip alone |
| **Provide** | Protocol act: home/support delivers definitions or artifacts to this process. | Silent side-load without definition |
| **Cache / replicate** | Optional: after provide, store locally so later boots look **local**. Supporter replication, cold workers. Far future. | Primary remote story (primary is provide) |
| **Authority** | Author of structure definition when not only local seed (later: remote / org). Does not stand at every client gate. | Local host packaging |
| **Reassemble** | Load new or forced definition; void prior ready; converge again. | Soft-skip admission for CI |
| **Readiness dashboard** | See admission, refuse business start / continue paths, map duals — **without** yet owning materialize. Progress honesty for early structure work. | Claiming structure manager is done |
| **Dual readiness** | Two or more peer answers for “may business run?” (soft flags, catalog order, host dig, admission). **Architecture debt** — purge or name. | Honest residual control paths (cancel when closed) |
| **Assembly** | **Vision / theme name** for structure management ([VISION-ASSEMBLY](../vision/VISION-ASSEMBLY.md)). Packages are `palm.*.structure`. | A second product |

**Code now (2026-08-17 — José locked package rename):**

| Intended | Code today |
|----------|------------|
| Structure definition | `StructureDefinition` / `resolve_builtin_definition` / `structure_definition_id` |
| Structure reconciler | `StructureEngine` (`palm.core.structure`) |
| Structure status / admission | `StructureStatus` / `AdmissionSnapshot` · phase `StructurePhase` |
| Structure errors | `StructureEngineError` · `StructureError` |
| Structure manager | `StructureSeat` + loop + hands (`palm.system.structure`) — **partial** (dashboard strong; materialize weak) |
| Phase / field / seat | `system.structure.assemble` · shell `.structure` · vitality `structure` (`SEAT_STRUCTURE`) |
| Options | `structure_definition` · `structure_skip` · `structure_bind_workload` · `structure_max_ticks` |

---

## 3. Shell, ports, planes

| Term | Intended meaning | Do not use for |
|------|------------------|----------------|
| **Shell** | System instance that owns interfaces and subsystems. Not the default argument to every function. | Host packaging module |
| **Interface** | Named contract on the shell others call (`execution`, `install`, admission, structure effects, …). | UI “interface” |
| **Port** | Code name for a named effect or admission interface. Prefer **interface** in architecture prose when teaching contracts. | TCP/UDP network port (say *network port*) |
| **Execution interface** | Business effects: submit, resume, provide input, invoke resource, start/exec workload, … | Structure effect intents |
| **Install interface** | Collaborator board for subsystem install (peer of execution). | Product “install Palm” CLI alone |
| **Subsystem** | Membership + lifecycle region on the shell (planes, supervisor, …). Under structure management: organ with a contract. | Entire product domain |
| **Plane** | System path for one kind of traffic (work/start, wait/continue, session, workload, event, …). | Cloud “control plane” marketing |
| **Work plane** | Start path: WorkIntent → new job (drain under supervisor). | Structure assemble loop |
| **Wait plane** | Continue path: wait interest match → resume / fail owner. | Human “wait” in product copy |
| **Session** | Outside subject of a walk. Owns many instances. Continue **focus** is among owned instances only. | Instance id; principal identity; user plane |
| **Principal** | Who is walking (identity). Core type exists. Not the walk. | Session; admission; adapter filter |
| **User plane** | Later identity policy over principal ↔ session (entry, visibility, impersonation, grants). Does not own jobs. [ADR-027](../adr/027-session-plane.md) D8 · D11. | Session plane; Navigator invert; ambient `AuthEngine` current principal |
| **Supervisor** | Continuous care of planes / drain workers (system). | OS process supervisor only |
| **Vitality** | Living eyes / inspect heat on the system (present, not structure law). | Admission snapshot |
| **Seat** | Installed organ on the shell (e.g. structure seat, plane service). Prefer inject seat/interface over ambient shell. | Chair metaphor as architecture |

---

## 4. Job path (business)

| Term | Intended meaning | Do not use for |
|------|------------------|----------------|
| **Job path** | Business spine: catalog definition → pattern → job → effects → events → start/continue. | Structure assemble path |
| **Definition** (business) | Declared contract of work (flow, process, resource, …) in the catalog. | Structure definition |
| **Operator-guidance definition** | Catalog definition whose job is the empty-handed walk. It **stays** as session home when it starts other work. Many allowed. None is the engine `main()`. [VISION-NAVIGATOR](../vision/VISION-NAVIGATOR.md). | Assist product domain; structure definition; user plane |
| **Presentation adapter** | Kit **`palm.kits.present`**: bind session, present the current turn, submit input, start or continue, change focus. Consumes runs. Not purpose. [VISION-NAVIGATOR](../vision/VISION-NAVIGATOR.md). | Product service; catalog ACL; surface protocol; `palm.kits.server` |
| **Pattern** | How a business definition runs (wizard, process, …). | Structure reconcile algorithm |
| **Job** | Live run under orchestration. | OS process; workload place |
| **Instance** | Durable record of a run. | Structure status |
| **Orchestration** | Drives jobs (scheduler, apply result, status). Not structure manager. | Host “orchestrator” profile role alone |
| **Interest** | Explicit want: **start** (trigger) or **continue** (wait). | Casual curiosity |
| **Start** | New work via work plane / drain. | Booting the process |
| **Continue** | Resume or fail owner via wait plane. | Structure reassemble |
| **Effect** (business) | Side effect through execution interface (resource, workload, …). | Structure effect intent |
| **Completer** | Emits self-events when a unit finishes so start/continue can fire. | Structure observation |

---

## 5. Places and scale (intended)

| Term | Intended meaning | Do not use for |
|------|------------------|----------------|
| **Place** | Named body or ground unit in the structure / place registry (process, worker, support, …). | UI screen |
| **Place registry** | Map of places this process knows; horizontal scale (many bodies). | Business product catalog |
| **Truth home** | Place that is authoritative for durable meaning this process projects. | Local packaging defaults |
| **Projection** | Local view of authoritative state — not a second truth. | CQRS product board only |
| **Control home** | Who assigns work / whose control doors this process uses. | Truth home (may differ) |
| **Light center** | Role intent: refuse heavy body/ground on purpose; place weight elsewhere. | “Lightweight library” marketing |
| **Support place** | Place that holds ground (or weight) another node projects from. | Customer support desk |
| **Work place** | Place that executes work a light center will not carry. | Job path “work plane” (different word: *plane* vs *place*) |
| **Vertical axis** | Authority and meaning (home up, projection, hop home). | Package layer stack alone |
| **Horizontal axis** | Bodies in the place registry (workers, hosts, resources). | REST surface fan-out alone |
| **Tunnel** | Trusted path between places after home is known (later seed). | SSH product feature only |

---

## 6. Packaging and seed

| Term | Intended meaning | Do not use for |
|------|------------------|----------------|
| **Packaging** | Settings, env, profiles, modes as **seed and wire** — storage paths, ports, pool widths, secrets. | Structure law after definition load |
| **Profile** | Deployment / composition preset that **seeds** definition or membership. | Permanent dual structure king |
| **Boot mode** | Entry shape (cli, server, embedded, …) that **seeds** definition id. | Structure status phase |
| **Boot** | Machine up: phases that bring the system to life before or around structure ready. | Structure manager materialize (related but not the same care) |
| **Env** | `PALM_*` and settings fields: packaging stays; structure-shaped flags **seed or die**. | Peer OR with composition after load |

---

## 7. Design practice (this vault)

| Term | Intended meaning | Do not use for |
|------|------------------|----------------|
| **Intended architecture** | Target shape of Palm described in this vault. | Accidental as-built digs |
| **As-built** | What code does today. Optional contrast only ([appendix/as-built-notes.md](appendix/as-built-notes.md)). | Silent override of intended law |
| **C4** | Context · container · component · code altitudes for diagrams and notes. | A fourth layer of Palm packages |
| **Container** (C4) | Process or deployable unit (e.g. one Palm process, storage). | IoC DI container only |
| **Component** (C4) | Major internal part (structure management, job path, planes, …). | Every Python class |
| **View** | Cross-cutting architecture cut (lifecycle, deployment, …). | REST view-model |
| **Registry extension** | Definition at the edge; consumer holds registry and runs one loop. | Central hub that names every concrete forever |
| **Seat DI** | Inject interfaces and subsystems needed; not ambient shell. | Service locator host dig |
| **Residual** | Named temporary dual or open edge — debt, not architecture. | Permanent soft dual for green CI |
| **Fail closed** | When admission or policy says no, refuse; do not soft-open. | Fail the whole process boot always |

---

## 8. Aliases and retirements

| Prefer (architecture) | Accept as vision / was | Avoid in architecture law |
|----------------------|------------------------|----------------------------|
| Structure definition | Assembly definition (vision); DNA (theme was) | “Profile is the structure” |
| Structure reconciler | AssemblyEngine (was) | Host readiness flag |
| Structure manager | system.assembly seat/loop (was) | Dashboard-only admission |
| Structure status | AssemblyStatus (was) | Soft definitions ready |
| Interface | Port (code) | Digging composition root |
| Business definition | Flow / process definition | Structure definition |
| Dual readiness path | Pretender (metaphor); `READINESS_EDGES` | Corridor police as forever design |
| Structure materialize path | Household (metaphor); `StructureEffectPort` | Business skip of admission |
| Effect port | `EffectPort` (protocol; was `AssemblyEffectPort`); `StructureEffectPort` (default hands) | `Assembly*` on the apply protocol |
| Business path needing admission | Citizen (metaphor); `GATED_PATHS` | — |
| Admission inventory | `admission_inventory` / `admission_inventory_snapshot` | Guard tower as architecture |
| Published admission (façades) | Peasants’ oath; `*.published_admission` | Host dig for readiness |
| Surface uses host / port | Fealty (metaphor) | Kernel dig as product path |
| Business start / continue | Market day (metaphor) | — |
| Seed (chooser, not king) | DNA (theme lag); `PALM_STRUCTURE_DEFINITION_ID`; `structure_definition_id` | Packaging as structure law after load |
| Place registry | Place book (theme lag); `PlaceEffectPort` / `InProcessPlaceRegistry` | Address book as architecture |

---

## 9. How to grow this glossary

1. New term needed by a note → add a row here **first**.  
2. Conflict with PALM.md → resolve deliberately (update PALM or note lag).  
3. Metaphor → [appendix/metaphor.md](appendix/metaphor.md), not this table.  
4. José locks contested renames. **Locked 2026-08-17:** packages `palm.core.structure` / `palm.system.structure`; types `StructureDefinition` / `StructureEngine` / `StructureStatus` / `StructureSeat`. Vision/ADR keep the word assembly.

**Next consumer of this glossary:** package diagram under [c4-code/diagrams/](c4-code/diagrams/).
