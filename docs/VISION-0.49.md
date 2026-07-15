# VISION 0.49 — App composition profiles (DRAFT, for discussion)

**Status:** 🟡 **DRAFT — not scheduled.** Opened mid-0.48 (T2) as a design note to discuss, then plan. Nothing
here is committed to; the slice list is a sketch, not a promise. Supersede/rewrite freely at the real `0.49.0`.

**Seed:** while decomposing `ApplicationHost` (T2), a deeper question surfaced — *the god-object isn't just
too big, it has no declared **shape**.* This doc captures that thread so we can decide how far to take it.

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

1. **Do we actually need N apps?** Today there is one. The honest risk is building a plugin-app framework before
   a second app exists to validate it — a speculative abstraction wrong in three places. What are the *real*
   second-shape candidates? (a headless/library-only app? an edge/worker-only app? a test harness app? a
   customer-embedding of palm with a curated capability set?)
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

1. **Facade decomposition** — methods → `host.<facade>.<verb>()`; host shrinks; shape becomes visible. *(Low risk;
   valuable regardless of how far B goes.)*
2. **Make `__init__` an explicit `AppProfile`** — the implicit manifest becomes a typed, inspectable object the
   host assembles from. Still one app; no new machinery.
3. **(Only if a real second shape appears)** — registry of profiles / author-facing declaration / multiple apps.

## Recommendation

Do **step 1 (facades)** as the tail of T2 — it's real, low-risk, and it de-risks everything after. Treat steps
2–3 as *earned by need*: let the manifest crystallize from the registries when a genuine second app shape shows
up, rather than building the framework on spec. **Decision needed:** which of the open questions above do we
want to answer now vs. defer, and is there a concrete second-app shape driving this (which would change the
calculus toward doing B sooner)?
