# VISION 0.50 — Composition Profiles

**Status:** 🟢 **Planned — opens at 0.50.0.** The first capability theme after the debt-paydown line
(0.46 T1 → 0.47 T3 → 0.48 T2) and the 0.49 naming minor. Design is grounded (see §Mechanism); the build is
sequenced in §Slices.

**Lineage:** seeded mid-0.48 while decomposing `ApplicationHost` (the god-object had no declared *shape*);
its vocabulary was carved in **0.49** (`DeploymentProfile`, `PalmKernel`, and the `CompositionProfile` name).
0.50 builds the mechanism those names anticipate.

**Thesis:** the god-object wasn't just too big — the app's **composition** (which services / surfaces /
capabilities make it up) had no name and no declaration; it was hand-coded per composition root. 0.50 names it
(`CompositionProfile`) and makes `ApplicationHost` a thin **assembler** over a declared shape, so palm's already-
real shapes (headless / embedded / lib / edge / worker / server) become *declarations*, not bespoke classes.

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

A running app is assembled from a **`CompositionProfile`** and a **`DeploymentProfile`**.

> Rationale (user, kickoff): *"selecting a composition profile for the palm app is coherent alongside the
> deployment profile"*; *"app shape is confusing for referring to palm."*

**Landed (the vocabulary in code):**
- ✅ **0.49.1** — `HostProfile` → `DeploymentProfile` (+ `HostProfilePreset`/`HostRoleName`/`host_profile_from_settings`).
- ✅ **0.49.2** — `PalmApp` → `PalmKernel`, `palm.app.app` → `palm.app.kernel` — the infra *substrate*, not "the app".

**Still open (settle when the mechanism lands):**
- The two composition roots — `ApplicationHost` (the assembler) vs `ServerContext` — converge: "server" becomes
  a `CompositionProfile`, not a separate class. What does the surviving assembler get called (keep
  `ApplicationHost`, or `PalmHost`)? — decide alongside building the `CompositionProfile` mechanism.

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

**North star — a declarative `CompositionProfile`.** An app is *declared* (its services, projections, surfaces,
collaborators, contributors), and `ApplicationHost` becomes a thin **assembler** over that declaration — the way
a Django project is `INSTALLED_APPS` + settings, not a god-class. "Another app" becomes "another profile", not
"another god-class." The `DeploymentProfile` composes *with* it (a running app = composition + deployment), it
doesn't merge into it.

## Mechanism — grounded in what palm already has (don't invent)

The design falls out of a survey of the existing **extensibles + configs**: palm's composition isn't missing,
it's **scattered across four mechanisms that don't know about each other.**

| Mechanism | Declares | Scope today |
|---|---|---|
| `INSTALLED_SERVICES` / `_PATTERNS` / `_PROVIDERS` / `_STORAGES` (+ `autoload()`) | *which plugins exist* | global, per-domain |
| `default_surfaces(ctx)` (server runtime) | *which surfaces are exposed* | **hardcoded function** — the one domain with no `INSTALLED_` list |
| `PalmSettings.enable_*` (`work_drain`, `compensation`, `outbox`, `webhook`, `analytics`, …) | *which optional capabilities are on* | config flags |
| `ApplicationHost.__init__` / `ServerContext.__init__` | *which services + projections + collaborators get built* | hardcoded per composition root |

**`CompositionProfile` is the convergence of those four into one named shape** — not new machinery. And palm
already ships the exact template on the *other* axis: **`DeploymentProfile`** is a typed dataclass of name-tuples
(`roles`), with presets (`all_in_one`/`server_only`/…), resolved from settings by
`deployment_profile_from_settings`. `CompositionProfile` is its twin:

```
DeploymentProfile   roles=(master, worker, server)                   # already exists — the "where/how" axis
CompositionProfile  services=(…), surfaces=(…), capabilities=(…)     # the "what" axis, same shape
```

Low bet: no manifest DSL, no plugin framework — the tuple-of-installed-names + preset + settings-resolver idiom
palm already lives by, applied to the composition axis.

### The needs answer the fields

