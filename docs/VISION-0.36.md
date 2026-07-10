# VISION 0.36+ — Reactive Platform Evolution

**Palm Engine long-horizon vision** (0.36 through ~0.39)

| Field | Value |
|-------|--------|
| **Status** | Charter — **foundations landed in 0.36–0.39**; polish/debt open (see §12a). **Forward plan:** [VISION-0.40](VISION-0.40.md) |
| **Date** | 2026-07-10 (status refresh with 0.39.0 cut) |
| **Ship baseline** | **0.39.0** — analytics + work/journal foundations + dashboards + palm system inspect |
| **Depends on** | [VISION-0.33](VISION-0.33.md) · [VISION-0.34](VISION-0.34.md) · [VISION-0.35](VISION-0.35.md) · [ADR-001](adr/001-compositional-power-resources.md) · [ADR-011](adr/011-local-document-resources.md) · [AGENTS.md](../AGENTS.md) |
| **Spirit** | Embrace necessary complexity for **decade-scale robustness**; never accidental complexity |

---

## 1. Why this document exists

Through 0.30–0.35 Palm became:

- **Operator-remote** (Assist tool|chat, menu/open, Portal/WS)
- **Definition-driven data** (resources, kv/file, design publish)
- **Exposure analytics** (published datasets, present profiles, thin `/analytics`)
- **Example packs** (`examples/definitions/<pack>/` with ordered `__init__.py`)

Dogfood (especially **todos**: interact → kv → analytics) proved the spine **and** revealed the next structural gaps:

1. Views and refresh are still **manual or materialize-only**
2. Flows want to be **hooked, scheduled, or reactive to resources**
3. Events are a **live bus + selective outbox**, not a durable “run when able” work model
4. Tiered KV is a **document store**, not an event log

This charter gathers the agreed evolution: **data plane + control plane + deferred work**, without a Bot layer, without OLAP-in-core, without gluing complexity into examples.

---

## 2. Enduring principles (non-negotiable)

From the Palm constitution, applied to this arc:

| Principle | Application here |
|-----------|------------------|
| **Single responsibility** | Analytics reads; Execution runs; Host drains work; EventEngine fans out live signals |
| **Core purity** | Core holds pure types + live bus + orchestration math — **not** flow submit, cron, or storage backends |
| **Registry / definition extension** | Triggers, exposure, view specs live on definitions — not if/else in runtimes |
| **Minimal magic** | Explicit WorkIntent, explicit triggers, explicit coalesce keys |
| **Human-first + truth-seeking** | Operator can see *pending work* vs *last success*; no silent side effects |
| **Examples set the standard** | Definition-only packs (resource + transform steps); no junior commit-hook glue |

**Embrace complexity where it pays for robustness:** durable intents, offsets, coalesce, depth limits, schema contracts.  
**Refuse complexity that duplicates brains:** no second Job engine in core, no warehouse, no Portal-as-BI.

---

## 3. North-star architecture

```text
                    DEFINITIONS (contracts)
         Flow / Process / Resource / (later) Dashboard
                           │
     ┌─────────────────────┼──────────────────────────┐
     │                     │                          │
     ▼                     ▼                          ▼
  TRIGGERS            RESOURCES                  ANALYTICS
  schedule            facts / views              describe / query
  on_flow             (kv, file, …)              present profiles
  on_resource                                    (raw|table|series|kpi)
     │                     │                          ▲
     │                     │ put/delete               │ read
     │                     ▼                          │
     │              ResourceEngine ──emit──► EventEngine (live)
     │                     │                    │
     │                     │                    └──► WorkIntent enqueue (durable)
     │                     │                              │
     │                     │                    when Host is able
     │                     │                              ▼
     └─────────────────────┴──────────────────► Execution (jobs / flows)
```

### One sentence

> **Resources hold state; events signal change; work intents defer reaction; execution runs flows when the host is able; analytics reads state.**

### Android analogy (product semantics)

| Android | Palm |
|---------|------|
| Enqueue work request (alarm or trigger) | Enqueue **WorkIntent** at schedule or change time |
| WorkManager runs Worker **when able** | Host **drains** intents when workers/storage ready |
| Small Intent extras | Small payload: refs, keys, hash — **not** full documents |
| Unique work / REPLACE | **coalesce_key** on intents |

