# Palm — Technical debt (live)

**Status:** Live open residual · **2026-08-05**.  
**Paid/closed detail:** [docs/audit/TECH-DEBT-PAID.md](docs/audit/TECH-DEBT-PAID.md)  
**PD-era archive:** [docs/audit/TECH-DEBT-ERA-0.45.md](docs/audit/TECH-DEBT-ERA-0.45.md)  
**Map:** [docs/PALM.md](docs/PALM.md) · **Status:** [STATUS.md](STATUS.md) · **Open theme:** [VISION-0.69](docs/vision/VISION-0.69.md) · seed [VISION-NAVIGATOR](docs/vision/VISION-NAVIGATOR.md)  
**Language:** ASD-STE100 (practical).

Closed theme chronicles live under [docs/vision/closed/](docs/vision/closed/).  
This file holds **what still needs work** plus a **master index** of all IDs.

---

## 1. How to use this file

| Rule | Meaning |
|------|---------|
| **Live** | Open residual only in detail sections below |
| **Paid archive** | Full closed write-ups: [TECH-DEBT-PAID](docs/audit/TECH-DEBT-PAID.md) |
| **IDs** | **SD-** system · **SU-** surface · **SI-** session · **BI-** boot · **OD-** operate · **ST-** stub · **CS-** smell · **CF-** carry |
| **Close** | Mark paid in master table; move detail to archive when volume hurts |
| **Victory** | Name debt before workaround; [VERSIONING.md](docs/VERSIONING.md) · [PALM.md](docs/PALM.md) |

**Add a row when:** shim, edge→engine bypass, purpose lie, surface bypass.  
**Do not add:** fixed bugs that are not structural.

---

## 2. Master index (system debt)

