# ADR-017: Sanctioned import seams — closing T3 (0.47)

## Status

**Accepted** — July 2026 (0.47.9, TECH-DEBT theme T3)

## Context

T3 (PD-012) drove the **upward, cycle-forcing function-local `palm` imports** from **35 → 5** across
0.47 (see [VISION-0.47](../VISION-0.47.md)). The technique throughout was *dependency inversion*: move
the shared **state** (registries) below `common`, and have higher layers **register downward** instead
of `common` reaching up. Landed inversions:

- pattern + provider registries → `common/{patterns,providers}/_registry` (0.47.5)
- storage key-listing → `BaseBackend.keys_with_prefix` polymorphism (0.47.6)
- service CQRS contributors → `common/cqrs/service_contributors`, services self-register on import (0.47.7)
- `job_inspect` → a `JobInspectable` capability; each pattern owns `inspect_job` (0.47.8)
- analytics preflight + assist CTA enrichment → contributor registries; the domain registers a probe /
  enricher downward (0.47.9a)

The **5 remaining** upward edges are *not* cycle-dodges — they sit at genuine **composition-root** and
**lazy-loading** boundaries, where knowing a concrete higher-layer type is the layer's actual job.
Inverting them would add machinery (or a large relocation) for no cycle-safety gain. We sanction them
explicitly rather than chase a vanity zero.

## Decision

**Accept these 5 as documented seams; forbid any *new* upward edge.** The `scripts/guard_deferred.py`
ratchet holds `MAX_UPWARD = 5`; because the ratchet only ever lowers, any new upward import fails
`just ci`. The sanctioned seams:

1. **`app/app.py` → `runtimes.{embedded,daemon,server}` (3)** — the runtime **factory**. `app` is the
   composition root; `_build_runtime(kind)` imports only the runtime actually selected, so an embedded
   process never pulls the server HTTP stack. Runtimes do **not** import `app` at runtime (their
   `ApplicationHost` refs are `TYPE_CHECKING`), so there is no cycle — this is deliberate lazy loading,
   not an escape valve.
2. **`common/runtimes/server/context.py` (`ServerContext`) → `services._cqrs_wiring`,
   `services.design.contributors` (2)** — `ServerContext`'s *standalone* (host-less) branch is a full
   composition root: it instantiates every service and wires the CQRS buses. That is `app`/`runtimes`
   work misplaced in `common` — the true shape of **PD-013** (the "dual `server/` trees"). The right
   fix is to **relocate the composition root up**, not to invert two wiring calls in place.

**PD-013 / `ServerContext` relocation is deferred to 0.48 (T2 — `ApplicationHost` decomposition).**
`ServerContext` is a second composition root parallel to `ApplicationHost`; both are decomposed by the
same seam work, so moving it belongs with T2, not as a standalone ~50-import-site churn (+ MIGRATION)
tacked onto T3.

## Consequences

- **Positive.** The dependency graph's real shape is now top-level and honest: 5 named seams with a
  rationale, guarded against regression. The 81-module SCC above `core` is broken; `guard_core` holds.
- **Negative.** Two of the five (`ServerContext`) are acknowledged debt still carried, tracked under
  **PD-013** and scheduled for 0.48. The guard would need its ceiling lowered again then.
- **Follow-through.** When `ServerContext` moves in 0.48, drop `MAX_UPWARD` to `3` (or lower) and note
  any public import-path change in `MIGRATION-0.48.md`.
