# VISION 0.56 — Workload plane (WorkloadEngine + runtimes)

**Status:** 📋 **Scout** — foundation landed (core engine + WorkloadLeaf + runners + product path). Adopt remainder is open minor [VISION-0.71](VISION-0.71.md). After [VISION-0.55](closed/VISION-0.55.md) **Reactive Interests**. Session watches: [VISION-SESSION-PLANE](closed/VISION-SESSION-PLANE.md) (may overlap late).  
**Theme:** First-class **isolated workloads** — one-shot **runs** and long-lived **services** — via pure **WorkloadEngine**, pluggable **WorkloadRuntimes**, **hosts**, **execution-domain CQRS** (`ExecutionService.workloads`), **WorkloadLeaf** (opens **wait interest**), optional resource **blueprints**, and **event-driven composition** (pipelines). NeonRoot becomes one runtime, not the product.

> *Palm orchestrates life. Workloads are where foreign work lives. Providers are how we speak to systems. CQRS is how edges ask. Events are how the graph continues. Never collapse those layers.*

**ADR:** [024-workload-engine.md](../adr/024-workload-engine.md) (accept with **0.56.0**).  
**Builds on:** [ADR-003](../adr/003-provider-apps.md) · [ADR-009](../adr/009-service-cqrs-contributors.md) · [ADR-022](../adr/022-neonroot-provider.md) · [ADR-023](../adr/023-hermetic-jobs.md) · [ADR-025](../adr/025-reactive-interests.md) · [EVENT-PLANE](../EVENT-PLANE.md) · [VISION-0.54](closed/VISION-0.54.md) · [VISION-0.55](closed/VISION-0.55.md) · [VISION-GROVE](VISION-GROVE.md).  
**Scale meaning (updated):** Workload is the **horizontal** axis — the **place book**. Vertical home/authority is [VISION-ASSEMBLY](VISION-ASSEMBLY.md). Reach later is [VISION-TUNNELS](VISION-TUNNELS.md). Tiny model process as a place: [VISION-TINY-LLM](VISION-TINY-LLM.md) (needs; not this theme’s spawn remainder). See [PALM.md §8](../PALM.md).

---

## 0. Place book (how to read this theme now)

This theme still delivers isolation engines and runners.  
**Updated reading:** every durable foreign body Palm may **mean** should become a **named place** (spawn or adopt). Readiness in the book gates honesty. That is how multi-process (local and remote) stays controlled without inventing a second lock religion inside orchestration.

| Workload (this theme) | Not workload |
|-----------------------|--------------|
| Horizontal bodies and availability | WorkIntent claim law (work plane · 0.62) |
| Runner adapters | Assembly DNA / definition-ready |
| Place lifecycle events | Business flow rules |

---

## 1. Problem

1. **NeonRoot-as-provider** conflates isolation with data I/O (kv, rest, postgres).  
2. **Prod / Compose** cannot require host Podman + vault; DinD is fragile.  
3. **Cold spawn only** hurts Assist run-code; warm load+exec is a first-class need.  
4. Growth needs **host** (unsafe, optional), **SSH**, **peer Palm**, **K8s**, **GPU placement** — one Spec.  
5. **Services** Palm starts must be **consumed via providers**, not a parallel service API.  
6. Edges (REST/MCP/Assist) must not call core engines ad hoc — **CQRS** is the Palm way.  
7. Finishing a workload must be able to **start pipelines/flows** without teaching WorkloadEngine about patterns.

---

## 2. Naming (normative)