Push ≠ execute. **T_trigger / T_enqueue / T_execute** are distinct.

---

## 4. Layer placement

| Layer | Owns | Does **not** own |
|-------|------|------------------|
| **`palm/core/event`** | `Event`, `EventEngine` live pub/sub, interceptors | Durable multi-consumer log, flow submit |
| **`palm/core/work`** (proposed) | Pure `WorkIntent` value type | Store, drain, constraints |
| **`palm/core/resource`** | Invoke; enough result metadata to emit change | Trigger policy |
| **`palm/core/orchestration`** | Jobs, `RunResult`, apply_result | Cron, WorkManager |
| **`palm/common/events`** | Outbox, reliable publish, journal evolution | Present profiles |
| **`palm/common/work`** (proposed) | Intent store, claim/ack, coalesce | Business rollups |
| **`palm/common/triggers`** (proposed) | Parse definition triggers → enqueue | UI |
| **`palm/services/analytics`** | Published query/present; later virtual views | ETL, schedules |
| **`palm/services/execution`** | Run flows/processes | “When able” policy |
| **`palm/app/host`** | Drain services, schedule ticks, constraints | Resource schemas |
| **Runtimes** | REST/WS/MCP/static thin adapters | Product policy |

**No fat `WorkEngine` in core** that both queues and runs flows.  
**Name clarity:** *WorkIntent + queue + drain* — not a second orchestration engine.

---

## 5. Data plane evolution (0.35 → 0.36+)

### 5.1 Settled (0.35)

- Published resources via `metadata.analytics`
- AnalyticsService: gate → invoke (read allowlist) → normalize → present
- Profiles: `raw` | `table` | `series` | `kpi`
- Palm dogfood: **todos** pack (flows + resources), not sales BI
- Definition packs under `examples/definitions/<name>/`
- Transform `count_by` for definition-only rollups
- Thin `/analytics` UI

### 5.2 Virtual views (P0)

**Gap:** Materialized second keys for every rollup.

**Target:** View as **definition contract**:

```yaml
# on ResourceDefinition.metadata.analytics (illustrative)
published: true
kind: view
source: palm-todos          # fact dataset
transform:
  op: count_by
  field: priority
# materialize: false  → evaluate at query time in AnalyticsService
```

| Layer | Work |
|-------|------|
| Exposure parse | Typed `source` / `transform` / `materialize` |
| AnalyticsService | Load source → apply transform registry → present |
| Design / doctor | Validate published views; warn missing schema |

**Principle:** Materialize is an **optimization**; virtual is default for cheap ops.

### 5.3 Schema ↔ field roles (P1)

- Align `output_schema` with analytics semantics (`x-palm-role: dimension|measure` or `analytics.fields[]`)
- `describe()` returns stable field catalog for dashboards and agents
- Series/kpi defaults from roles, not column heuristics alone

### 5.4 Joins (explicit non-goal for Analytics)

- Joins belong in **pipelines/flows** that materialize denormalized facts
- Analytics remains **single-dataset query** until a later, restricted DSL is justified
- Portal/dashboard **never** join in the browser

### 5.5 DashboardDefinition (P2)

- Tiles: `{ dataset, profile, options }` as data
- Thin surface consumes Analytics only
- Design authors dashboards like flows (evolutionary)

### 5.6 Dataset discovery

- Assist menu section **datasets** (alongside flows)
- Doctor: published without schema; view without source; non-read published action

---

## 6. Control plane: triggers (0.36–0.37)

Flows (and processes) declare **how they attach** to the world:

```yaml
# FlowDefinition / ProcessDefinition metadata (illustrative)
triggers:
  - kind: schedule
    cron: "0 2 * * *"        # or interval
    enabled: true
    work:
      coalesce_key: "todo-analytics:nightly"

  - kind: on_flow
    flow: todo-builder
    when: succeeded          # committed / failed later
    work:
      flow_id: todo-analytics  # or implicit self
      coalesce: true

  - kind: on_resource
    resource: palm-todos
    actions: [put]
    work:
      flow_id: todo-analytics
      coalesce_key: "view:palm-todos-by-priority"
      debounce: 5s
```

