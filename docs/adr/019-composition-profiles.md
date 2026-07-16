# ADR-019: Composition profiles — declare the app's shape (0.50)

## Status

**Accepted** — July 2026 (0.50.0, theme: Composition Profiles)

> **Progress + refinement (0.50.5e–f):** decisions 1–2 landed. Decision 3 — *the two composition
> roots collapse into one* — is **refined**: both `ApplicationHost` and the host-less `ServerContext`
> now build their services through the **same** `core_service_registry()` (the convergence that
> mattered). But building the mechanism revealed `ServerContext` is not redundant logic to delete — it
> is the surface-facing context type (~50 files) *and* a genuinely leaner phenotype (direct-from-runtime
> dispatch, no projection layer — the server-side sibling of `embedded()`). So decision 3 is achieved
> **at the service-build layer**, and `ServerContext` is **retained** as the lean server composition
> root. Fully folding it into `ApplicationHost` would need **projections modeled as a capability** (so
> the assembler can express the lean shape) — a coherent *future* theme (0.51+), not a 0.50 slice. See
> the revised-understanding note in [VISION-0.50](../VISION-0.50.md).

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

3. **The two composition roots share one service genome.** *(Refined at 0.50.5e — see the Status note; the
   original wording was "`ServerContext` dissolves into `CompositionProfile.server()`".)* Both
   `ApplicationHost` and the host-less `ServerContext` build services through the **same**
   `core_service_registry()`. "server" *is* a composition. But `ServerContext` is **retained**, not deleted:
   it is the surface-facing context and the lean, projection-less server phenotype. This is the payoff (one
   service-build genome, expressed as many phenotypes) and the most careful move; it landed last (0.50.5d–e),
   behind the trusted skeleton. Collapsing the two *types* into one assembler awaits projections-as-a-capability
   (a future theme).

Sequenced low-risk → high-care: skeleton + presets (pinned against today's behavior) → host reads profile →
surfaces from profile → facades → service-build convergence (both roots → `core_service_registry()`) →
optional author-facing profiles.

## Consequences

- **Positive.** Every shape becomes a declaration, not a bespoke class; adding one (or embedding palm as a
  library) is authoring a `CompositionProfile`, not editing a god-class. The four scattered composition
  mechanisms unify. `ApplicationHost` crosses <350 LOC as the facade/profile split lands. The
  `palmengine-django` shape becomes first-class (`CompositionProfile.embedded()`).
- **Negative / risk.** Touches the composition roots and public API (facades) → `MIGRATION-0.50.md`. Presets
  must be pinned against current behavior (0.50.1 tests) before anything assembles from them, or a shape
  silently drifts. *(The feared `ServerContext` import-path migration did not materialize — 0.50.5e converged
  the service build without removing the type; see the Status note.)*
- **Bounded.** Author-facing / user-declared profiles and a named-profile registry are deferred to 0.50.6,
  *only if warranted* — the internal typed-dataclass mechanism ships first and stands alone.