| Term | Meaning | Anti-pattern |
|------|---------|--------------|
| **Workload plane** | Product capability | “Container feature” |
| **WorkloadEngine** | Pure core lifecycle engine | RuntimeEngine (collides with surfaces) |
| **WorkloadSpec** | Portable intent (JSON-serializable) | Runtime-native YAML as core type |
| **Workload** | Live allocation + status + handle; a **place** in the book | Confusing with Job or Session |
| **Place book** | Registry of named places Palm may use | Ad-hoc URLs outside the book |
| **WorkloadRuntime** | Adapter implementation | “Provider” for isolation |
| **Host** | Where capacity lives (one kind of place constraint) | Full CMDB |
| **Provider** | ResourceEngine backend (interfaces) | Using provider for raw `exec` forever |
| **Hermetic** | *Policy*: not in Palm process | Synonym for NeonRoot |
| **`palm.runtimes`** | Surfaces (CLI, server, MCP) | Workload backends |
| **WorkloadExecutionService** | Under **execution** domain (peer of flows/providers/processes); policy + CQRS | Top-level `services/workloads` god domain; fat reimplementation of engine |

**One-liner:** *Allocate with WorkloadEngine · Speak with providers · Drive graphs with orchestration · Expose with CQRS · React with events.*

---

## 3. Architecture (full stack)

```text
  Assist / REST / MCP / Portal / palm provider (peer)
              │
              ▼
       CQRS commands/queries  (execution domain contributor)
              │
              ▼
  ExecutionService
    .flows | .processes | .providers | .workloads
              │
              ▼
  WorkloadExecutionService     ◄── policy, authz, placement, owner bind
              │                    (palm/services/execution/workloads/)
              ▼
       WorkloadEngine (core)   ◄── pure: place/exec/status/stop
              │
       ┌──────┴──────┐
       ▼             ▼
  Host registry   WorkloadRuntime registry
       │             │
       │        host | neonroot | ssh | palm | k8s | …
       │             │
       └──── WorkloadSpec ──── adapts per runtime

  Patterns (wizard / DAG / pipeline)
       WorkloadLeaf ──► service/CQRS or test double engine
       ResourceLeaf ──► ResourceEngine (+ optional blueprint → workloads)

  Parallel (not inside WorkloadEngine):
       ResourceEngine + providers  ← consume interfaces / blueprints
       OrchestrationEngine         ← jobs, wizards, DAG, pipelines
       Event bus (runtime.event)   ← workload.* → triggers → new flows
       Session plane (0.55)        ← subscribe by session_id / workload_id
```

### 3.1 Package layout (normative)

Same spirit as providers / storages — **not** a separate git repo for v1.

```text
palm/core/workload/                 # PURE — base contract + engine
  engine.py, spec.py, result.py, handle.py
  protocol.py                       # WorkloadRuntime ABC/Protocol  ← “base”
  registry.py

palm/common/workload/               # coordination only (no driver clients)
  placement.py, ownership.py, events.py
  # optional: projection helpers — NOT neonroot/ssh/k8s

palm/runners/                       # concrete WorkloadRuntime adapters
  _apps.py                          # INSTALLED_RUNNERS
  host/, neonroot/, ssh/, palm/, k8s/, …
  # each: runtime.py + registry.py

palm/services/execution/workloads/  # product CQRS (ExecutionService.workloads)
  service.py, bindings/cqrs/…

palm/patterns/… WorkloadLeaf        # BT contract with engine/port
```

| Piece | Package | Not |
|-------|---------|-----|
| **Base** protocol + engine | **`core/workload`** | `common` as home of the ABC |
| Policy / placement glue | **`common/workload`** | Driver SDKs |
| host, neonroot, ssh, peer palm | **`palm/runners/*`** | Top-level `services/workloads` |
| CQRS / REST | **`execution/workloads`** | Edges calling core directly |
| Separate runners git repo | **No for v1** | Optional install extras much later |

**Core purity**

| In core | Out of core |
|---------|-------------|
| Spec, Result, Handle, Status | neonroot, docker, k8s, paramiko clients |
| Engine + in-memory index | Durable workload rows (service/common later) |
| `WorkloadRuntime` protocol + registry | Host inventory storage backends |
| Transition validation | Image builds, registries |

Runners register at bootstrap (`INSTALLED_RUNNERS` autoload → `registry.py` → `workload_runtime_registry`).