| Trigger | T_trigger | T_enqueue | T_execute |
|---------|-----------|-----------|-----------|
| **schedule** | Clock due | Write WorkIntent | Drain when able |
| **on_flow** | Lifecycle event | Write WorkIntent | Drain when able |
| **on_resource** | Successful mutating invoke | Write WorkIntent | Drain when able |

**Anti-loops:** debounce, coalesce, trigger depth limit, single-flight per key.

`analytics.refresh.flow_id` becomes a **special case of triggers**, not a dead metadata field.

---

## 7. Work intents: Android-shaped deferred execution (0.36–0.37)

### 7.1 Three primitives

```text
1. Signal     EventEngine.publish(event)           # live, may be best-effort
2. Intent     WorkIntent durable enqueue             # "run this when able"
3. Execution  Orchestration / QueuedScheduler        # job runs
```

### 7.2 WorkIntent (pure core data — proposed)

```text
WorkIntent(
  id,
  kind,              # run_flow | run_process | …
  target,            # flow_id / process_id
  payload,           # small: resource_ref, resource_id, correlation, content_hash
  coalesce_key,      # unique work name (REPLACE semantics)
  not_before,        # schedule
  created_at,
  attempt,
  depth,             # trigger chain depth
)
```

**No I/O in core.** No flow submit in core.

### 7.3 Store + drain (common / host)

| Component | Role |
|-----------|------|
| **WorkIntentStore** (or extended **Outbox** kinds) | Append, claim, ack, fail, list due |
| **WorkDrainer** (extend `OutboxBackgroundService`) | When able → Execution submit |
| **Constraints** | workers_ready, not shutting down, optional storage durable, rate limits |

### 7.4 What we refuse

| Option | Verdict |
|--------|---------|
| Fat `WorkEngine` in core (queue + run flows) | **No** — purity + SRP + duplicates orchestration |
| Only EventEngine handlers become “durable work” | **No** — confuses observers with deferred jobs |
| Park work intents in tiered document KV | **No** — wrong store |

### 7.5 Practical sequence

1. Extend **outbox entry kinds** with `run_flow` (+ coalesce) — fastest path  
2. Drain when able (existing background service pattern)  
3. TriggerRegistry from definitions  
4. `resource.changed` emission  
5. Generalize to journal + consumer offsets if multi-consumer replay is needed  

---

## 8. Event system evolution (0.36–0.38)

### 8.1 Today

| Piece | Reality |
|-------|---------|
| `EventEngine` | In-process pub/sub, sync handlers, interceptors |
| Reliable outbox | Critical types enqueued on publish |
| Outbox processor | External dispatch / recovery |
| Projections | Job board, pattern hooks |

### 8.2 Target semantics (“Kafka-like” without cargo cult)

| Kafka idea | Palm form |
|------------|-----------|
| Durable ordered log | **Event journal / outbox log** on StorageEngine |
| Consumer offsets | Named consumers (drain, webhooks, projections) |
| Replay | Redrive triggers / rebuild projections from offset |
| Compacted topic | Optional **latest-by-key** for `resource.changed` |
| At-least-once | Claim + ack + retry |
| Exactly-once | **Do not promise**; idempotent submit |

### 8.3 Canonical events (illustrative catalog)

| Event | When |
|-------|------|
| `resource.changed` | Mutating invoke success (`put`/`delete`/`write`…) |
| `flow.session.succeeded` / `failed` | Session terminal states |
| `wizard.commit.succeeded` | Commit path (where still used) |
| `work.intent.enqueued` / `claimed` / `succeeded` / `failed` | Work pipeline observability |
| Host / orchestration events | Existing + tighten schemas |

**Payload rule:** refs + action + content_hash + correlation — **not** full document bodies by default.

### 8.4 EventEngine stays live

- Fast path for metrics, projections, optional best-effort sync hooks  
- Must not block resource put with heavy flow submit  
- Interceptor path: **enqueue WorkIntent**, return  

### 8.5 Storage split (critical)

