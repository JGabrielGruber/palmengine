# VISION 0.40+ — Compositional Mesh & Reactive Completion

**Palm Engine long-horizon vision from 0.40 onward**

| Field | Value |
|-------|--------|
| **Status** | Vision / priority charter |
| **Date** | 2026-07-10 |
| **Ship baseline** | **0.39.0** (analytics plane, WorkIntent/journal foundations, dashboards, palm system inspect) |
| **Prior charter** | [VISION-0.36](VISION-0.36.md) — reactive platform (partially landed) |
| **Spirit** | Dogfood **Palm consuming Palm**; distributed work easy; complexity for robustness, not glue |

---

## 1. Strategic priority (agreed)

### Critical for compositional expansion (P0)

Shared **semantics** + reliable **call path**:

1. **Submit + wait/fetch** (local and remote) — jobs/instances durable  
2. **Same resource contracts** local vs remote (`items`, actions, analytics exposure)  
3. **Recursion / correlation** (parent job, depth)  
4. **Palm provider** as the single brand for “talk to Palm” (run **and** inspect)

### High value for *reactive* composition (P1)

5. **Durable change contract** — events + **journal** (offsets, redrive)  
6. **WorkIntent** on each node — enqueue at trigger time, **run when able**  
7. **Definition triggers** wired in example packs (dogfood, not only unit tests)

### Accelerators, not the definition of composition (P2)

8. **Live push transport** (WebSocket/SSE) for humans **and** palm-provider consumers  
9. Continuous background drain (vs explicit `tick_work`)  
10. Dashboard design authoring, durable dashboard registry  

**WebSocket streaming of outbox/events is strategically aligned** with multi-Palm “feel,” but it is a **transport** on top of the change contract—not a substitute for submit/wait/resources.

```text
Critical path:     invoke + durable jobs + resources (+ system inspect)
Reactive path:     journal + WorkIntent + triggers
Realtime path:     WS/SSE push (optional consumer for provider + Portal)
```

---

## 2. Open debt from 0.36–0.39 (carry into 0.40.x)

Do not start greenfield 0.40 features without finishing or consciously deferring:

| ID | Open item | Suggested train |
|----|-----------|-----------------|
| D1 | Example `metadata.triggers` dogfood (e.g. on resource put) | **0.40.1** |
| D2 | Continuous work drain loop on host (optional profile flag) | **0.40.2** |
| D3 | Trigger debounce / depth limits / storm tests | **0.40.2** |
| D4 | Journal consumers wired for webhooks/projections (named) | **0.40.3** |
| D5 | Doctor embeds `control_plane_status` | **0.40.3** |
| D6 | Assist `open:dataset` / deep link to describe | **0.40.4** |
| D7 | Durable dashboard registry (not only in-process) | **0.41** |
| D8 | Design-service dashboard propose (optional) | **0.41+** |
| D9 | More virtual transform ops beyond `count_by` | **0.40.4** / as needed |
| D10 | Schedule: real cron (beyond `interval_seconds`) | **0.41** |

Foundation that **already exists** and must be extended, not replaced: virtual analytics, WorkIntent store, TriggerRegistry, `resource.changed`, EventJournal, dashboards, palm system-read actions.

---

## 3. North star (0.40+)

> **Palm consumes other Palms through one provider; state changes are durable signals; each node runs follow-on work when able; analytics and dashboards only present published resources.**

```text
                    Palm A                         Palm B (origin)
                 ┌──────────┐                   ┌──────────────────┐
  Human/Agent ──►│ Assist / │  invoke (HTTP)    │  Execution/Jobs  │
                 │ Analytics│ ─────────────────►│  Resources       │
                 │ Provider │  fetch / list_*   │  System inspect  │
                 └────▲─────┘                   └────────┬─────────┘
                      │                                  │
                      │         change contract          │
                      │    (journal / events / WS)       │
                      └──────────────────────────────────┘
                                 optional realtime

  On each node:  resource.changed → triggers → WorkIntent → tick/drain → flows
```

**Extend origin Palm** = B is callable **and** observable; A reacts without busy-poll thrash; B reacts locally via triggers.

---

## 4. Palm provider evolution (composition hub)

| Era | Capability |
|-----|------------|
| **Today (0.39)** | submit_flow/process, invoke_resource, fetch; **system-read** list_*; local + `remote_url` |
| **0.40** | Harden system-read remote envelopes; correlation docs; dogfood remote system dashboard |
| **0.41–0.42** | **Event consumer** (poll journal HTTP first, then WS); map terminal job / resource.changed → unblock wait |
| **Later** | Multi-origin mesh policies, authz per event type |

**Analytics role:** keep making provider-backed resources **pretty** (table/series/kpi, virtual views). No SystemService calls from dashboard shell.

**Do not** invent a parallel `system` provider unless palm provider SRP collapses.

---

## 5. Event / journal / WS priorities

