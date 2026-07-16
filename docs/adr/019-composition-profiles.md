# ADR-019: Composition profiles — declare the app's shape (0.50)

## Status

**Accepted** — July 2026 (0.50.0, theme: Composition Profiles)

## Context

palm ships multiple app *shapes* — `embedded`, `daemon`, `server`, `cli`, `mcp` runtimes, plus the
`palmengine-django` embedding — but the **composition** of each (which services, surfaces, projections,
collaborators, and capabilities it is made of) is not declared anywhere. It is hand-coded across **four
mechanisms that don't know about each other**:

- the global `INSTALLED_SERVICES` / `_PATTERNS` / `_PROVIDERS` / `_STORAGES` lists (which plugins *exist*),
- `default_surfaces(ctx)` — a hardcoded function (surfaces have no `INSTALLED_` list),
- `PalmSettings.enable_*` flags (which optional capabilities are *on*),
- `ApplicationHost.__init__` / `ServerContext.__init__` (which pieces get *built*).

The visible symptom was the T2 god-object (PD-009) and the **two hand-coded composition roots**
(`ApplicationHost` + `ServerContext`, separated in 0.48.7). There is no single place that says "*this* is
what app X is made of," so every shape is a bespoke class.

## Decision

Introduce **`CompositionProfile`** — the *what it's made of* axis — as the twin of the existing
`DeploymentProfile` (the *where/how it runs* axis). A running app is assembled from **one
`CompositionProfile` and one `DeploymentProfile`**; the two are orthogonal and never merge.

Three load-bearing choices:

1. **Converge, don't invent.** `CompositionProfile` is the unification of the four scattered mechanisms into
   one declared shape — it reuses palm's own idiom: a typed dataclass of **name-tuples** (`services`,
   `surfaces`, `capabilities`) with **presets** (`all_in_one`/`server`/`embedded`/`worker`/`cli`/`mcp`) and a
   `composition_profile_from_settings` resolver — exactly the shape of `DeploymentProfile`. **No manifest DSL,
   no plugin framework.** The needs (the shapes palm already ships) determine the fields.

2. **`ApplicationHost` becomes a thin assembler.** It stops hardcoding its composition and instead builds from
   its `CompositionProfile`. `default_surfaces()` becomes a profile field; the `enable_*` settings become
   profile defaults (settings still override, per the `*_from_settings` pattern). Facades
   (`host.flows`/`host.instances`) are the per-shape capability surface a profile turns on/off.

3. **The two composition roots collapse into one.** `ServerContext` dissolves into
   `CompositionProfile.server()` — "server" is a composition, not a class. This is the payoff (one assembler
   over declared profiles) and the most careful move; it lands last (0.50.5), behind the trusted skeleton.

Sequenced low-risk → high-care: skeleton + presets (pinned against today's behavior) → host reads profile →
surfaces from profile → facades → `ServerContext` dissolution → optional author-facing profiles.

## Consequences

- **Positive.** Every shape becomes a declaration, not a bespoke class; adding one (or embedding palm as a
  library) is authoring a `CompositionProfile`, not editing a god-class. The four scattered composition
  mechanisms unify. `ApplicationHost` crosses <350 LOC as the facade/profile split lands. The
  `palmengine-django` shape becomes first-class (`CompositionProfile.embedded()`).
- **Negative / risk.** Touches the composition roots and public API (facades, the `ServerContext` import
  path) → `MIGRATION-0.50.md`. Presets must be pinned against current behavior (0.50.1 tests) before anything
  assembles from them, or a shape silently drifts.
- **Bounded.** Author-facing / user-declared profiles and a named-profile registry are deferred to 0.50.6,
  *only if warranted* — the internal typed-dataclass mechanism ships first and stands alone.