### 3.2 Layer duties (error-proofing)

| Layer | May | Must not |
|-------|-----|----------|
| **WorkloadEngine** | Allocate, exec, stop, status | Parse HCL, call HTTP APIs of business services, start Palm flows |
| **WorkloadExecutionService** | Enforce policy, pick host, bind owner, emit domain intent | Import neonroot; live outside `services/execution/` |
| **WorkloadRuntime** | Map Spec → native ops | Mutate Palm job state directly |
| **Provider** | Speak SQL/HTTP/… | Own process isolation long-term (façade OK) |
| **Orchestration / pipeline** | Sequence steps, wait on events | Shell to docker |
| **Inbound / triggers** | On `workload.*` start flows | Live inside WorkloadEngine |
| **Surfaces** | CQRS/REST/MCP only | Reach into runtime adapters |

---

## 4. WorkloadSpec (universal, versioned)

Specs are **JSON-serializable**, append-friendly (`spec_version: 1`).

### 4.1 Fields

| Field | Required | Purpose |
|-------|----------|---------|
| `spec_version` | yes | Schema evolution |
| `kind` | yes | `run` \| `service` \| `workspace` (warm exec box; may alias service) |
| `image` / `image_ref` | kind-dependent | Portable or runtime-native |
| `command` | for run/exec | **argv list only** — no shell strings in v1 |
| `workdir` | no | Relative path inside allocation |
| `seed` | no | `none` \| `{type: uri\|git_archive\|bind, …}` |
| `env` | no | Non-secret key/values |
| `secrets_ref` | no | **Refs only** — never inline secret material in Spec logs |
| `ports` / `expose` | service | Publish hints |
| `health` | service | Readiness probe definition (abstract) |
| `timeout_s` | no | Hard deadline for run/exec |
| `resources` | no | Hints: `cpu`, `memory`, `gpu`, `gpu_memory` |
| `isolation` | yes | `host` \| `hermetic` \| `best_effort` |
| `lifecycle` | yes | `job` \| `session` \| `lease` |
| `labels` | no | Placement: `accelerator=cuda`, `zone=…` |
| `placement` | no | Soft constraints: `host_id`, `runtime`, `reject_runtimes` |
| `mesh` | no | `max_hops`, `prefer_local` |

Runtimes **must reject** Specs they cannot honor when `isolation=hermetic` (e.g. host runtime).  
Unknown fields: **reject in strict mode**; warn+ignore only if `PALM_WORKLOAD_SPEC_LAX=1` (dev).

### 4.2 Results & handles

```text
WorkloadResult (run / exec)
  exit_code, stdout_tail, stderr_tail, duration_s
  artifact_refs[]          # URIs, not blobs on the bus
  runtime_meta             # small

WorkloadHandle (service / workspace)
  workload_id, base_url?, endpoints{}, connection_hints{}
  # connection_hints feed providers — never replace providers
```

---

## 5. Lifecycle & state machine

```text
PENDING → STARTING → RUNNING (run)
                   → READY (service/workspace)
                   → STOPPING → STOPPED
                   ↘ FAILED
```

**Invariants:**

1. Terminal states are **STOPPED** or **FAILED** (no resurrection without new id).  
2. **exec** only on READY workspace/service (or defined run-in-place policy).  
3. **stop** is idempotent.  
4. Owner cancel ⇒ engine **stop** (best-effort + record leak if runtime dies).  
5. No silent status skip (e.g. PENDING → READY without STARTING) except documented fast-path for pure local mocks.

### 5.1 Ownership (mandatory)

| Owner | Stop when | Use |
|-------|-----------|-----|
| `job_id` | Job cancel/fail/success (if lifecycle=job) | One-shot CI steps |
| `instance_id` / session | Session cancel / process end | Warm run-code, sidecars |
| `lease_id` | TTL / explicit stop | Ops-held GPU box |