| Layer | Priority | Role |
|-------|----------|------|
| **Event types catalog** | P1 | Stable names + small payloads (refs, not bodies) |
| **Journal + offsets** | P1 (extend 0.38) | Catch-up, redrive, multi-consumer |
| **WorkIntent drain** | P1 (extend 0.37) | Run when able on each host |
| **WS Assist channel** | P2 | Human chat remains request/response primary |
| **WS/SSE `/ws/v1/events`** (new) | P2 | Machine + Portal push; **not** overload assist dispatch |
| **Outbox stream as product** | P2 | Prefer journal as the stream contract; outbox stays reliable external delivery |

**Human WS push (Portal):** nice dogfood, ~days.  
**Provider as WS consumer:** medium; do **after** journal HTTP (or equivalent) consumer exists so reconnect has a source of truth.

---

## 6. Release trains from 0.40

### 0.40 — Composition dogfood & reactive completion

**Theme:** Close 0.37–0.38 gaps; prove Palm→Palm + local triggers.

| Step | Deliverable |
|------|-------------|
| **0.40.0** | This vision + STATUS |
| **0.40.1** | ✅ Example pack triggers — `todo-analytics` `on_resource` put-palm-todos / palm-todos → WorkIntent; `host.reload_work_triggers()` |
| **0.40.2** | Optional continuous `WorkDrainService` loop; debounce/depth tests |
| **0.40.3** | Journal: named consumer helpers for webhooks/projections; doctor `control_plane` section |
| **0.40.4** | Assist dataset open/describe; extra virtual ops if needed for system views |
| **0.40.5** | Remote Palm system datasets dogfood doc + one integration test (`remote_url`) |

### 0.41 — Durable presentation & schedules

**Theme:** Ops UX maturity without new brains.

| Step | Deliverable |
|------|-------------|
| 0.41.0 | Durable dashboard registry (storage-backed) |
| 0.41.1 | Schedule triggers: cron or robust interval registry across restarts |
| 0.41.2 | Design optional: propose dashboard / validate tiles |
| 0.41.3 | System dashboard remote_url story in docs |

### 0.42 — Change transport (realtime)

**Theme:** Push without making WS the composition core.

| Step | Deliverable |
|------|-------------|
| 0.42.0 | Event stream protocol sketch (subscribe, filter, heartbeat, `since`/offset) |
| 0.42.1 | Server `/ws/v1/events` (or SSE) — journal-backed catch-up |
| 0.42.2 | Portal optional live strip (ops events) |
| 0.42.3 | Palm provider **event consumer** (prefer offset resume) → improve remote wait |
| 0.42.4 | Outbox optional mirror only if product needs “delivery stream” |

### 0.43+ — Mesh & multi-tenant (later)

- Event type authz, multi-worker fan-out  
- Cross-origin trigger policies  
- Bot / NL only if contracts are boring  
- Never: OLAP-in-core, analytics joins as default  

---

## 7. Effort hints (for planning, not commitments)

| Slice | Ballpark |
|-------|----------|
| 0.40.1–0.40.3 (triggers dogfood + drain loop + doctor) | Days–1 week |
| 0.40.5 remote system analytics test | 1–2 days |
| 0.41 durable dashboards + cron | ~1 week |
| 0.42 human event stream MVP | ~0.5–2 days protocol + hub |
| 0.42 provider event consumer solid | ~1–2 weeks |
| Full multi-worker production stream | Weeks |

---

## 8. Complexity embrace / refuse (carry forward)

**Embrace:** signal vs intent vs execution; journal offsets; coalesce; definition triggers; palm provider as composition hub; analytics-only presentation.

**Refuse:** fat WorkEngine in core; EventEngine as job runner; tiered KV as Kafka; overloading Assist WS for machine control plane; Bot before contracts; system dashboards that bypass resources.

---

## 9. Success criteria (0.40–0.42)

1. **Local:** resource put → trigger → WorkIntent → drain → follow-on flow (dogfood pack).  
2. **Remote:** Palm A lists/jobs/instances on Palm B via provider; analytics dashboard works with `remote_url`.  
3. **Restart:** pending WorkIntents and journal offsets survive; redrive works.  
4. **Realtime (0.42):** provider or Portal can subscribe without replacing HTTP invoke.  
5. **Core purity** preserved; examples remain definition packs.

---

## 10. Relationship to prior visions

| Vision | Role |
|--------|------|
| 0.32–0.34 | Human transport + Assist remote |
| 0.35–0.39 | Data plane + reactive **foundations** + dashboards + system inspect |
| **0.40+** | **Composition mesh**: finish reactive dogfood, then optional live transport for provider + humans |

---

## 11. Closing

Composition succeeds when **calling Palm is boring** and **watching Palm is reliable**.  
Streaming makes watching **fast**; jobs, resources, journal, and WorkIntent make it **true**.

Organize work **0.40 first** (debt + dogfood), **0.41** (durable UX), **0.42** (push transport)—not WS-first.
