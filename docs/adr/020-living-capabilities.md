# ADR-020: Living capabilities — the composition profile's third axis (0.51)

## Status

**Proposed** — July 2026 (0.51.0, theme: Living Capabilities). Sibling of
[ADR-019](019-composition-profiles.md); planned in [VISION-0.51](../VISION-0.51.md).

## Context

0.50 introduced `CompositionProfile` — a typed dataclass with three name-fields: `services`,
`surfaces`, `capabilities`. Two came alive (0.50.2 services, 0.50.3 surfaces). The third did not:
`capabilities` is **declared and gated by nothing** (`grep "composition.has(" src/palm` → empty).

The machinery those capabilities *should* gate is still wired the pre-0.50 way — scattered across
settings flags (`enable_compensation`, `enable_webhook_dispatcher`, `enable_work_drain_service`),
deployment-profile flags (`profile.enable_outbox_service`, `profile.master`), a runtime start-option
(`enable_event_outbox`), infra-readiness checks (journal), and — for **projections** — nothing at all
(wired unconditionally in `_wire_cqrs`/`_attach_projections`). And `composition_profile_from_settings`
is still the 0.50.1 stub returning `all_in_one()`.

This is the *same* scattered-mechanism problem 0.50 solved for the other two axes, left unfinished for
the capability axis. It also blocks the deeper goal from [ADR-019 / 0.50.5f](019-composition-profiles.md):
`ServerContext` can only be folded into `ApplicationHost` once the host can express a **lean,
projection-less** shape — which requires projections to be a capability.

## Decision

Make `CompositionProfile.capabilities` the **authoritative third axis** — the single declared source of
which background/recovery/dispatch machinery a shape wires — using palm's existing idioms, not new ones.

1. **The resolver derives capabilities.** `composition_profile_from_settings` maps the scattered
   `enable_*` flags onto `capabilities`, **pinned against today's behavior** by tests before anything
   gates on it (the 0.50.1 safety-net discipline). Settings **refine** the profile; they never bypass it.

2. **`composition.has(capability)` is the one gate.** Each host piece (`RecoveryCoordinator`,
   `WorkPlaneCoordinator.wire_*`, projection attach) reads the capability instead of a private flag —
   a `Capability → wiring` map in the register-downward idiom, the shape of `core_service_registry()`.

3. **Composition declares *availability*; deployment decides *activation*.** The axes stay orthogonal
   (ADR-019). Pure-composition capabilities (`compensation`, `webhook`, `journal`, `projections`,
   reliable-events `outbox`) are had-or-not. Deployment-activated ones (outbox **drainer**, `work_drain`
   background loop) gate on `composition.has(cap) and profile.<activates>` — the seam kept explicit,
   preferably via one `capability_active(composition, profile, cap)` helper rather than scattered `and`s.

4. **Projections become a capability.** A `projections` capability gates the projection layer. Absent,
   `ApplicationHost` wires none — expressing the lean shape only `ServerContext` can today. This is the
   careful last slice; the `ServerContext` fold-in it *enables* is assessed (0.51.6), not forced.

Sequenced low-risk → high-care: resolver derives (pinned) → compensation/webhook gated → outbox/work_drain
(available × activated) → journal gated → projections-as-capability → *assess* the fold-in.

## Consequences

- **Positive.** The profile's three-field promise becomes fully true; the scattered capability flags
  unify into one declared axis (settings/deployment refine, never bypass); the composition × deployment
  seam is named and honored; and — the payoff — `ApplicationHost` can finally express the lean,
  projection-less shape, making the ADR-019 "one assembler over all shapes" endpoint *reachable*.
- **Negative / risk.** Touches recovery, workplane, and projection wiring — the host's live machinery.
  Capabilities must be derived and **pinned against current behavior** before any gate reads them, or a
  shape silently loses (or gains) a background loop. The available-vs-activated distinction must not be
  flattened, or worker/master behavior diverges wrongly. Projections-as-capability (0.51.5) changes what
  `ApplicationHost` *can be* — land it behind the trusted, pinned earlier slices.
- **Bounded.** The `ServerContext` fold-in stays out of scope unless 0.51.6 finds it a genuine
  simplification. Runtime-level `enable_event_outbox` may stay a start-option (it precedes any
  composition); the boundary is documented, not forced into the profile.

## Alternatives considered

- **Delete `settings.enable_*` outright.** Rejected — settings are the operator's override surface; the
  resolver pattern (settings → profile → wiring) keeps both the declared default and the override.
- **Collapse capabilities onto `DeploymentProfile`.** Rejected — most capabilities are *what the app is
  made of*, not *where it runs*; only activation is deployment. Merging the axes would undo ADR-019.
- **Force the `ServerContext` dissolution now.** Rejected by 0.50.5f — destructive without the lean
  `ApplicationHost` this theme first makes possible.