```text
StorageEngine
  ├── platform: definitions, instances, snapshots
  ├── control:  outbox / event_journal / work intents   ← grow this
  └── data:     resource kv (memory | storage | tiered)  ← documents only
```

**Tiered KV is not Kafka.** Hot/cold document cache ≠ consumer log.

---

## 9. Resource ↔ reaction bridge

```text
ResourceEngine.invoke(mutating) SUCCESS
  → Event resource.changed { ref, id, action, hash }
  → TriggerRegistry (on_resource)
  → WorkIntent enqueue (coalesce)
  → (later) drain → flow materialize / notify
```

| Concern | Policy |
|---------|--------|
| Which actions emit | Mutating only by default |
| get/list/fetch | Silent (no storm) |
| Analytics virtual views | No reaction required |
| Analytics materialize views | Subscribe to source `on_resource` or schedule |

---

## 10. Definition-only examples (standard)

**Preferred pack layout:**

```text
examples/definitions/<pack>/
  __init__.py       # ordered register: resources → flows
  resources.py
  builder.py
  analytics.py      # optional interaction flows
```

| Do | Don’t |
|----|--------|
| Resource + transform steps for persist/rollup | Junior commit hooks that reinvent invoke |
| `count_by` and future transforms in **common** | Example-only Python rebuild helpers as product path |
| Relative imports inside packs | `examples.*` glue for bootstrap file load |
| Flows as the interaction surface | Bare published resources with no path to create them |

Bootstrap loads packages first, then flat `*.py` demos ([DEVELOPMENT.md](../DEVELOPMENT.md)).

---

## 11. Cross-cutting gap matrix

| Gap | Product pain | Engine improvement | Suggested train |
|-----|--------------|--------------------|-----------------|
| Virtual views | Manual materialize for rollups | Analytics metadata + transform at query | **0.36** |
| Schema / field roles | Weak series/kpi defaults | describe() catalog from schema | **0.36** |
| Hooked flows | Hand-run follow-ons | `on_flow` → WorkIntent | **0.36–0.37** |
| Scheduled flows | Dead `refresh` metadata | `schedule` → WorkIntent; host tick | **0.37** |
| Resource reactions | No auto refresh | `resource.changed` + `on_resource` | **0.37** |
| Deferred execution | Sync handler temptation | WorkIntent + drain when able | **0.36–0.37** |
| Event durability / replay | Restart loses “should run” | Journal + offsets (outbox evolve) | **0.37–0.38** |
| Dataset discovery | Dual catalogs | Assist menu datasets + doctor | **0.36–0.37** |
| Dashboard product | Dogfood HTML only | DashboardDefinition + thin surface | **0.38–0.39** |
| Joins in analytics | Temptation | **Non-goal**; ETL in flows | — |
| Bot / NL analytics | Temptation | **Deferred** until contracts solid | 0.40+? |
| OLAP in core | Temptation | **Never** | — |

---

## 12. Suggested release trains

### 0.36 — Contracts & virtual data plane

**Theme:** Make analytics and definitions honest without full reactivity.

| Step | Deliverable |
|------|-------------|
| 0.36.0 | This vision + STATUS ladder |
| 0.36.1 | Typed analytics exposure: `source`, `transform`, `materialize` |
| 0.36.2 | Virtual view evaluation in AnalyticsService (count_by + path ops) |
| 0.36.3 | Field roles / describe enrichment from output_schema |
| 0.36.4 | Doctor checks for published datasets |
| 0.36.5 | Assist menu section `datasets` (optional open → describe) |
| 0.36.6 | Todos pack: prefer virtual view for priority; materialize flow optional |

### 0.37 — Work intents & triggers

**Theme:** Android-shaped enqueue / run-when-able.

| Step | Deliverable |
|------|-------------|
| 0.37.0 | WorkIntent pure type (core) + outbox kind `run_flow` |
| 0.37.1 | Coalesce + claim/ack drain in host |
| 0.37.2 | TriggerRegistry: parse schedule / on_flow / on_resource |
| 0.37.3 | `resource.changed` emission on mutating invoke |
| 0.37.4 | Schedule tick → enqueue (not inline submit) |
| 0.37.5 | Depth limits, debounce, storm tests |
| 0.37.6 | Dogfood: todo put → enqueued todo-analytics / virtual invalidate |

