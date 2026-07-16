# VISION 0.51 — Living Capabilities (the third axis)

> *Theme (proposed name — see Open questions):* **Living Capabilities.** Make
> `CompositionProfile.capabilities` — declared since 0.50.1 but **inert** — the authoritative
> source of *which background/recovery/dispatch machinery a shape wires*. This completes the
> composition profile's third axis (services ✅ 0.50.2, surfaces ✅ 0.50.3, **capabilities → 0.51**)
> and, at its far end, unlocks a lean `ApplicationHost` via **projections-as-a-capability** — the
> soil the 0.50.5f `ServerContext` fold-in needs.

Sibling of [VISION-0.50](VISION-0.50.md) (Composition Profiles); decision in
[ADR-020](adr/020-living-capabilities.md).

---

## The through-line from 0.50

0.50 gave palm a name for its *wholes* — `CompositionProfile`, a typed dataclass with three
name-fields: `services`, `surfaces`, `capabilities`. Two of the three came alive:

- **0.50.2** — `composition.services` drives service construction (`build_all(only=…)`).
- **0.50.3** — `composition.surfaces` drives which surfaces the server mounts.

The third field never did. `CompositionProfile.capabilities` is **declared and read by nothing**:

```
$ grep -rn "composition.has(\|composition.capabilities" src/palm/   # gating wiring
(no results)
```

The profile's own docstring promises "which services, surfaces, **and capabilities**," but only
two-thirds is true. 0.51 makes the last third real.

## Evidence — the capability axis is still the scattered-mechanism problem 0.50 set out to solve

For services and surfaces, 0.50 unified four hand-coded mechanisms into one declared field. For
capabilities, that unification simply hasn't happened yet — the gating is still scattered across
settings flags **and** deployment-profile flags **and** unconditional wiring:

| Capability | How it is gated **today** | Lives on |
|---|---|---|
| `compensation` | `settings.enable_compensation` | settings |
| outbox background service | `profile.master and profile.enable_outbox_service` (+ `outbox_recover_on_startup`) | **deployment** |
| runtime reliable-events outbox | runtime `enable_event_outbox` option (default on) | runtime start |
| `webhook` dispatch | `settings.enable_webhook_dispatcher` | settings |
| `work_drain` | `settings.enable_work_drain_service or profile.enable_work_drain_service` | settings **+** deployment |
| `journal` | wired whenever storage + event are initialized (no gate) | infra-readiness |
| **projections** | **wired unconditionally** in `_wire_cqrs` / `_attach_projections` | nothing |
| `composition_profile_from_settings` | **still the 0.50.1 stub** — returns `all_in_one()`, ignores every flag above | — |

`CompositionProfile.capabilities` is exactly the named field those belong in — the same move 0.50
made for the other two axes. **This is convergence of existing mechanisms, not new machinery.**

## The insight — capabilities are *available* (composition) × *activated* (deployment)

Nailing the mechanism surfaces a real subtlety, and it is the same one 0.50.3 found for surfaces
("surfaces are *available*; the deployment *mounts* them"):

- Some capabilities are pure **composition** — *what the app is made of*: `compensation`, `webhook`,
  `journal`, `projections`, reliable-events `outbox`. Either a shape has them or it doesn't.
- Others are **composition-declared but deployment-activated** — the capability is *available*, but
  *whether this node runs it* is a role decision. The outbox **drainer** and the `work_drain`
  background service run only on the master/server role, not on every worker.

So the axes stay orthogonal, exactly as 0.50 insisted: **`CompositionProfile` declares the capability
is available; `DeploymentProfile` decides whether this running node activates it.** A worker node and
a master node can share one composition yet differ in what background loops actually spin — because
that difference is deployment, not composition. 0.51 must honor that seam, not collapse it.

## The mechanism (to be locked by ADR-020)

Mirror what worked for services and surfaces:

1. **The resolver comes alive.** `composition_profile_from_settings` stops returning a constant and
   derives `capabilities` from today's `enable_*` flags — **pinned against current behavior** by
   tests before anything reads it (the 0.50.1 discipline). This is the safety net slice.
2. **`composition.has(capability)` becomes the single gate.** Each piece of host machinery
   (`RecoveryCoordinator.recover`, `WorkPlaneCoordinator.wire_*`, projection attach) reads the
   capability instead of a scattered flag. Settings still **refine** via the `*_from_settings`
   resolver (settings → profile → wiring), so nothing loses its override.