A workload records **who started it** (`created_by_palm`, `owner`). Remote Palm B stores `origin_host` + lease token so A can stop.

### 5.2 Compensation

Any Palm compensation / cancel path that started a workload **must** enqueue stop (same as nested child cleanup). Tests required.

---

## 6. Hosts & placement

### 6.1 Host record

```text
Host {
  id, kind: local|ssh|palm|k8s_context|…,
  endpoint?, auth_ref?,
  labels: {gpu, zone, …},
  enabled, health,
  allowed_runtimes: […],
  max_hops?  # for palm kind
}
```

v0: single implicit host `local`.  
v1: configured list (settings / composition / storage later).

### 6.2 Placement algorithm (normative sketch)

1. If `placement.host_id` set → use if enabled + healthy.  
2. Filter hosts by `labels` / `resources` (e.g. `gpu>=1`).  
3. Filter runtimes by `isolation` policy and host `allowed_runtimes`.  
4. Prefer: explicit runtime → neonroot if hermetic → best_effort fallbacks.  
5. If none → **fail closed** with actionable error (doctor hints).

**Never** auto-enable host runtime to “make it work.”

---

## 7. Runtimes (extension catalog)

| Runtime | Default | Trust | Notes |
|---------|---------|-------|-------|
| **host** | **OFF** | Low | Subprocess + data_dir workdir; dogfood only |
| **neonroot** | if CLI present | Medium–high | Cold spawn + warm load/exec |
| **ssh** | OFF + allowlist | Low–medium | Remote exec or remote neonroot |
| **palm** | peer allowlist | Medium | Delegate Spec via palm provider / HTTP |
| **docker** / **podman API** | optional | Medium | Socket mount; no full NeonRoot |
| **k8s** | later | High (cluster policy) | Jobs/Pods/GPU operators |
| **cloud sandbox** | later | Vendor | e2b-class, etc. |

### 7.1 Expected workloads (same Spec)

| Use case | Spec sketch |
|----------|-------------|
| Assist run-code | workspace + exec, image palm-ci |
| Hermetic CI | run, isolation=hermetic, neonroot/k8s |
| GPU kernel | run, resources.gpu, labels.accelerator |
| Terraform apply | run, image hashicorp/terraform, long timeout |
| Postgres sidecar | service + blueprint → postgres provider |
| Peer GPU Palm | runtime=palm, host=gpu-sidecar |
| SSH lab | runtime=ssh, host=lab-01 |

---

## 8. CQRS & execution domain (normative)

Edges **must not** call `WorkloadEngine` directly in product code paths.

### 8.1 Why under **ExecutionService**, not a top-level WorkloadService

Palm already groups “make the system run” under **execution**:

```text
ExecutionService
  .flows      → FlowExecutionService
  .processes  → ProcessExecutionService
  .providers  → ProviderExecutionService
  .workloads  → WorkloadExecutionService   # NEW
```

| Put workloads here | Not here |
|--------------------|----------|
| **`services/execution/workloads/`** | `services/workloads/` as peer of assist/design |
| Same host wiring as flows/providers | New ApplicationHost service slot unless needed |
| Same cancel/session affinity as jobs | Separate product domain (Design-like) |
| CQRS contributor beside execution flows | Parallel “Workload” brand in MCP catalog |

**WorkloadExecutionService** stays thin: policy, placement, owner bind, engine call, events — mirrors **ProviderExecutionService**, not a second orchestrator.

Composition capability remains `workloads` (or nested under execution profile flags).

### 8.2 Service responsibilities

`WorkloadExecutionService`:

- Resolves placement + policy  
- Binds owner (session/job from context)  
- Calls **WorkloadEngine**  
- Optionally persists projection rows  
- Emits/forwards events  

### 8.3 Commands (v1)

| Command | Effect |
|---------|--------|
| `workload.start` | Spec → STARTING → RUNNING/READY |
| `workload.exec` | argv (+ optional files) on READY workspace |
| `workload.stop` | Idempotent stop |
| `workload.cancel` | Alias/policy for owner-driven stop |

