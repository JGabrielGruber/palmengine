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

| Patch | Scope | MIGRATION? |
|---|---|---|
| **0.48.0** | Plan (this doc) + [ADR-018](adr/018-application-host-decomposition.md) + **characterization tests** pinning the 3 status reports' JSON shape and the degrade-to-fallback branches (the missing coverage) — so every later move is provably behavior-preserving | — |
| **0.48.1** | Seam 3 — `HostObservability`; optionally drop the `work_drain_background` deprecated alias | **yes** if alias dropped |
| **0.48.2** | Seam 1 — `HostServiceRegistry` scaffolding + remove dead accessors | **yes** (accessor removal) |
| **0.48.3** | Seam 2a — services ship `ServiceProvider`; `_wire_cqrs` service-construction → `registry.build_all(ctx)` | no |
| **0.48.4** | Seam 2b — projection + CQRS contributor unification; `_wire_cqrs` collapses to the `ctx` pipeline driver | no |
| **0.48.5** | Seam 6 — relocate `ServerContext` onto the shared pipeline, out of `common` (PD-013); ratchet `MAX_UPWARD` down | **yes** (import path) |
| **0.48.6** | Seam 4 — `WorkPlaneCoordinator` | **yes** if dead journal/tick methods removed |
| **0.48.7** | Seam 5 — `RuntimeSpawner`/`RecoveryCoordinator`; `__init__` slot reduction; narrow the 13 `except Exception` (touches PD-024) | no |

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