3. **Deployment-activation stays explicit.** For the available-vs-activated capabilities, the gate is
   `composition.has(cap) and profile.<activates>` — the seam kept visible, not hidden.
4. **Projections become a capability** (the far, careful end). A `projections` capability gates
   `build_host_projections` / `_attach_projections`. When absent, `ApplicationHost` wires no
   projection layer — it can finally express the **lean shape** that only `ServerContext` can today.

No manifest DSL, no plugin framework — a `Capability → wiring` map in the register-downward idiom, the
same shape as `core_service_registry()`.

## What this unlocks (and why it is the honest 0.51, per 0.50.5f)

0.50.5f found that `ServerContext` can't be dissolved while it is the *only* thing that can express a
lean, projection-less server. Step 4 above removes exactly that blocker: once projections are a
capability, `ApplicationHost` can express the lean shape, and the "one assembler over all shapes"
endpoint becomes **reachable** — not forced. Whether the `ServerContext` type then folds in (re-typing
the ~50 surface files behind a shared context protocol) is a *later* call, made only once the lean
`ApplicationHost` exists and is trusted. 0.51 earns the ground; it does not spend it prematurely.

## Slices (feature-per-patch; low-risk → high-care)

Sequenced so `capabilities` is *derived and trusted* before anything gates on it, and the projection
move — the one that changes what `ApplicationHost` can be — lands last.

| Patch | Scope | MIGRATION? |
|---|---|---|
| **0.51.0** | Plan (this doc) + [ADR-020](adr/020-living-capabilities.md). Capability vocabulary already in code (0.50.1). | — |
| **0.51.1** | **Resolver comes alive** — `composition_profile_from_settings` derives `capabilities` from the `enable_*` flags; pinned against today's effective wiring by tests. Declared → *derived*, still not yet gating. | no |
| **0.51.2** | **Compensation + webhook from the profile** — `RecoveryCoordinator` gates on `composition.has("compensation")` / `has("webhook")` instead of `settings.enable_*` (settings refine via resolver). Behavior-preserving. | no |
| **0.51.3** | **Outbox + work_drain — available × activated** — gate on `composition.has(cap) and profile.<activates>`; the composition/deployment seam made explicit. Behavior-preserving. | no |
| **0.51.4** | **Journal from the profile** — the always-on journal becomes `has("journal")`-gated (default on for the shapes that have it). Behavior-preserving. | no |
| **0.51.5** | **Projections as a capability** (the careful one) — `has("projections")` gates the projection layer; `ApplicationHost` can now assemble the lean shape. Default (all_in_one/server) keeps projections. | possibly (new capability default) |
| **0.51.6** | *(assess, don't force)* With a lean `ApplicationHost` real, revisit the 0.50.5f `ServerContext` fold-in behind a shared surface-context protocol — **only if** it reads as simplification, not churn. | **yes** (if taken) |

## Open questions (for ADR-020 to lock)

1. **Theme name.** *Living Capabilities* (organic, true — the inert field comes alive)? *Capability-Driven
   Assembly* (plainer)? *The Third Axis*? — settle at planning, in the 0.49 naming spirit.
2. **New capability names.** `projections` is new; is `recovery` its own capability or implied by
   `compensation`+`outbox`? Keep the `Capability` `Literal` honest and minimal.
3. **Where the available×activated gate lives.** In each coordinator (explicit, scattered) vs a small
   `capability_active(composition, profile, cap)` helper (one truth). Lean toward the helper.
4. **Does the runtime-level `enable_event_outbox` fold in**, or stay a runtime start-option (it is set
   before a host/composition exists)? Likely stays; note the boundary.

## Exit criteria

`CompositionProfile.capabilities` is authoritative: every background/recovery/dispatch piece the host
wires is gated by a declared capability (settings/deployment refine, never bypass); the resolver derives
capabilities from settings (pinned); the composition-availability × deployment-activation seam is explicit
and honored; **projections are a capability**, so `ApplicationHost` can express the lean, projection-less
shape; the suite is green throughout; and the 0.50.5f `ServerContext` fold-in is *reachable* (whether it
is taken is 0.51.6's honest call). The profile's three-field promise — services, surfaces, capabilities —
is finally, fully true.

---

*One genome, three axes. 0.50 named the whole; 0.51 gives its last axis a heartbeat.* 🌴
