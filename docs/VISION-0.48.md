# VISION 0.48 — Decompose `ApplicationHost` (T2)

**Theme:** TECH-DEBT **T2** — the god-object (PD-009) + its CQRS-wiring coupling (PD-010), the three
overlapping status APIs (PD-018), **and** the relocation of the second composition root `ServerContext`
(PD-013, deferred here from T3 — see [ADR-017](adr/017-import-seams.md)).

**Unblocked by 0.47 (T3).** T3 made the host's true dependency surface top-level and visible (only 10
function-local imports remain, none cycle-forcing) and built the exact registry/contributor machinery
this theme generalizes. Decomposing before T3 would just have relocated the cycles.

**Why:** `src/palm/app/host/application_host.py` is **1164 LOC, one class, 79 methods** incl. **29
`@property`** lazy service slots, a **~106-line `_wire_cqrs`**, three status vocabularies, and **13
degrade-to-fallback `except Exception`**. It's the #1 churn hotspot and the audit's 🔴 for Single
Responsibility — it mixes lifecycle + CQRS/projection wiring + execution facade + a 29-slot service
registry + observability. This is the endurance-critical seam.

## Target

`ApplicationHost` shrinks to a **thin composition root** (**< 350 LOC**, no `Any` service slots) that
(1) builds infra, (2) drives a lifecycle sequence, (3) delegates a stable public API. Everything else
moves to collaborators it *holds*, and services **self-register** into a registry instead of 29
hand-written accessors.

**The target model already exists in-tree — reuse it, don't invent.** T3 established the pattern:
`common/patterns/_registry` (`CqrsContributor`/`iter_cqrs_contributors`) and
`common/cqrs/service_contributors` (`ServiceCqrsContributor`/`wire_service_cqrs_contributors`) — plus the
new `preflight_registry` / `session_view_registry` — are all "domains register downward on import;
a driver drains the registry." Seams 1–2 generalize that same shape to service construction and wiring.

## Layout — modular, not flat

Each seam lands as a **concern-based subpackage** under `app/host/`, not another flat file — keeping `app/`
consistent with palm's django-apps/registry structure. E.g. `app/host/services/{registry,providers}.py`
(seam 1); later seams add `app/host/workplane/`, `app/host/lifecycle/`, `app/host/wiring/`, folding today's
flat `inbound_service.py`/`work_drain_service.py`/`cqrs_wiring.py` into the package that owns them. Each
package re-exports its public surface from `__init__`.

## Extraction seams (composition, not inheritance)

1. **`HostServiceRegistry`** — replaces the 29 lazy `@property` slots. A typed
   `ServiceProvider(name, build, depends_on)` registry (mirroring `common/cqrs/service_contributors`);
   services register providers; `build_all(ctx)` builds in dependency order. `host.system`/
   `host.execution`/… stay as 1-line delegators (public API unchanged). Drop the vulture-dead accessors
   after a zero-consumer grep.
2. **Contributor pipeline** — dissolves `_wire_cqrs`. Declarative registries (projections, services,
   CQRS contributors) + a ~20-line `wire(ctx)` driver. Core projections become factories; host handlers
   become a `HostCqrsContributor`. **The driver takes a root-agnostic `ctx`, not a `host`** — this is
   what lets the *second* composition root (`ServerContext`) share it instead of forking (see seam 6).
3. **`HostObservability`** (PD-018) — one collaborator owning the report; `event_plane_status`/
   `ops_status`/`control_plane_status` become delegators; magic-string bus IDs → a `BusIdentity` enum
   with identical serialized `.value`. Behavior-preserving.
4. **`WorkPlaneCoordinator`** — moves the work-drain/inbound/journal wiring + `reload_*`/`tick_*`/
   `drain_*` closures; owns `_work_drain`/`_inbound`/`_event_journal`. (Pairs with PD-011, the separate
   `inbound_service.py`.)
5. **`RuntimeSpawner` + `RecoveryCoordinator`** — extract `_spawn_runtimes`/`_recover`/outbox+webhook
   build; `start`/`shutdown` become orchestration over the collaborators.
6. **Relocate `ServerContext` up (PD-013)** — once seam 2's `ctx`-based pipeline exists, the standalone
   (host-less) branch of `common/runtimes/server/context.py` — which today instantiates every service and
   wires CQRS *inside `common`* — becomes a thin consumer of the shared pipeline. Move it out of `common`
   to `runtimes/server/` where its ~50 consumers already live. Retires PD-013 and the last 2 sanctioned
   `common→services` seams; drop `guard_deferred`'s `MAX_UPWARD` to ≤3.

## Slices (feature-per-patch; public API frozen)

Executed by **impact ÷ blast-radius**, not the seam numbers — front-load the low-risk extractions. Each
lands as a modular `app/host/<concern>/` subpackage (see Layout). Host LOC tracked: **1164 → 663** so far.