The shapes palm already ships tell us what a `CompositionProfile` must express (this is the "find the answer
from our needs" table):

| Shape | services | surfaces | background (work-drain / outbox) | facade |
|---|---|---|---|---|
| `all_in_one` | all | (optional) | on | full |
| `server` | all | rest / ssr / mcp / ws | on | — |
| `embedded` / lib (palmengine-django) | core only | **none** | **off** | submit / ask only |
| `worker` / daemon | execution | none | on | — |
| `cli` | all | none | on | cli |
| `mcp` | all | mcp | on | — |

### What this collapses

- `default_surfaces(ctx)` stops being a hardcoded function → becomes a `CompositionProfile.surfaces` field.
- The scattered `enable_*` settings become profile-level defaults (settings still override per the
  `*_from_settings` resolver pattern).
- **`ServerContext` dissolves** into `CompositionProfile.server()` — the two hand-coded composition roots become
  one assembler (`ApplicationHost`) over a declared profile. This is the biggest, most careful move of the theme.
- Facades (`host.flows` / `host.instances`) are the **capability surface** a profile turns on/off per shape.

## Open questions (mostly resolved by §Mechanism — left for the ADR to lock)

1. ~~Do we actually need N apps?~~ **Answered: yes** (Evidence). Remaining: *which* shapes get a first-class
   preset first — `all_in_one`/`server` exist; `embedded` is the palmengine-django case; `worker` is daemon-shaped.
2. ~~How declarative, how soon?~~ **Answered:** a typed `CompositionProfile` dataclass mirroring `DeploymentProfile`
   (tuple-of-names + presets + settings resolver) — not a manifest DSL. Author-facing profiles (0.50.6) can layer
   on later without changing this.
3. ~~Relationship to `DeploymentProfile`?~~ **Orthogonal** — composition (what) × deployment (where/how); a running
   app takes one of each. They never merge.
4. **Facade API & compatibility** (0.50.4) — additive (keep flat methods as thin delegators) vs clean break. *Open.*
5. **Where do profiles live?** `app/profiles/` beside `app/host/roles.py`? Registry of named profiles for the
   author-facing case (0.50.6)? *Open — decide when 0.50.6 is warranted.*

## Slices (feature-per-patch; low-risk → high-care)

Sequenced so the profile *exists and is trusted* before anything assembles from it, and the risky
composition-root convergence lands last.

| Patch | Scope | MIGRATION? |
|---|---|---|
| **0.50.0** | Plan (this doc) + [ADR-019](adr/019-composition-profiles.md). Vocabulary already in code (0.49). | — |
| **0.50.1** ✅ | **`CompositionProfile` skeleton** — typed dataclass (`services`/`surfaces`/`capabilities` name-tuples) + presets + `composition_profile_from_settings` seam. Mirrors `DeploymentProfile`; `all_in_one().services` pinned to `CORE_SERVICE_PROVIDERS`. Declared, not wired. | no |
| **0.50.2** ✅ | **`ApplicationHost` reads its profile (services)** — `build_all(only=composition.services)` with dependency closure; slots + cross-wiring guarded for absent services. Default (all six) unchanged; **the embedded shape is now real** (core-3, starts clean). Next: capabilities from `enable_*`. | no |
| **0.50.3** ✅ | **Surfaces from the profile** — `default_surfaces(ctx, only=…)` filters by `CompositionProfile.surfaces`, threaded from `ctx.host.composition`. `all_in_one` declares the full surface set (server-deploy unchanged); a subset (e.g. mcp) mounts fewer. | no |
| **0.50.4** | **Facades** — `host.flows` / `host.instances` / `host.jobs` as the capability surface a profile turns on/off; the <350 LOC shrink deferred from T2 lands here. | **yes** (facade API) |
| **0.50.5** | **`ServerContext` dissolves** → `CompositionProfile.server()`; the two composition roots become one assembler (`ApplicationHost`) over a declared profile. The careful one. | **yes** (import path) |
| **0.50.6** | *(optional)* **Author-facing profiles** — users declare their own `CompositionProfile` (the `palmengine-django` embedding enablement); a registry of named profiles if warranted. | — |

## Exit criteria

One assembler (`ApplicationHost`) over declared `CompositionProfile`s; `ServerContext` gone; palm's shapes
(`all_in_one`/`server`/`embedded`/`worker`/`cli`/`mcp`) are **declarations**, not bespoke classes; the
`palmengine-django`-style embedded/lib shape works via `CompositionProfile.embedded()`; `default_surfaces`
+ the scattered `enable_*` composition flags subsumed into the profile; suite green throughout; public-API
changes (facades, the `ServerContext` path) carried in `MIGRATION-0.50.md`. Bonus: `ApplicationHost` finally
crosses <350 LOC as the facade/profile split lands.
