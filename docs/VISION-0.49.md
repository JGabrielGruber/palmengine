# VISION 0.49 — App composition profiles (DRAFT, for discussion)

**Status:** 🟡 **DRAFT — warranted, not yet scheduled.** Opened mid-0.48 (T2) as a design note. The core open
question ("is there a real second-app shape?") is now **answered: yes** — see Evidence — so this is a real
direction, not a YAGNI hedge. Slice list is still a sketch; supersede/rewrite freely at the real `0.49.0`.

**Seed:** while decomposing `ApplicationHost` (T2), a deeper question surfaced — *the god-object isn't just
too big, it has no declared **shape**.* This doc captures that thread so we can decide how far to take it.

## Evidence — palm is already multi-shape (the need is real, not speculative)

The abstraction is warranted because the shapes already exist, hand-coded:

- **The runtimes are shapes:** `embedded`, `daemon`, `server`, `cli`, `mcp` — palm is *designed* to run
  headless / embedded / as a lib / on the edge / as a worker. Each assembles a different composition.
- **Two composition roots already coexist:** `ApplicationHost` (the all-in-one host shape) and `ServerContext`
  (the server-standalone shape). 0.48.7 *separated* them (relocating `ServerContext` to `runtimes/server/`) —
  which means we now have **two hand-coded compositions of the same parts, side by side, with no shared
  declaration.** That duplication is the smell 0.49 resolves.
- **Prior art:** `palmengine-django` (archived, ~0.13) embedded palm inside Django and worked — a proven
  embedded/library shape.

So the question isn't *whether* to support multiple shapes (we already do, badly) — it's whether to keep
hand-coding each composition root or **declare the shape once and assemble it**.

## Naming — the anchor vocabulary (decided at 0.49 kickoff)

Two axes, two deliberately-**distinct** names (not both `*Profile`-with-`app`, so the axes never blur; and
avoiding "app" as a modifier, which is ambiguous — palm *is* the engine):

- **`CompositionProfile`** — *what* an app is made of: the declared set of services, surfaces, projections, and
  collaborators. The 0.49 centerpiece.
- **`DeploymentProfile`** — *where/how* it runs: the deployment roles today in `HostProfile`
  (`all_in_one` / `worker_only` / `server_only`). Rename `HostProfile` → `DeploymentProfile`.

A running app is assembled from **`CompositionProfile` × `DeploymentProfile`**.

> Rationale (user, kickoff): *"selecting a composition profile for the palm app is coherent alongside the
> deployment profile"*; *"app shape is confusing for referring to palm."*

**Open naming threads** (the "app" ambiguity, to settle next):
- The two composition roots — `ApplicationHost` (the assembler) vs `ServerContext` — should converge: "server"
  becomes a `CompositionProfile`, not a separate class. What does the surviving assembler get called?
- `PalmApp` is the infra *substrate* (storage + runtime registry), not "the app" — rename to a
  non-"app" word (e.g. `PalmKernel`), or keep + document the distinction?

## The insight — two shapes are tangled in `ApplicationHost`

There are **two independent axes** of "what an app is", and today only one has a name:

| Axis | Question | Today |
|---|---|---|
| **Deployment** | *Which runtimes run?* (all-in-one / server / worker / master) | ✅ `HostProfile` — explicit, works |
| **Composition** | *What is the app made of?* (which services, projections, surfaces, collaborators) | ❌ **implicit** — hardcoded in `__init__` + `_wire_cqrs` |

The composition shape has **no name and no declaration** — `ApplicationHost` simply *is* that shape. That's
plausibly the *root* of the god-object: every capability got soldered onto one class because there was no
"this is the composition of app X" to attach it to. **We're lacking a composition profile**, distinct from the
deployment `HostProfile`.

"We need complexity" — an orchestration engine is *irreducibly* complex; the goal is not to delete that but to
give it a **shape you can point at**. A declared composition is that shape.

## What 0.47 + 0.48 already built toward this

This is the encouraging part — the foundation is largely in place:

- **Registries that list the parts a composition would name:** `HostServiceRegistry` (service providers),
  `build_host_projections`, the CQRS/preflight/session-view contributor registries.