### 8.4 Queries

| Query | Effect |
|-------|--------|
| `workload.get` | By id |
| `workload.list` | Filter by session/job/host/status |
| `workload.hosts` | Host registry view |
| `workload.runtimes` | Doctor-oriented runtime status |

### 8.5 Schemas & transport

- Register via **execution** **ServiceCqrsContributor** ([ADR-009](../adr/009-service-cqrs-contributors.md))  
- REST under `/v1/api/workloads/…` (or nested under execution prefix if that’s house style)  
- MCP / **assist aliases** / palm provider actions (prefer aliases — [VISION-0.31](closed/VISION-0.31.md))  
- Authz: same principal model as execution; host runtime requires explicit capability flag  

### 8.6 Idempotency

- `start` accepts optional `idempotency_key` (owner + key → same workload id)  
- `stop` / `exec` document retry semantics  
- Peer palm: propagate idempotency_key  

---

## 9. Reactive composition (pipelines & flows)

**WorkloadEngine never starts pipelines.**  
**Orchestration + inbound/triggers do.**

```text
workload.stopped | workload.failed | workload.ready
  → runtime.event (orchestration bus — EVENT-PLANE)
  → inbound bindings / on_event triggers / work-drain
  → SubmitFlow / pipeline / process
```

| Direction | Mechanism |
|-----------|-----------|
| Pipeline **includes** a workload | DAG/wizard step → CQRS `workload.start` / façade resource |
| Workload **triggers** pipeline | Trigger on `workload.stopped` (+ filter labels) |
| GPU leaf on remote Palm | Placement runtime=palm; same commands |
| Fan-out | Multiple starts; join in DAG, not inside engine |

**Dogfood (required for theme close):**

1. Flow A runs workload (e.g. terraform or ruff).  
2. On `workload.stopped` with exit 0, trigger flow B (pipeline stage or notify).  
3. On failure, trigger failure path / compensation.  

Public event payloads: **small** — `workload_id`, `status`, `exit_code?`, `owner`, `labels`, `host_id` — **not** full stdout (use artifact_ref / inspect).

---

## 10. Providers & blueprints

```text
ProviderDescriptor.workload?:
  supported: bool
  runtimes: [...]
  blueprint(resource_params, context) -> WorkloadSpec
  connection(handle, context) -> provider_params
```

**Rules:**

1. No blueprint ⇒ never auto-start (managed services).  
2. Blueprint start only if policy allows runtime (host still default off).  
3. Connection mapping is pure data (DSN, URL) — provider invoke unchanged.  
4. Teardown only if Palm created the workload (`created_by_palm=true`).  

Palm provider actions: `workload.start|exec|status|stop|list` for mesh and MCP symmetry.

---

## 11. Patterns, WorkloadLeaf & contract tests (normative)

### 11.1 WorkloadLeaf defines the pattern contract **with** the engine

When implementing **core WorkloadEngine**, ship **in the same arc** (or immediately adjacent slice):

1. **Core unit tests** — fake `WorkloadRuntime`, assert Spec → status machine → Result/Handle.  
2. **`WorkloadLeaf`** (BT leaf in patterns, peer spirit of `ResourceLeaf`) — drives start/exec/wait/stop via engine **protocol** (or test double implementing the same surface).  
3. **Contract tests** — leaf + fake runtime + real engine: isolation policy, owner bind, terminal wait, cancel/stop.  

That freezes the **integration contract** early:

| Contract surface | Guarantees |
|------------------|------------|
| `WorkloadSpec` / Result / Handle | Serializable intent and outcomes |
| Engine API | start / exec / status / stop semantics |
| Leaf behavior | How graphs wait, fail, and complete |
| Runtime Protocol | What adapters must implement |

**Do not** land a large engine with only free functions and no leaf — patterns will invent divergent call shapes.