| ID | Title | Sev | Effort | Theme slice | Status |
|----|-------|:---:|:------:|-------------|--------|
| [SD-001](docs/audit/TECH-DEBT-PAID.md#sd-001) | No unified execution port | S1 | L | 0.57.3–5, 0.57.11–12 | ✅ done (job + workload catalog on port) |
| [SD-002](docs/audit/TECH-DEBT-PAID.md#sd-002) | System mixed into `palm.common` | S1 | XL | 0.57.2–13 | ✅ system/kits extracted; common = shared libs |
| [SD-003](docs/audit/TECH-DEBT-PAID.md#sd-003) | `RuntimeHost` incomplete vs live runtime | S2 | M | 0.57.2–3, 0.57.12 | ✅ clarified (submit contract + execution) |
| [SD-004](docs/audit/TECH-DEBT-PAID.md#sd-004) | `PatternBuildContext` is an engine bag | S1 | M | 0.57.4 | ✅ done (execution + resolve helpers) |
| [SD-005](docs/audit/TECH-DEBT-PAID.md#sd-005) | Edge and product call engines by field | S2 | L | 0.57.5–7, 0.57.11–12 | ✅ done for known product edges |
| [SD-006](docs/audit/TECH-DEBT-PAID.md#sd-006) | `PalmKernel` name vs system instance | S3 | S | 0.57.2 docs + code | ✅ done (0.57.2) |
| [SD-007](docs/audit/TECH-DEBT-PAID.md#sd-007) | Product `SystemService` vs system layer name | S3 | S | **0.61.4** Inspect rename | ✅ paid (aliases residual) |
| [SD-008](docs/audit/TECH-DEBT-PAID.md#sd-008) | Session plane has no system home | S2 | M | **0.58** | ✅ closed (0.58.20 exit) |
| [SD-009](docs/audit/TECH-DEBT-PAID.md#sd-009) | Workload dual bind (leaf engine + service) | S1 | M | 0.57.3–5, 0.57.12 | ✅ service path on port; leaves already port-driver |
| [SD-010](#sd-010) | STE rewrite backlog (legacy dense docs) | S4 | L | ongoing | open |
| [SD-011](docs/audit/TECH-DEBT-PAID.md#sd-011) | Server transport stack under `common.runtimes` | S2 | L | 0.57.13 | ✅ kits package (`palm.kits.server`) |
| [SD-012](docs/audit/TECH-DEBT-PAID.md#sd-012) | Cutover shims (fill as 0.57 moves) | S3 | — | 0.57.6–12 | ✅ deleted (0.57.12) |
| [SD-013](docs/audit/TECH-DEBT-PAID.md#sd-013) | Installed placeholders that lie (capability catalog) | S1 | M | 0.57.9 | ✅ gated (ST-001…005) |
| [SD-014](docs/audit/TECH-DEBT-PAID.md#sd-014) | No unified system boot phase table; composition not full truth | S2 | L | **0.59** | ✅ closed (0.59.8 exit) |
| [SD-015](docs/audit/TECH-DEBT-PAID.md#sd-015) | SystemPlanes open-codes wait/session/work install | S2 | M | **0.61** boy-scout | ✅ paid (definitions at edge) |
| [SD-016](#sd-016) | Ambient system-instance DI (seat DI incomplete) | S2 | L | **0.61**+ | open (boot engine seats + ensure_on; host residual) |
| [SD-017](docs/audit/TECH-DEBT-PAID.md#sd-017) | WorkIntent claim not exclusive (no claimer/lease) | S1 | M | **0.62.1–0.62.3** | ✅ paid (exclusive claim + reclaim + plane claimer) |
| [SD-018](docs/audit/TECH-DEBT-PAID.md#sd-018) | Work drain single-claimer by construction | S2 | M | **0.62.4–0.62.7** | ✅ drain N + Queued pool + exclusive drive |
| [SD-019](#sd-019) | Multi-process / multi-runtime shared claim needs storage CAS | S2 | L | later | open residual (not 0.62 floor) |
| [SD-020](#sd-020) | Dual readiness / residual edges (no single admission gate) | S1 | L | **0.63** floor | open (0.66 face; 0.67 dependents paid [VISION-0.67](docs/vision/closed/VISION-0.67.md); residual edges named) |
| [SD-021](#sd-021) | Profile / composition / env as parallel structure king | S2 | L | **0.63** growth | open (seed map + purge) |
| [SD-022](#sd-022) | Law docs treat talk/metaphor as types | S3 | L | ongoing | open (named 2026-08-19) |
| [SD-023](#sd-023) | 0.68 exit residual duals | S3 | S | **0.68** exit | open (named 2026-09-15; not unpaid costume) |
| [SD-024](#sd-024) | Host names wizard | S3 | S | after **0.68** close | open (named 2026-09-15; not unpaid costume) |

### Surface debt (SU)

| ID | Title | Sev | Effort | Status |
|----|-------|:---:|:------:|--------|
| [SU-001](#su-001) | Explorer SSR bypasses product (engine fields) | S2 | M | open |
| [SU-002](#su-002) | Explorer / forms god-files (size + mixed roles) | S2 | L | open |
| [SU-003](#su-003) | MCP dual stack (assist meta + domain tools + fat in_process) | S2 | L | open |
| [SU-004](docs/audit/TECH-DEBT-PAID.md#su-004) | MCP legacy module names still in tree | S3 | S | ✅ deleted (empty stubs) |
| [SU-005](#su-005) | CLI legacy alias forest locks old phrases | S3 | M | open |
| [SU-006](docs/audit/TECH-DEBT-PAID.md#su-006) | Surface transport kit split (`common.runtimes.server` vs `runtimes.server`) | S2 | L | ✅ kit home (`palm.kits.server`) |
| [SU-007](#su-007) | WebSocket / Portal maturity vs dual frame homes | S3 | M | open |
| [SU-008](#su-008) | Surface weight vs thin-adapter law (~14k server LOC) | S2 | XL | open |

### Stub / intention debt (ST)

| ID | Title | Sev | Effort | Status |
|----|-------|:---:|:------:|--------|
| [ST-001](docs/audit/TECH-DEBT-PAID.md#st-001) | Fake-success providers (graphql, postgres) | S1 | S | ✅ gated 0.57.9 |
| [ST-002](docs/audit/TECH-DEBT-PAID.md#st-002) | No-op storage backends listed as installed | S1 | S | ✅ gated 0.57.9 |
| [ST-003](docs/audit/TECH-DEBT-PAID.md#st-003) | ETL pattern is a phase ticker (gated off install) | S2 | S | ✅ gated 0.57.9 |
| [ST-004](docs/audit/TECH-DEBT-PAID.md#st-004) | Transform `parquet_load` registered, always errors | S3 | XS | ✅ gated 0.57.9 |
| [ST-005](docs/audit/TECH-DEBT-PAID.md#st-005) | Tests freeze lying install sets (`test_modular_apps`) | S1 | S | ✅ fixed 0.57.9 |
| [ST-006](#st-006) | Phase-named tests become eternal contracts | S3 | M | open |

### Code smell (CS)

| ID | Title | Sev | Effort | Status |
|----|-------|:---:|:------:|--------|
| [CS-001](#cs-001) | Layer bulk: `runtimes` + `common` dominate LOC; `system` exists and is larger than `common` | S2 | — | open (metric) |
| [CS-002](docs/audit/TECH-DEBT-PAID.md#cs-002) | Triple observability names on host | S2 | M | ✅ paid (0.61.7 demotion; triple aliases residual) |
| [CS-003](#cs-003) | Core leaves take concrete engines (not protocols) | S2 | M | open |
| [CS-004](#cs-004) | Definition `from_dict` forever-legacy shapes | S3 | M | open |
| [CS-005](#cs-005) | Broad swallow `except` / empty `pass` in hot paths | S3 | M | partial (hot paths logged; residual elsewhere) |
| [CS-006](docs/audit/TECH-DEBT-PAID.md#cs-006) | Supervisor continuous wire is schedule prose | S3 | M | ✅ paid (definitions at edge) |
| [CS-007](docs/audit/TECH-DEBT-PAID.md#cs-007) | Vitality `lineage: adapter` schema residue | S4 | S | ✅ paid (coerce + no emit) |
| [CS-008](docs/audit/TECH-DEBT-PAID.md#cs-008) | Plane factories still close over full runtime | S3 | M | ✅ paid (InstallContext ports) |

### Operate diagnosis (OD)

| ID | Title | Sev | Effort | Status |
|----|-------|:---:|:------:|--------|
| [OD-001](docs/audit/TECH-DEBT-PAID.md#od-001) | Doctor as kernel eyes (not vitality) | S2 | M | ✅ paid (0.61.6 demotion; packaging residual named) |

---


---

## 3. Open debt detail

### SD-016 — Ambient system-instance DI (seat DI incomplete)

<a id="sd-016"></a>

**Severity:** S2 · **Effort:** L · **Theme:** **0.61**+ (structural)

**Observation:** Palm grew real seats (`execution`, `install`, planes, supervisor)
but call graphs still often take the whole system instance and dig. Planes were
the loud instance; the bug is system-wide (boot, host, surfaces).

**Law (target):** inject **interfaces** and **subsystems** — not ambient shell DI.  
[AGENTS §1.2](AGENTS.md) · [PALM §9](docs/PALM.md) law 18.

| Landed (0.61) | Still open |
|---------------|------------|
| `InstallInterface` / `SystemInstall` | Kill ambient digs in host/product/surfaces |
| `system.interfaces` + `system.subsystems` packages | Drop compat shims when callers migrated |
| `Subsystem` protocol | Seat-first APIs outside boot (product doors) |
| BootContext seats: engines + install/planes/supervisor | Progressive install bind (partial board earlier) |
| Schedule uses `ctx.shell` + published seats | Thin `*_to_runtime` bridges remain |
| `SystemPlanes.ensure_on` / `SystemSupervisor.ensure_on` | Host recovery / ApplicationHost bag digs |
| Phase **how** co-located on subject (`phase_*.py`); boot = order + catalog + walk | Host phase definitions (same pattern) |
| System phase catalog imports subject modules only | Drop remaining wire / `*_to_runtime` shims when quiet |
| **0.63.22** assist `admission_source` / `admission_gate()` (oath) | Other product doors still dig runtime bag for readiness |

**Avoid:** rename theater only (`runtime` → `source`); `system.common` dump.

**Related:** [SD-015](#sd-015) · [CS-008](#cs-008) · [SU-*](#surface-debt-su) · [SD-020](#sd-020).

**Status:** open (boot seat DI improved; assist admission boy-scout; host/surfaces residual).

---


### SD-019 — Multi-process / multi-runtime shared claim needs storage CAS

<a id="sd-019"></a>

**Severity:** S2 · **Effort:** L · **Theme:** residual after 0.62 (not floor)

**Observation:** `BaseBackend` is get/set/delete only. No atomic compare-and-set claim.  
Two OS processes (or two continuous drain owners) on one durable store can double-claim even with lease fields on disk.

**Product law until paid:** **one continuous work-drain owner per work-intent store.**  
Multi-runtime `worker_count` is not a shared claim pool.

**Pay later:** Storage-native claim or CAS; fencing tokens as needed.  
Shape 0.62 claimer/lease fields so CAS is a plug-in, not a rewrite.

**Do not:** Block 0.62 floor on multi-process CAS. Do not market multi-host claim pool without this.

**Related:** [SD-017](#sd-017) · Grove scale-out (different home).

**Status:** open residual (named at 0.62.0).

---


### SD-020 — Dual readiness / residual edges (no single admission gate)

<a id="sd-020"></a>

**Severity:** S1 · **Effort:** L · **Theme:** **0.63** floor (closed) · face [VISION-0.66](docs/vision/closed/VISION-0.66.md) (**closed**) · dependents [VISION-0.67](docs/vision/closed/VISION-0.67.md) (**closed**)

**Observation:** Business that needs ground can start without a single **admission** surface. Soft “definitions ready,” host flags, catalog order, and half-host tests act as peer readiness. Dual mode hides as green.

**Pay in 0.63:** Core/status + system admission; one citizen path fail-closed; coherence suite maps pretenders; purge or kill-date residual. Law: [VISION-ASSEMBLY](docs/vision/VISION-ASSEMBLY.md) §6.4 · [ADR-032](docs/adr/032-organism-assembly.md).

**Progress:** **0.63.1–0.63.7** seats · gates · coherence · seed · refuse · eyes. **0.63.20–0.63.33** product + host packaging + CQRS. **0.63.34** surface fealty. **0.63.35–0.63.37** surface admission voice (REST · MCP/WS · CLI/SSR). **0.63.38** exit residual ledger (`open_residual_edges` / doctor present).

**Named residual (not this door — not architecture):** live list via `open_residual_edges()` / `admission_inventory()["open_residual_ids"]` (0.63.38). Summary:

| Residual | Kind | Why named |
|----------|------|-----------|
| Direct **`WorkloadEngine.start` / `.exec`** | **Assemble / unit** free; **residual** if product digs for business | Port law **0.63.20** / **0.63.27** |
| Direct **`ResourceEngine.invoke`** | **Unit / non-port** free; **residual** if product digs | Port law **0.63.24** |
| **`stop_workload` / stop_owned** | Control path when admission closed | **named_0_63_27** — shutdown must work |
| **Assist session cancel** | Control path when admission closed | **named_0_63_29** — operator stop must work |
| **Flow cancel · `cancel_job`** | Control path when admission closed | **named_0_63_30** — operator stop must work |
| **Workload product stop/cancel** | Control path when admission closed | **named_0_63_31** — operator stop must work |
| **Flow LIST / DESCRIBE** | Soft catalog browse when admission closed | **named_0_63_32** — packaging eyes, not start |
| **PalmKernel / bare runtime public dig** | Port-gated only; bypasses host packaging edge | **named_0_63_33** — port is law |
| Host packaging eyes (CS-002) | Eyes residual | **named_0_63_23** |

**Paid (not residual architecture):** planes, ports, product façades, host packaging start/continue, surface host/port, surface admission voice ring, exit residual ledger cartography — see `paid_readiness_edges()` / admission inventory.

**Do not:** Soft-open the gate for CI. Permanent corridor guards instead of one gate. Fake green that encodes dual mode. Leave “not this door” **unnamed** so digs become lifestyle.

**Status:** open (0.63 walls up; residuals **named**). **0.66** paid the face. **0.67** paid dependents (require door, drain able, composition kings + leftover). Sequence: [VISION-0.64](docs/vision/closed/VISION-0.64.md). Costume composted: [VISION-0.68](docs/vision/closed/VISION-0.68.md) (**closed**). Residual [SD-023](#sd-023).

---


### SD-021 — Profile / composition / env as parallel structure king

<a id="sd-021"></a>

**Severity:** S2 · **Effort:** L · **Theme:** **0.63** growth (closed) · residual profile/env (not 0.68 costume)

**Observation:** `CompositionProfile`, `DeploymentProfile`, `BootMode`, and some structure-shaped `PALM_*` toggles still act as **structure law** beside the structure definition. That is dual king after assembly lands.

**Pay in 0.63 growth:** Map entry/mode/env into **definition seed**; after load, assembly status is structure truth; packaging env stays; structure dual toggles purge or residual kill-date. First definition: **embedded**; dogfood: cli / server.

**Progress:** **0.63.5** seed map + builtin DNA catalog on host spawn. **0.63.13** — `PALM_ASSEMBLY_DNA_ID` explicit seed; membership always for refuse; continuous drain DNA king; `STRUCTURE_SEED_ENV` cartography. **0.63.19** — full `MEMBERSHIP_CAPABILITY_SEEDS` catalog; bootstrap single source. **0.63.28** — host outbox store wire from `composition.has("outbox")` (settings seed only). **0.63.39** — DNA `capabilities` lists `work_drain`; manager materializes (register/start) only when listed; `composition.has` / `BootMode.allow_background_drain` no longer peer-gate that unit. **0.65.2** — host outbox store wire follows DNA `has_capability("outbox")`; the 0.63.28 composition king is paid. **0.67.7** — journal is DNA list + attach hand; `composition.has("journal")` dies on that unit. **0.67.8** — journal leftover costume paid (one attach on the runtime bus; host slot aliases it; not a loop). **0.67.9** — projections is DNA list + attach hand; `composition.has("projections")` dies on that unit. **0.67.10** — projections leftover costume paid (one attach on the runtime bus; host slots alias it; not a loop). **0.67.11** — compensation is DNA list + attach hand; `composition.has("compensation")` dies on that unit. **0.67.12** — compensation leftover costume paid (one attach on the runtime bus; host slot aliases it; not a loop). **0.67.13** — webhook is DNA list + attach hand; `composition.has("webhook")` dies on that unit. **0.67.14** — webhook leftover costume paid (one dispatcher; host slot aliases it; URLs refine that object; not a loop). **0.67.15** — unread `enable_compensation` / `enable_webhook_dispatcher` composted; dead `attach_runtimes` gone. **0.67.16** — analytics is DNA list + attach hand; `composition.has("analytics")` dies on that unit. **0.67.17** — analytics leftover costume paid (one organ; host slot aliases it; `analytics_enabled` refines that object; not a loop). **0.68.1** — empty `host.projections.attach` composted. **0.68.4** — outbox store wire is DNA listing (`capability_off:outbox`); `enable_event_outbox` gone. Residual: profile/env duals (this row); 0.68 costume closed — [VISION-0.68](docs/vision/closed/VISION-0.68.md); [SD-023](#sd-023); SD-020 soft-ready neighbors.

**Do not:** Leave profiles as public dual structure forever “for compatibility.” Remove packaging env wholesale.

**Status:** open (seed map + membership catalog + outbox DNA skip paid — profile/env residual).

---


### SD-022 — Law docs treat talk/metaphor as types

<a id="sd-022"></a>

**Severity:** S3 · **Effort:** L · **Theme:** standing docs (not a minor)

**Observation:** Living law files treat **spoken and metaphorical words as types** (Assist as the only operator, feudal/biology as ontology, “Terminal” as if a package). STE “same word” cemented the leak. Architecture already splits metaphor vs engineering: [appendix/metaphor.md](docs/architecture/appendix/metaphor.md).

This is **not** SD-010 (dense prose). This is **wrong ontology**.

**Target:** When a law file is touched for substance, replace talk-as-type with computer-science terms. Move leftover metaphor to the appendix or [PHILOSOPHY.md](PHILOSOPHY.md). Rule: [WRITING.md](docs/WRITING.md) *Talk vs law*. Example split: [VISION-NAVIGATOR](docs/vision/VISION-NAVIGATOR.md). No big-bang rewrite.

**Do not:** Freeze a spoken word because it is familiar. Refuse a CS word because it is missing from the STE term list.

**Status:** open (named 2026-08-19).

---


### SD-023 — 0.68 exit residual duals

<a id="sd-023"></a>

**Severity:** S3 · **Effort:** S · **Theme:** [VISION-0.68](docs/vision/closed/VISION-0.68.md) (**closed**) · named at exit

**Observation:** José closed 0.68 with these duals **named**, not composted. They are leftover names and defaults, not unpaid organs.

| Dual | What it is | Keep |
|------|------------|------|
| MCP profile `experimental` | Same tool groups as `full` | `full` / `assist` / `core` |
| Recovery `_webhook_dispatcher` | Second pointer to `install.webhook` so tests count two seats | DNA webhook, URL refine on the install organ |
| Host `event_plane_status` / `ops_status` / `control_plane_status` | CS-002 residual public names. `packaging_status` ≡ `control_plane_status`. `event_plane` / `ops` are nested bags | Living eyes: `inspect.top` / vitality |
| `HttpWebhookDeliverer` as unused default | `WebhookDispatcher` defaults to urllib POST. Production drain does not call `dispatch` | Webhook organ, recording deliverer, `on_before_publish` test hook |

**Do not:** Wire outbox drain to `dispatch` to “use” HTTP. Deflate the fat MCP `full` catalog here (that is [VISION-SURFACE-DEFLATION](docs/vision/VISION-SURFACE-DEFLATION.md) / SU-003). Open a minor only to delete these names.

**Status:** open (named 2026-09-15).

---


### SD-024 — Host names wizard

<a id="sd-024"></a>

**Severity:** S3 · **Effort:** S · **Theme:** none (named after [VISION-0.68](docs/vision/closed/VISION-0.68.md) close) · registry extension leftover

**Observation:** José named this after 0.68 close. Dispatch already walks `CqrsContributor`. Pattern projections already walk `registered_projection_factories()`. The hub still **imports wizard** for typed convenience and job-context stitch. 0.68.15 composted unused `host.wizards` / `instances` / `jobs` objects and kept the flats without naming them.

| Dual | What it is | Keep |
|------|------------|------|
| `ApplicationHost.get_wizard_progress` / `list_wizard_progress_views` | Host imports wizard query types and read-model type. Thin `ask()` wrappers. CLI dashboard, diagnostics, `full_demo` call the flats | `host.ask(query)`. Callers import the query from `palm.patterns.wizard` |
| `HostQueryHandlers._get_job_context` | Generic job-context query hardcodes `_pattern_projections.get("wizard")` and builds `GetWizardProgressQuery` | Pattern extras via contributor / read-model registry |
| `build_job_context(..., wizard_progress=)` | Shared job-context envelope names a pattern field. `derive_next_actions` copy says wizard input | Pattern inspection already on the payload |
| `PalmKernel.current_wizard_step` / `BaseRuntime.current_wizard_step` / `wizard_answers` | Runtime inspect already is `inspect_step` / `inspect_answers` | Generic inspect on the executable |
| `kits.server.cqrs` `_wizard_progress` | Server kit repeats the same stitch | Same as host query walk |

**Do not:** Invert this as a 0.68 compost slice (theme closed). Fold it into [SD-023](#sd-023). Treat it as [VISION-SURFACE-DEFLATION](docs/vision/VISION-SURFACE-DEFLATION.md) or Navigator. Add a new host facade. Open a minor only to delete these names.

**Law:** [src/palm/AGENTS.md](src/palm/AGENTS.md) §1.1 — definition at the edge; hub holds and runs. A private menu of concretes in the host is a missing inversion.

**Status:** open (named 2026-09-15).

---


### SD-010 — STE rewrite backlog

**Severity:** S4 · **Effort:** L

**Observation:** New map/theme text uses STE.  
ARCHITECTURE, README, many VISION files remain dense legacy.

**Target:** Rewrite when a file is touched for substance. No big-bang rewrite required for 0.57 exit.

**Related:** [SD-022](#sd-022) is vocabulary/ontology, not density.

---


### SU-001 — Explorer SSR bypasses product

**Severity:** S2 · **Effort:** M · **Related:** SD-005

**Observation (updated 0.57.7):** Explorer **effects** use the port
(`execution.invoke_resource`, `execution.resume_job`). Residual risk is
**bulk / mixed roles** (SU-002) and any new bypasses, not those two call sites.

**Why it still hurts:** Surface code remains thick; easy to re-introduce engine fields.

**Target:** Explorer → product services where possible; keep port-only for effects.

---


### SU-002 — Explorer / forms god-files

**Severity:** S2 · **Effort:** L · **Related:** CF-004 (PD-016)

**Observation:**

| File | ~LOC |
|------|-----:|
| `ssr/explorer/components.py` | 988 |
| `ssr/explorer/forms.py` | 942 |
| `ssr/explorer/actions.py` | 382 |
| `rest/doc_examples.py` | 642 |

Mixed HTML, forms, and orchestration concerns.

**Target:** Split present vs drive; drive through product.

---


### SU-003 — MCP dual stack

**Severity:** S2 · **Effort:** L · **Related:** CF-003 (PD-014/015)

**Observation:**

- Assist-first meta-tool is the **law** for agents.  
- Full domain tool packs still exist (`flows/`, `design/`, …).  
- `mcp/in_process.py` ~816 LOC — bridge + catalog + surface glue.

**Why it hurts:** Two mental models for agents; fat process entry resists “thin surface.”

**Target:** Assist path complete; domain tools optional or generated from same dispatch; shrink in_process.

---


### SU-005 — CLI legacy alias forest

**Severity:** S3 · **Effort:** M

**Observation:** CLI keeps primary commands **and** shorter legacy phrases (`registry.py`, `catalog.py`, help text).  
Pre-1.0 is free to cut aliases; keeping them freezes old product language.

**Target:** One phrase set; migration note if needed; drop aliases that only exist for comfort.

---


### SU-007 — WebSocket / Portal dual homes

**Severity:** S3 · **Effort:** M

**Observation:** WS frames re-export from `common.websocket`; session logic under `runtimes/server/surfaces/websocket/`.  
Portal client direction is still thin vs Assist law.

**Target:** One frame module path; Portal stays a client of Assist dispatch only.

---


### SU-008 — Surface weight vs thin-adapter law

**Severity:** S2 · **Effort:** XL

**Observation (approx. Python LOC under `src/palm/runtimes/`):**

| Surface | ~LOC | Note |
|---------|-----:|------|
| server | 14100 | REST + SSR + WS |
| mcp | 4700 | tools + in_process |
| cli | 3800 | commands + TUI |
| daemon | 50 | thin OK |
| embedded | 30 | thin OK |

**Why it hurts:** “Thin surface” is a law surfaces currently fail by bulk. Not all LOC is wrong (HTML/OpenAPI is heavy), but bypass and dual stacks are.

**Target:** Metric + policy: new surface code must call product/ports; no new engine field access (SD-005/SU-001).

---

## 3c. Stub / intention debt detail

Full intention table: [docs/STUBS.md](docs/STUBS.md).


### ST-006 — Phase-named tests

**Severity:** S3 · **Effort:** M

**Observation:** Names like `test_cqrs_phase5.py`, `test_mcp_phase3.py`, `test_resource_phase5.py` encode temporary program phases as permanent contracts.

**Target:** Rename to capability (`test_cqrs_schemas.py`, …) when touched; no new `phaseN` files.

---

## 3d. Code smell detail


### CS-001 — Layer bulk

**Severity:** S2 · **Metric**

Approx. Python LOC under `src/palm/` (all `.py` lines, living tree):

| Package | ~LOC / note |
|---------|-------------|
| runtimes (surfaces) | 24500 |
| common | 15300 · still fat · lazy-exports system types |
| system | first-class · 133 files · ~630KB · larger than common |
| services | 13700 |
| patterns | 9900 |
| core | 9000 |
| app | 5100 |

`palm.system` exists as first-class and is larger than `common`. `common` is still fat and still lazy-exports system types.

**Use:** Track after system extract; surfaces and common should both fall or reclassify.

---


### CS-003 — Core leaves take concrete engines

**Severity:** S2 · **Related:** SD-001, SYSTEM-LOW-LEVEL P2

`ResourceLeaf` (and similar) take `ResourceEngine` type in **core**.  
Blocks a clean port without a core **protocol** for invoke.

**Target:** Small invoker protocol in core; engines and ports implement it.

---


### CS-004 — Definition forever-legacy shapes

**Severity:** S3

`from_dict` paths accept legacy shapes across definitions. Pre-1.0 can drop dead branches once fixtures update.

---


### CS-005 — Broad swallow / empty pass

See **CF-007**. Prefer explicit error or documented ignore.

**Progress (capacity residual):** Hot-path honesty without changing fail-closed job lifecycle:

| Site | Change |
|------|--------|
| Job hooks (`outbox_drain`, `session_ownership`, `instance_persistence`) | Log + documented ignore (must not break orchestration) |
| Host `RecoveryCoordinator` outbox supervisor paths | `debug` + `exc_info` instead of empty `pass` |
| `SystemLog` console print | Narrow to `OSError` |
| **BI-014** system start host session | Fail closed (no swallow) |

**Residual:** product/kit/runner sites still open-code broad `except` — boy-scout on touch.

---

## 4. Carry-forward (old era, still real)

These are **not** closed by the archive. Full text: [TECH-DEBT-ERA-0.45](docs/audit/TECH-DEBT-ERA-0.45.md).

| ID | Old | Title | Notes |
|----|-----|-------|-------|
| CF-001 | PD-018 | Overlapping observability vocabularies | Host vs runtime bus is clearer; magic strings may remain |
| CF-002 | PD-009 / PD-010 | Host composition residual | Host smaller than 1170 LOC; **structural fix → [SD-014](#sd-014)** (boot phases + composition truth) |
| CF-003 | PD-014 / PD-015 | Assist/MCP complexity + coverage | Product/surface debt |
| CF-004 | PD-016 | Large SSR explorer files | Surface debt; also SD-005 call sites |
| CF-005 | PD-022 / PD-030 | DB adapters + empty extras | Runner/provider maturity |
| CF-006 | PD-023 | Placeholders registered as installed | Gate experimental |
| CF-007 | PD-024 | Broad `except Exception` | Hygiene |
| CF-008 | PD-029 | `urlopen` scheme allowlist | Security hygiene |
| CF-009 | PD-005 | Complexity gate scope | Tooling |
| CF-010 | PD-017 | Runtimes coverage cold spots | Tests |
| CF-011 | PD-011 | Inbound mixed responsibilities | Host/work plane |
| CF-012 | PD-025–027 | Naming / magic numbers | Low priority |

**Closed in old era (do not reopen without new evidence):**  
PD-001–004, PD-006–008, PD-012, PD-013, PD-019–021, PD-028, PD-031, and theme-closed work through 0.55 — see archive roadmap tables.

---

## 4b. Session impact inventory (SI-* · 0.58.0 analysis)

**Purpose:** Capture **what the session plane will break or rebind** so agents can chew later without chat context.  
**Law (0.58):** session ≠ instance ≠ job; multi-instance; system home; surfaces bind.  
**Not all SI rows are 0.58 must-close.** Pay when a slice touches that edge; otherwise leave open.

| ID | Title | Area | Theme touch | Status |
|----|-------|------|-------------|--------|
| [SI-001](#si-001) | `session_id` forced equal to `instance_id` | product Assist | 0.58.6–12 · **0.58.19** | ✅ paths/envelopes (handles thin SI-002) |
| [SI-002](#si-002) | FlowSession / AssistSession are product-only “sessions” | product | 0.58.1–12 · exit seed | open → [VISION-SURFACE-DEFLATION](docs/vision/VISION-SURFACE-DEFLATION.md) |
| [SI-003](#si-003) | ProcessInstance has no session owner link | instances / system | 0.58.4 | ✅ done |
| [SI-004](#si-004) | WS connection bind is surface-local only | server WS | 0.58.7 | ✅ done |
| [SI-005](#si-005) | MCP / palm_assist paths treat session as instance | MCP Assist | 0.58.6–8 · **0.58.17** · **0.58.19** | ✅ path/alias rename |
| [SI-006](#si-006) | CLI / REPL `active_assist_session_id` | CLI TUI | 0.58.3 · **0.58.17** | partial (BoundSurface truth; dual mirrors residual) |
| [SI-007](#si-007) | CQRS instance queries are the public “session” | host CQRS / kits | 0.58.8 partial | partial (`system/session`) |
| [SI-008](#si-008) | `flow.session.*` events lack real session subject | event plane | 0.58.4+8 | ✅ partial + filter |
| [SI-009](#si-009) | WorkloadOwner.session_id optional / unenforced | workload | 0.58.8 partial | partial (EventContext) |
| [SI-010](#si-010) | Explorer / REST drive instance without session bind | surfaces SU | later (SU-*) | open (named residual) |
| [SI-011](#si-011) | Composition / inbound start without session attribution | work plane edges | 0.58.13 · **0.58.16** | ✅ done (inherit-or-service) |
| [SI-012](#si-012) | Docs and skills say session ≡ flow instance | docs / MCP skill | **0.58.20** | ✅ taught (skill + MCP + wiki) |
| [SI-013](#si-013) | Session multi-attach + reverse index | system plane | 0.58.2 | ✅ done |
| [SI-014](#si-014) | Plane-store pattern not shared across planes | architecture | **ponder later** | open |
| [SI-015](#si-015) | Continue paths skip owner check when session bound | product / surfaces | 0.58.11 · **0.58.15** | ✅ done (strict attribution) |
| [SI-016](#si-016) | Surfaces invent dual context; walk facts on job meta | product / surfaces | **0.58.14** · **0.58.17** | partial (seat+dogfood ✅; job-meta cleanup residual) |


### SI-002 — FlowSession / AssistSession product-only

**Where:** `services/execution/flows/session.py`, `services/assist/session.py`, `services/assist/sessions/`.  
**Impact:** Handles still useful for testing and CLI/assist verbs; they resolve
continue via **SessionService** when wired. Fields may still name continue as
`session_id` (pre-plane era).  
**Target (named, not paid in 0.58):** honest **walk** handles under BoundSurface,
or **cut** and rebuild when APIs/SDKs land — see
[VISION-SURFACE-DEFLATION](docs/vision/VISION-SURFACE-DEFLATION.md). Do not polish the lie forever.


### SI-006 — CLI / REPL active session id

**Where:** `runtimes/cli/tui/*`, `runtimes/cli/shared/context.py`.  
**Impact:** **Partial (0.58.3 · 0.58.17):** `CliContext.bound_surface` is product
truth; `active_system_session_id` mirrors it. Product
`active_assist_session_id` may still be instance-shaped (SI-001). TUI prompt
still shows assist id.  
**Target:** Prompt / verbs prefer BoundSurface; drop dual mirrors after rename.


### SI-007 — CQRS instance queries as public session

**Where:** host CQRS, `kits/server/cqrs.py`, facades `get_instance`, flows session REST.  
**Impact:** **Partial (0.58.8 + 0.58.18):** operator paths via product door —
`system/session/{id}` · `/view` · `/waiting` · `/instances` · `/focus` ·
`/cancel` · `/cancel/all`. SessionService operate verbs (`focus`,
`cancel_owned`, `surface_view` v2). Full CQRS contributor + REST routes
optional residual.  
**Target:** Session inspect/operate first-class in operator catalog; instance remains job-path API.


### SI-009 — WorkloadOwner.session_id

**Where:** `palm/core/workload/owner.py`, engine stop-by-owner filters.  
**Impact:** **Partial (0.58.8):** `BaseRuntime.start_workload` enriches owner from
active `EventContext` (session/job/instance) when missing. Explicit owner still
wins. Residual: leaves that never bind event context.  
**Target:** All job-path starts carry session on owner when metadata has it.


### SI-010 — Explorer / REST without session bind

**Where:** server explorer SSR, bare explorer instance routes (SU-* related).  
**Impact:** Operator UI can drive instance without BoundSurface bind. Dogfood MCP/CLI/WS
paths bind; explorer bulk not paid in 0.58.  
**Status:** **open residual (0.58.20 honesty)** — name for later surface / SU-* theme.
Not a dual-path law hole on dogfood surfaces.  
**Target:** Cookie / BoundSurface when explorer HTTP is next touched.


### SI-014 — Shared plane-store framework

**Observation:** Wait, work, workload, session may each need stores.  
**Target:** **Ponder later** — not a 0.58 gate. Per-plane store first.


### BI-003 — Dual composition root

**Observation:** `ServerContext` lean path vs `ApplicationHost` (ADR-019 refined).  
**Law (refined):** dual **types** stay (surface single-runtime view vs multi-runtime host) — scout 0.51.6. Dual **assembly law** is refused: one `core_service_registry` + shared product packaging.  
**Progress (0.61 residual):** `apply_product_packaging` shared by host `_wire_cqrs` and host-less `ServerContext`; assist↔analytics, dashboards, design CQRS; standalone accepts real `PalmSettings`; parity pins in `tests/test_product_packaging_parity.py`.  
**Not paid:** packaging as registry/install seats at the edge; workplane session enrich + definition catalog still host coordinator (BI-013 residual); lean-host MCP dogfood chrome.  
**Do not:** delete `ServerContext` or re-type surfaces onto the host.


### BI-007 — Test host constructions

**Observation:** Many tests build hosts without a named mode.  
**Progress (0.59.6–.7):** `ApplicationHost.for_mode("test"|"safe"|shapes)`; `server_port`; conftest
`test_mode_host` / `safe_mode_host`; dogfood tests pin phenotype + spine.  
**Progress (0.59.8 residual cleanup):**
- Default integration fixture `host` → `for_mode("all_in_one", settings=fast_settings)` (named mode).
- Dead spine examples fixed: legacy `pattern="dag", options={"name": "quick"}` → one-step wizard
  helper `tests/helpers/flows.py` (DAG requires `nodes` since 0.54).
- Touched host CQRS / CLI / palm_app / job-board tests use spine helper or `for_mode`.
**Still open:** opportunistic migrate of remaining hand-built `ApplicationHost(...)` sites when
edited; not a full suite force. Kill condition: new integration tests prefer `for_mode` or the
shared fixtures; do not reintroduce dead `options={"name": "quick"}` DAGs.


### BI-009 — Triple override

**Observation:** Settings, profile, and start options can disagree.  
**Pay:** resolver table documented and tested.


### BI-010 — Surface mount special cases

**Observation:** Surface mount not only `CompositionProfile.surfaces`.  
**Progress (0.59.5):** host schedule requires `deployment.server` **and** non-empty
`composition.surfaces`; factory already filters by `only=composition.surfaces`.  
**Pay residual:** chrome / dual-stack surface bulk → [VISION-SURFACE-DEFLATION](docs/vision/VISION-SURFACE-DEFLATION.md).


### BI-011 / BI-012 — Harvest buckets

Fill concrete rows when breaks appear. Note **rule**, **true owner**, **parked theme**.

## 7. Later theme seeds (not the open minor)

| Seed | Debt | Spirit |
|------|------|--------|
| **Multi-claimer / capacity** | SD-017 · SD-018 · residual SD-019 | **Closed 0.62** — [VISION-0.62](docs/vision/closed/VISION-0.62.md) · [ADR-031](docs/adr/031-multi-claimer-work-drain.md) Accepted |
| **Assembly / organism truth** | SD-020 · SD-021 · SD-023 · SD-024 · host/profile glue · catalog wire · product dig into composition root | **0.63–0.68 closed** — [VISION-0.68](docs/vision/closed/VISION-0.68.md) · seed [VISION-ASSEMBLY](docs/vision/VISION-ASSEMBLY.md) · residual [SD-023](#sd-023) · [SD-024](#sd-024) |
| **Surface deflation** | SU-* · SI-002/006/010 | Compost with evidence after eyes — [VISION-SURFACE-DEFLATION](docs/vision/VISION-SURFACE-DEFLATION.md) |
| **Navigator** | SD-022 · Assist as product bag | **Open 0.69** — [VISION-0.69](docs/vision/VISION-0.69.md) · seed [VISION-NAVIGATOR](docs/vision/VISION-NAVIGATOR.md) · [ADR-037](docs/adr/037-navigator-invert.md) **Proposed**. Do not pay [SD-024](#sd-024) here. |
| **Plane-store framework** | SI-014 | Ponder only; per-plane stores first |
| **User plane + session impersonation** | D11 · SI-015 bare residual | Principal **acts as** owning session — not dual-own. **Also owns** entry chooser and definition visibility (named on [VISION-NAVIGATOR](docs/vision/VISION-NAVIGATOR.md) 2026-09-15). Do not grow ambient `AuthEngine` principal into this plane. Do not open this to ship Navigator. |
| **Delegate / team session membership** | growth | Shared walk under one owner session |
| **Workload remainder** | 0.56 queue | Full placement, cancel hooks, peer mesh; place registry for assembly |
| **Tunnels / reach** | after assembly | Trusted paths · neighborhood · edge/cloud — [VISION-TUNNELS](docs/vision/VISION-TUNNELS.md) (queue seed; not open) |

**Closed (not a seed):** **System vitality** — [VISION-0.61](docs/vision/closed/VISION-0.61.md) closed · [ADR-030](docs/adr/030-system-vitality.md) Accepted · residual BI-015 · SD-016.

**Closed (not a seed):** **System supervisor + work plane** — [BI-013](docs/audit/TECH-DEBT-PAID.md#bi-013) ✅ · [VISION-0.60](docs/vision/closed/VISION-0.60.md) closed.  

**Closed (not a seed):** **System boot** — [SD-014](docs/audit/TECH-DEBT-PAID.md#sd-014) ✅ · [VISION-0.59](docs/vision/closed/VISION-0.59.md) closed · residual **BI-***.

---

*Name the debt. Then pay it in order. Do not paper it.*