### 0.38 — Journal & multi-consumer durability

**Theme:** Control-plane log robustness.

| Step | Deliverable |
|------|-------------|
| 0.38.0 | Event/work journal API (append, read from offset) |
| 0.38.1 | Named consumers (drain, webhooks, projections) |
| 0.38.2 | Optional compacted latest-by-key for resource.changed |
| 0.38.3 | Redrive / replay tools (operator + doctor) |
| 0.38.4 | Observability: pending intents vs last success |

### 0.39 — Dashboard as definition

**Theme:** Presentation product without a second brain.

| Step | Deliverable |
|------|-------------|
| 0.39.0 | DashboardDefinition sketch + ADR |
| 0.39.1 | Tile bind: dataset + profile + options |
| 0.39.2 | Thin dashboard surface (replace dogfood HTML gradually) |
| 0.39.3 | Design propose/validate dashboard (optional) |

*Years beyond:* multi-tenant ACL, warehouse federation, Bot-on-contracts — only after the above spine is boring.

---

## 13. Complexity we explicitly embrace

| Complexity | Why it is worth it |
|------------|-------------------|
| Separate **signal / intent / execution** | Correctness under restart and load |
| Coalesce + debounce + depth | Prevent trigger storms |
| Virtual vs materialize | Cost control without lying in the model |
| Schema + exposure | Agents and UIs share one type story |
| Journal offsets | Replay and multi-consumer without dual-write chaos |
| Definition packs | Examples remain the standard, not the exception |

## 14. Complexity we explicitly refuse

| Complexity | Why refuse |
|------------|------------|
| WorkEngine in core that runs flows | Breaks purity; duplicates orchestration |
| EventEngine as durable job runner | Mixes observers with deferred work |
| Tiered KV as event log | Wrong abstraction |
| Analytics joins / OLAP core | Wrong layer; pipelines exist |
| Bot before contracts | Weak tools thrash (0.31 lesson) |
| Example Python rebuild hooks as architecture | Hides missing engine features |
| Auto-publish all resources | Security / PII |

---

## 15. Success criteria (platform maturity)

Palm has “arrived” on this arc when:

1. **A published view** can be virtual (query-time) or materialized (flow) — declared, not coded ad hoc  
2. **A flow** can be scheduled, hooked to another flow, or react to a resource **via definition triggers**  
3. **Resource put** never blocks on follow-on flow execution; work runs **when the host is able**  
4. **Restart** does not lose “should refresh view” (durable intent)  
5. **Examples** for the happy path are packages of definitions only  
6. **Assist** can navigate datasets as well as flows  
7. **Doctor** tells the truth about stale data and pending work  
8. **Core** remains pure; new weight sits in common/host/services  

---

## 16. Relationship to prior visions

| Vision | Contribution retained |
|--------|----------------------|
| 0.30–0.31 | Assist / design entry; MCP surface discipline |
| 0.32 | WS + Portal human transport |
| 0.33 | Modular present; tool vs chat |
| 0.34 | Operator remote menu/open |
| 0.35 | Analytics exposure plane; no Bot warehouse |
| **0.36+** | Reactive platform: virtual data + triggers + work intents + journal |

---

## 17. How to use this document

- **Implementers:** Pick a train (0.36 / 0.37 / …); open ADRs for WorkIntent store and trigger metadata when code lands  
- **Reviewers:** Reject PRs that put trigger policy in Portal JS, analytics joins, or core flow-submit  
- **Examples authors:** Packs + definition steps first; if you need a hook, file an engine gap  
- **Future self:** Complexity here is **load-bearing**. Do not “simplify” by collapsing signal/intent/execution into one synchronous publish handler  

---

## 18. Closing

Palm should remain:

- **Simple at the core**, powerful at the edges  
- **Definition-driven** for data, navigation, and reaction  
- **Honest about time**: when change happened vs when work ran  
- **Evolutionary**: registries and metadata grow capabilities without rewriting foundations  

The path from 0.35 dogfood to a robust platform is not “more glue in examples.”  
It is **contracts for views**, **intents for deferred work**, and **events that tell the truth**—complexity chosen for longevity.