| Patch | Scope | Status | MIGRATION? |
|---|---|---|---|
| **0.48.0** | Plan + [ADR-018](adr/018-application-host-decomposition.md) + characterization tests pinning the 3 status reports + fallback branches | ✅ | — |
| **0.48.1** | Seam 3 — `app/host/observability.py::HostObservability` (1164→1040) | ✅ | no |
| **0.48.2** | Seam 1 — `app/host/services/` — 6 core services build via a dependency-ordered `HostServiceRegistry` (1040→985) | ✅ | no |
| **0.48.3** | Seam 4 — `app/host/workplane/` — `WorkPlaneCoordinator` (work-drain/inbound/journal wiring + ops) + folds in the flat `inbound_service`/`work_drain_service` (985→816) | ✅ | no |
| **0.48.4** | Seam 5 — `app/host/lifecycle/` — `RuntimeSpawner` (spawn runtimes) + `RecoveryCoordinator` (worker readiness, compensation, outbox/webhook, projection rebuild) (816→671) | ✅ | no |
| **0.48.5** | Seam 2a — `app/host/wiring/` — projection build+register extracted to root-agnostic `build_host_projections`/`register_host_projections` (671→663) | ✅ | no |
| **0.48.6** | Seam 2b — **broke the latent cycle** (below): lazy composition-root exports in `common/runtimes/server/__init__` (PEP 562), then folded `cqrs_wiring.py` into `app/host/wiring/cqrs.py`. Wiring package now complete + order-independent | ✅ | no |
| **0.48.7** | Seam 6 — **relocated `ServerContext` + `ServerApp`** out of `common` → `runtimes/server/` (**PD-013 closed**). Kills the 2 `context→services` upward edges (`MAX_UPWARD` 5→3); reusable server infra stays in `common`. [MIGRATION-0.48.md](../MIGRATION-0.48.md) | ✅ | **yes** (import path) |
| **0.48.8** | **Dead-accessor removal** — dropped 8 `@property` accessors with zero repo-wide consumers (whole-repo sweep verified) (662→629 LOC) | ✅ | **yes** (accessors) |

**T2 re-scoped (0.48.8):** the *structural* decomposition is **complete** — 6 seams extracted into modular
subpackages, PD-009/010/013/018 addressed, the two composition roots separated, host **1164 → 629 LOC**. The
remaining shrink to <350 is via **facades** (`host.flows`/`host.instances`/…), which turned out to be the
**per-shape capability surface of a composition profile** — so it moves to **0.50** ([VISION-0.50](VISION-0.50.md)),
designed together with the composition-profile work rather than blindly here.

*(Dropped from the original plan: "services ship their own `ServiceProvider`" — a service importing the
provider type from `app/host` is an upward edge; the composition root owning the provider list is the
layering-correct design.)*

**✅ Latent import cycle (found in 0.48.5) — FIXED in 0.48.6.**
`services.definitions.service` → `common.runtimes.server.plans` → (`server/__init__` eagerly imported
`server.app`/`context`) → `ServerContext` → `services.definitions` (partial). It only stayed quiet because
`cqrs_wiring` happened to sort before `services` and pre-load the chain. Fixed at the root by making the
composition-root exports (`ServerApp`/`ServerContext`/`ServerWebhookBridge`) **lazy** in
`common/runtimes/server/__init__` — importing server *infra* (`.plans`, `.middleware`) no longer pulls the
service layer, order-independent. This de-risks the eventual `ServerContext` relocation (seam 6), which is
now purely architectural (kill 2 upward edges + put the composition root in `runtimes`), not a cycle fix.

**Invariant:** `host.execute`, `host.ask`, `host.start`, `host.shutdown`, `submit_flow`/`submit_process`/
`provide_input`/`resume_process`/`invoke_resource`, the thin service accessors, and `run_host` keep
identical signatures/behavior.

## Risks & dependencies

- **T3 satisfied.** The wiring that had to hoist before seams 1–2 could extract cleanly is hoisted; the
  10 residual function-local imports in the host are the lifecycle-lazy ones, addressed by seams 4–5.
- **Coverage** — the fragile bits are the 13 degrade-to-fallback `except Exception` and the status
  branches. Mitigate with the 0.48.0 characterization tests **before** extracting.
- **Two composition roots** — `ApplicationHost` and `ServerContext` must share a **root-agnostic**
  contributor interface (`ctx`, not `host`), or they fork further. This is the main way to get seam 2
  wrong, and the reason seam 6 (PD-013) comes *after* the pipeline, not before.
- **Churn** — `application_host.py` + `cqrs_wiring.py` are the hottest files; front-load low-blast-radius
  extractions (observability, dead-accessor removal), defer the pipeline unification.

## Exit criteria

`ApplicationHost` < 350 LOC, zero `Any` service slots, `_wire_cqrs` gone; one observability object
(PD-018 closed); services self-register; `ServerContext` relocated (PD-013 closed); public API unchanged;
suite green; a `MIGRATION-0.48.md` for the accessor/alias/import-path removals. Bonus: retires a large
chunk of the mypy errors (the `Any`-typed slots), moving mypy toward a blocking gate.