- **Modular collaborators** (`observability`, `services/`, `workplane/`, `lifecycle/`, `wiring/`) — the app's
  capabilities are now *nameable objects*, not methods lost in a 1164-line class.
- `ApplicationHost.__init__` already reads like an **implicit manifest**: "I compose these 6 services, these
  projections, these 5 collaborators." The move is to make that explicit.

## The direction (sketch)

**Near-term bridge — facade attributes.** Group the host's ~30 public methods into cohesive sub-facades
(`host.flows.submit(…)`, `host.instances.list(…)`, `host.jobs.tick()`, `host.work.…`) instead of a flat wall.
This shrinks the host toward <350, makes the API navigable, and — crucially — *surfaces the capabilities as
structure*. It is also the cheapest thing that makes the shape visible.

**North star — a declarative `AppProfile` / composition manifest.** An app is *declared* (its services,
projections, surfaces, collaborators, contributors), and `ApplicationHost` becomes a thin **assembler** over
that declaration — the way a Django project is `INSTALLED_APPS` + settings, not a god-class. "Another app" then
becomes "another manifest", not "another god-class." The deployment `HostProfile` composes *with* it (shape ×
deployment), it doesn't merge into it.

## Open questions (to discuss before planning)

1. ~~Do we actually need N apps?~~ **Answered: yes** (see Evidence). Shapes already exist — headless, embedded,
   lib, edge, worker — and two composition roots (`ApplicationHost`, `ServerContext`) are already hand-coded.
   The remaining question is *which shapes get a first-class profile* and in what order (host / server exist;
   embedded-lib is the palmengine-django case; worker/edge are daemon-shaped).
2. **How declarative, how soon?** Options on a spectrum: (a) keep imperative `__init__`, just extract facades;
   (b) a typed `AppProfile` dataclass the host reads; (c) a full django-apps `INSTALLED_*` manifest with
   autoload. Each is a different bet size.
3. **Relationship to `HostProfile`.** Composition (what) vs deployment (where/how) — kept orthogonal, or unified
   into one "app definition" with both facets?
4. **Facade API & compatibility.** Grouped attributes are a public-API change. Additive (keep flat methods as
   delegators) or a clean break with a `MIGRATION`?
5. **Where does a manifest live?** `app/profiles/`? A registry of `AppProfile`s (django-app style)? Author-facing
   (users declare their own app) or internal-only?

## Tentative sequence (if we proceed)

1. **Facade decomposition** — methods → `host.<facade>.<verb>()`; the facades are the *capability surface*.
   Host shrinks; the shape becomes visible. *(Design these as composable capabilities, since a profile turns
   them on/off per shape — not blind method-grouping.)*
2. **Make `__init__` an explicit `AppProfile`** — the implicit manifest becomes a typed, inspectable object the
   host assembles from.
3. **Collapse the two composition roots** — `ApplicationHost` and `ServerContext` both assemble from a declared
   `AppProfile` instead of hand-coding; the runtimes select/parameterize a profile. This is where the real
   payoff lands (headless / embedded-lib / edge / worker shapes become declarations).

## Recommendation (revised — the need is now confirmed)

Because the multi-shape need is **real and already hand-coded**, the facade decomposition is *not* separable
from this theme: **facades are the per-shape capability surface** a profile assembles (a lib/embedded app has
no `host.jobs.tick()` / no server surfaces; the server shape has no CLI facade). Doing facades blindly inside
T2 would risk redoing them once the profile lands. So:

- **Finish the genuinely-independent tail of T2 now** — **dead-accessor removal** (pure cleanup, forward-
  compatible with any profile design). This "finishes what's left" of T2 that the profile work does *not* touch.
- **Re-scope T2's exit:** the *structural* decomposition is done (seams extracted, PD-013 closed, modular
  subpackages, the two composition roots separated). The final shrink to <350 via **facades moves into 0.49**,
  because facades = composition-profile capability surface — same problem, design them together.
- **Then plan 0.49 properly**, grounded in the real shapes + `palmengine-django` as the validation case:
  declare a shape once, and make both `ApplicationHost` and `ServerContext` assemble from it.

**Decision needed from you:** (a) OK to land T2 at "structurally complete" (dead-accessor cleanup + docs), moving
the facade/`<350` work into 0.49? and (b) how additive-vs-clean-break do you want the eventual facade API?