Later: product paths prefer **WorkloadExecutionService/CQRS**; leaf in production may call service or a narrow port. **Tests** may inject the engine/fake directly to keep pattern tests fast.

### 11.2 Pattern integration matrix

| Integration | Role |
|-------------|------|
| **WorkloadLeaf** | Primary BT contract; wizard/DAG/pipeline nodes |
| Resource façade | Back-compat `provider: neonroot` → execution.workloads → engine |
| `step_kind: workload` | Definition sugar materializing WorkloadLeaf |
| DAG hermetic node | Spec + wait until terminal (uses leaf or shared helper) |

Leaves **wait** on status like resources today; tick budget via existing job runner — no infinite spin.

---

## 12. Session plane (0.55) integration

| Need | Mechanism |
|------|-----------|
| Progress during long run | Session subscribe + `workload.*` events |
| List attached boxes | Query workloads by `instance_id` |
| Portal auto-clean | Session cancel → stop all owned workloads |
| Multi-tab | Same session_id filter |

---

## 13. Security & safety (defaults fail closed)

| Control | Default |
|---------|---------|
| host runtime | **OFF** |
| ssh runtime | **OFF** + host allowlist |
| palm peers | **Allowlist** URLs only |
| command | argv arrays; no shell |
| secrets | refs; redacted logs |
| hermetic | cannot select host runtime |
| mesh hops | `max_hops` default **1** |
| image allowlist | optional per host; recommended for host/ssh |
| multi-tenant host | **unsupported** — document |

Doctor must show: runtimes, host-enabled **warning**, peer list, recent placement failures.

---

## 14. Observability

- Structured logs: workload_id, host, runtime, owner (no secrets)  
- Metrics (later): starts, failures, duration by runtime  
- Artifacts: tails capped (existing neonroot tail size); full logs via ref  
- Align with event plane doctor table  

---

## 15. Error model

| Class | Example | Operator action |
|-------|---------|-----------------|
| **PolicyDenied** | host disabled, hermetic+host | Enable runtime or change isolation |
| **PlacementFailed** | no GPU host | Add host / labels |
| **RuntimeUnavailable** | neonroot missing | Install or best_effort |
| **StartFailed** | image pull / spawn | Doctor + runtime logs |
| **ExecFailed** | non-zero exit | Result on state; trigger failure path |
| **StopFailed** | leak | Alert; mark orphan; reap job |
| **MeshRejected** | hop/allowlist | Config peers |

All CQRS errors map to stable codes for Assist CTAs (resume, doctor, open host config).

---

## 16. Migration (0.53–0.54 → 0.56)

| Phase | Action |
|-------|--------|
| A | Engine + host + neonroot adapter; façade keeps `run_script`/`spawn` |
| B | Assist run-code optional warm path via service |
| C | CQRS + REST; MCP/assist aliases |
| D | Events + trigger dogfood |
| E | Blueprints dogfood |
| F | palm remote runtime |
| G | Deprecate dual path; MIGRATION-0.56 note |

**Compatibility:** existing resource definitions keep working until G.  
**No** big-bang delete of neonroot provider in 0.56.1.

---

## 17. Relationship to other themes

| Theme | Relation |
|-------|----------|
| 0.54 Hermetic Jobs | Spec + DAG semantics; dogfood proven |
| 0.55 Session plane | Owners + live watches |
| **0.56 Workload plane** | This document |
| Docs domain | Consumer of workloads later |
| PD-022 adapters | Prefer workload images over in-process drivers when heavy |

---

## 18. Non-goals (explicit)

- WorkloadEngine starts flows/pipelines itself  
- HCL/Terraform engine in core  
- Folding CLI/server/MCP into WorkloadEngine  
- Full CMDB / cost accounting v1  
- Streaming multi-MB logs on event bus  
- Claiming host runtime is multi-tenant safe  
- Mandatory NeonRoot in Docker image  
- Replacing ResourceEngine  

