# ADR-018: `ApplicationHost` decomposition strategy (0.48)

## Status

**Accepted** — July 2026 (0.48.0, TECH-DEBT theme T2)

## Context

`app/host/application_host.py` is the composition root and the project's worst SRP offender (PD-009):
1164 LOC, 79 methods, **29 `@property` lazy service slots** (all `Any`-typed — a large share of the
mypy debt), a ~106-line `_wire_cqrs` hand-wired root (PD-010), three overlapping status vocabularies
(PD-018), and 13 degrade-to-fallback `except Exception`. It is the #1 churn hotspot, so every unrelated
change risks it.

A second composition root exists: `common/runtimes/server/context.py` (`ServerContext`) independently
instantiates every service and wires CQRS in its standalone branch — the real shape of PD-013, deferred
to this theme from T3 ([ADR-017](017-import-seams.md)).

T3 (0.47) already proved the mechanism this theme needs: **registries that domains populate downward on
import, drained by a thin driver** (`common/patterns/_registry`, `common/cqrs/service_contributors`,
`preflight_registry`, `session_view_registry`).

## Decision

Decompose by **composition, not inheritance**, keeping the public API frozen. Three load-bearing choices:

1. **Services self-register into a `HostServiceRegistry`.** Replace the 29 hand-written `@property`
   accessors with typed `ServiceProvider(name, build, depends_on)` entries that each service registers
   on import; `build_all(ctx)` constructs them in dependency order. The `host.system`/`host.execution`/…
   accessors survive as 1-line delegators, so no caller changes. This kills the `Any` slots (each
   provider is typed) and the 29-accessor boilerplate at once.

2. **One `ctx`-based contributor pipeline, shared by both roots.** `_wire_cqrs` dissolves into
   declarative projection / service / CQRS-contributor registries drained by a ~20-line `wire(ctx)`
   driver. **The driver takes a root-agnostic `ctx`, never a `host`.** This is the linchpin: it is the
   only thing that lets `ServerContext` (seam 6 / PD-013) consume the *same* pipeline instead of forking
   a parallel one. Getting seam 2 wrong = passing `host` = PD-013 never closes.

3. **Behavior-preserving extractions, pinned by characterization tests first.** Before any move, 0.48.0
   lands tests that freeze the JSON shape of the three status reports and the degrade-to-fallback
   branches (the thin-coverage, fragile bits). Observability collapses to one `HostObservability`
   collaborator; magic-string bus IDs become a `BusIdentity` enum whose `.value` serializes identically.

Sequencing is **impact ÷ blast-radius**: front-load low-risk extractions (observability, dead-accessor
removal), then the registry, then the pipeline, then — only once the `ctx` pipeline exists — relocate
`ServerContext` (PD-013), then the work/runtime coordinators.

## Consequences

- **Positive.** `ApplicationHost` becomes a <350 LOC composition root delegating to named collaborators;
  PD-009/010/018/013 close together; the `Any` service slots (a big mypy chunk) disappear, moving mypy
  toward a blocking gate; the two composition roots converge on one wiring path.
- **Negative / risk.** These are the hottest files in the tree — extractions must stay small and green
  per slice, guarded by the 0.48.0 characterization tests. Accessor/alias/import-path removals are
  breaking-ish internally → `MIGRATION-0.48.md`.
- **Deferred.** Observability *unification* across `event_plane`/`ops`/`control_plane` semantics is T5
  (PD-018 here only extracts the report object + de-magics bus IDs, behavior-preserving).
