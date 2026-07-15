# VISION 0.48 — Decompose `ApplicationHost` (T2)

**Theme:** TECH-DEBT **T2** — the god-object (PD-009) + its CQRS-wiring coupling (PD-010) and the three
overlapping status APIs (PD-018). **Depends on 0.47 (T3) landing first** — see §Risks.

**Why:** `src/palm/app/host/application_host.py` is 1170 LOC, one class, ~89 methods incl. **29 `@property`**
lazy service slots and a **123-line `_wire_cqrs`**; it's the #1 churn hotspot and the audit's 🔴 for Single
Responsibility. It mixes lifecycle + CQRS/projection wiring + execution facade + a 29-slot service registry +
three status vocabularies. This is the endurance-critical seam.

## Target

`ApplicationHost` shrinks to a **thin composition root** (**< 350 LOC**, no `Any` service slots) that (1) builds
infra, (2) drives a lifecycle sequence, (3) delegates a stable public API. Everything else moves to collaborators
it *holds*, and services **self-register** via a registry instead of 29 hand-written accessors. **The target model
already exists in-tree** — generalize `patterns/_registry` (`CqrsContributor`/`iter_cqrs_contributors`) and
`services/_cqrs_registry` (`ServiceCqrsContributor`/`wire_service_cqrs_contributors`); do not invent a new mechanism.

## Extraction seams (composition, not inheritance)

1. **`HostServiceRegistry`** — replaces the 29 lazy `@property` slots. A typed `ServiceProvider(name, build, depends_on)` registry (mirroring `services/_cqrs_registry`); services register providers; `build_all(ctx)` builds in dependency order. `host.system`/`host.execution`/… stay as 1-line delegators (public API unchanged). Drop the **9 vulture-dead accessors** after a zero-consumer grep.
2. **Contributor pipeline** — dissolves `_wire_cqrs`. Three declarative registries (projections, services, CQRS contributors) + a ~20-line `wire(ctx)` driver. Core projections become factories; host handlers become a core `HostCqrsContributor`. Interface takes a **`ctx`, not a `host`**, so it converges with the *second* composition root (`common/runtimes/server/cqrs.py`).
3. **`HostObservability`** (PD-018) — one collaborator owning the report; `event_plane_status`/`ops_status`/`control_plane_status` become delegators; magic-string bus IDs → a `BusIdentity` enum with identical serialized `.value`. Behavior-preserving.
4. **`WorkPlaneCoordinator`** — moves the work-drain/inbound/journal wiring + `reload_*`/`tick_*`/`drain_*` closures; owns `_work_drain`/`_inbound`/`_event_journal`. (Pairs with PD-011, the separate `inbound_service.py` split.)
5. **`RuntimeSpawner` + `RecoveryCoordinator`** — extract `_spawn_runtimes`/`_recover`/outbox+webhook build; `start`/`shutdown` become orchestration over the collaborators.

## Slices (feature-per-patch; public API frozen; run after 0.47)

| Patch | Scope | MIGRATION? |
|---|---|---|
| **0.48.0** | Plan (this doc) + **characterization tests** pinning the 3 status reports' JSON shape and the swallowed-exception fallbacks (the missing ~16% coverage) — so later moves are provably behavior-preserving | — |
| **0.48.1** | Seam 3 — `HostObservability`; optionally drop the `work_drain_background` deprecated alias | **yes** if alias dropped |
| **0.48.2** | Seam 1 — `HostServiceRegistry` scaffolding + remove 9 dead accessors | **yes** (accessor removal) |
| **0.48.3** | Seam 2a — services ship `ServiceProvider`; `_wire_cqrs` service-construction → `registry.build_all(ctx)` | no |
| **0.48.4** | Seam 2b — projection + CQRS contributor unification; `_wire_cqrs` collapses to the pipeline driver; reconcile with `server/cqrs.py` | no |
| **0.48.5** | Seam 4 — `WorkPlaneCoordinator` | **yes** if dead journal/tick methods removed |
| **0.48.6** | Seam 5 — `RuntimeSpawner`/`RecoveryCoordinator`; `__init__` slot reduction; narrow the 13 `except Exception` (touches PD-024) | no |

**Invariant:** `host.execute`, `host.ask`, `host.start`, `host.shutdown`, `submit_flow/submit_process/provide_input/
resume_process/invoke_resource`, the thin service accessors, and `run_host` keep identical signatures/behavior.

## Risks & dependencies

- **Hard dep on T3 (0.47).** The 29 function-local imports in `application_host.py` (`:568-577,627,650-651,772-813`) are exactly the wiring that must hoist to top-level before seams 1–2 can extract cleanly. 0.47.3 + 0.47.4 do this. Starting T2 first just relocates the deferred imports.
- **Coverage 84%** — the missing ~16% is the fragile bits (13 degrade-to-fallback `except Exception`, status branches). Mitigate with the 0.48.0 characterization tests before extracting.
- **Two composition roots** — the host and `common/runtimes/server/cqrs.py` must share a **root-agnostic** contributor interface (`ctx`, not `host`), or they fork further. This is the main way to get seam 2 wrong.
- **Churn** — `application_host.py` (38) + `cqrs_wiring.py` (21) are the hottest files; front-load low-blast-radius extractions (observability, dead-accessor removal), defer the pipeline unification.

## Exit criteria

`ApplicationHost` < 350 LOC, zero `Any` service slots, `_wire_cqrs` gone; one observability object (PD-018 closed);
services self-register; public API unchanged; suite green; a `MIGRATION-0.48.md` for the accessor/alias removals.
Bonus: this retires a large chunk of the 380 mypy errors (the `Any`-typed slots), moving mypy toward blocking.