---

## 19. Slice plan (lock at 0.56.0; adjust after 0.55)

| Patch | Deliverable | Hardens against |
|-------|-------------|-----------------|
| **0.56.0–0.56.2** | ADR-024 accepted; core engine + Spec/Result/status + registry; **WorkloadLeaf** + contract tests; glossary | Naming drift · core purity · divergent pattern APIs — **landed as one coherent foundation** |
| **0.56.3–0.56.4** | **host** runtime default **OFF** + settings + doctor; **neonroot** WorkloadRuntime (`palm/runners/`); BaseRuntime wires engine | Accidental exec · dual isolation model — **runners cut landed** (provider façade dogfood still until CQRS/collapse) |
| **0.56.5–0.56.6** | Host warm **workspace**+exec; **`execution.workloads`** + CQRS commands/queries; hosts v0 | Cold-only UX · edge→engine bypass — **product path landed** (REST/MCP aliases later) |
| **dogfood** | Wizard `step_kind: workload` + **run-python** (host/neonroot/auto); replaces complex run_script loop | Divergent dogfood contracts |
| **0.56.4b** | **Delete neonroot provider** — runner + WorkloadEngine only; hermetic dogfood retargeted | Dual isolation — **cut** |
| **trust base** | **`local` always-on runner**; `WorkloadRuntime.health()`; `engine.doctor()` | Engine not trusted without neonroot/host — **landed** |
| **0.56.7** | Richer host registry + placement + capability flag | Ad-hoc host strings |
| **0.56.8** | Session cancel hooks / ownership product wiring | Blind long runs |
| **0.56.9** | Trigger dogfood: `on_workload` + workload.stopped → follow-up flow | Missing reactive path — **landed** |
| **0.56.10** | Provider blueprint protocol + one dogfood | Spin-up without consume |
| **0.56.11** | Palm provider workload.* + runtime=palm allowlist | Mesh without auth |
| **0.56.12** | ssh **or** k8s (demand) + GPU label placement test | Single-runtime trap |
| **0.56.13** | MIGRATION, assist aliases, retire unsafe dual paths | Dual source of truth |

---

## 20. Success criteria (theme exit)

1. Run-code on **host (enabled)** or **neonroot** without definition rewrites.  
2. Core **zero** neonroot/docker/k8s imports.  
3. Host runtime **off** by default; doctor warns when on.  
4. All product starts go through **execution CQRS** (tested); leaf contract tests green.  
5. **workload.stopped** can trigger a second flow/pipeline (dogfood).  
6. Service workload + **provider** consume dogfood.  
7. Session/job cancel stops owned workloads (test).  
8. Peer palm placement lab-tested with allowlist.  
9. Hermetic policy rejects host.  
10. `just check` green; CI can require neonroot for hermetic jobs.

---

## 21. Open decisions (close in ADR accept)

1. ~~Package layout~~ → **locked** §3.1 (`core/workload`, `common/workload`, `runners/*`, `execution/workloads`)  
2. `workspace` vs `service` enum (alias vs distinct kind)  
3. Façade deprecation timeline for `provider: neonroot`  
4. Secret ref scheme (reuse existing auth/secrets if any)  
5. Default `max_hops` and peer auth mechanism  
6. Whether `execution.workloads` is always-on or composition-profile gated only  
7. Production WorkloadLeaf calls service vs engine port (tests always use port/fake)  

---

## Horizon

Workload plane is **place** (and peer `runtime=palm`) under [**The Grove**](VISION-GROVE.md). It **consumes** [0.55](closed/VISION-0.55.md) wait interest (`kind=workload`) and emits lifecycle events for the matcher — completers announce themselves; graphs open interest. Prefer designs where a second Palm is only trust + target id + lifecycle events, not a new integration grammar.

---

*Allocate places. Speak through providers. Command via CQRS. Continue via events. Grow runtimes without growing core.* 🌴⚙️
