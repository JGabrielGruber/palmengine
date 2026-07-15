# VISION 0.47 — Break the import cycles (T3)

**Theme:** TECH-DEBT **T3** — the deferred-import / circular-dependency debt (PD-012).
**Why now:** this is the **dependency root of the complexity arc**. `ApplicationHost` (T2/0.48) can't be
decomposed cleanly while its wiring imports must stay function-local to dodge startup cycles — do T2 first
and you just relocate the cycles. T3 makes the real dependency graph visible and top-level, then T2 can move.

Runs on the green, CI-enforced baseline from T1 (0.46).

## Headline: the debt is ~4× smaller than the raw count (verified)

The audit's "595 deferred imports" (PD-012) was a single grep that conflated two very different things. An AST
classification (reproduced independently — `scripts/` candidate below) gives:

| | Count | Nature |
|---|---:|---|
| `TYPE_CHECKING` palm imports | **310** | **Not debt** — the correct way to reference cross-layer *types*; never run. |
| **function-local runtime** deferrals | **287** | The real escape valve. |
| — of which **upward / cross-layer** | **~35** | The only ones that need real dependency inversion. |
| — of which **downward** | ~91 | Cargo-cult; hoistable once their one enabling cycle is cut. |
| — of which **same-layer sibling** | ~157 | Mostly intra-`runtimes` `mcp`↔`server`. |

**The metric that matters is `upward function-local imports = 35`**, across ~8 seams. `common/__init__.py`
(lazy `__getattr__` + `_LAZY_EXPORTS`) and `patterns/_registry.py` (all `TYPE_CHECKING`) already implement the
target pattern — they're the exemplars, not debt.

## The cycles (one SCC, 35 upward edges)

At package granularity there's **one SCC of 8 packages above `core`** (`app, common, definitions, instances,
patterns, providers, runtimes, services`); `core` is clean (guard-core holds). At module granularity the
dominant SCC is 81 modules across `app.* + common.runtimes.server.* + runtimes.*`. It exists because of ~35
**upward** function-local edges, grouped:

- **`common → patterns._registry` (13)** + **`common → providers._registry` (4)** — the registry/autoload seam: `common` needs registry *data* but imports the plugin *package* to reach it.
- **`common → services` (9)** — `cqrs/schemas`, `operator/flow_session_view`, `resource/preflight`, `runtimes/server/context`.
- **`app → runtimes` (4)** — the runtime factory (`app/app.py`) + a `job_inspect` reach.
- **`{common,patterns} → runtimes.cli.shared.job_inspect` (3)** — one misplaced pattern-aware helper.
- **`common → storages` (2)** — `document_storage` reaching backends.
- **intra-`runtimes` `mcp ↔ server` (23, sibling)** — `mcp/in_process` reuses `server.rest.*` leaf helpers; only **4** `server → mcp` edges make it mutually recursive.

## Root causes → technique (ranked by impact ÷ risk)

1. **Hoist cargo-cult deferrals** (91 downward + ~130 sibling) — mechanical, once the enabling cycle is cut. *Very low risk.*
2. **Cut the 4 `server → mcp` edges** (lazy capability seam), then hoist `mcp/in_process`'s 19 `rest.*` imports. *`in_process.py` 34→~5; helps PD-015.*
3. **Relocate registry data below `common`** — move `patterns._registry`/`providers._registry` *state* into a neutral module (reuse `core.registry` or a new `palm.registry`); plugins register into it. Removes 17 upward edges. *High architectural value — realizes the django-app/registry target.*
4. **Explicit `ready()`/autoload at bootstrap** instead of `import palm.patterns` for side-effect (incl. `application_host.py:540`). Folds into #3.
5. **Move misplaced modules to their true layer** — `common/runtimes/server/*` → `app`/`runtimes` (also resolves **PD-013** dual-server-tree); reclassify `states/storages/backends/definitions/instances` as the leaves they already are.
6. **Invert `job_inspect`** — neutral formatter shell + pattern extractors via the existing `patterns._registry` hook.
7. **Runtime factory via registry** (runtimes self-register their kind) or accept as a documented lazy seam.
8. **Protocol/ABC inversion** for residual `common → services` consumers (contract in `common`/`core`, `services` implements).

## Slices (feature-per-patch; `just check` green + deferred metric strictly decreasing each patch)

- **0.47.0** — Plan (this doc) + refine PD-012 metric in the register.
- **0.47.1** ✅ — **Fitness function** `scripts/guard_deferred.py` (ratchet ceilings 287/35, AST layer-direction classification), wired into `just check` / `just ci`. Locks the graph.
- **0.47.2** ✅ — **mcp/in_process hoist**: leaf `rest.*` + mcp intra-package deferrals to top-level (32→12); ratchet 287→267.
- **0.47.3** ✅ — **Relocate shared surface helpers → `palm/common/surfaces/`** (pagination, serializers). Kills the `mcp→rest` shared-helper coupling — both surfaces depend *down* on `common`. *(added from review feedback; the only remaining `mcp→rest` edge is `build_openapi_spec`, which is the REST API's own spec.)*
- **0.47.4** ✅ — **Hoist `app`/`ApplicationHost` downward deferrals** (technique 1): `app→services` + `app→common` wiring imports to top-level. **⛳ Unblocks T2** — the god-object's true dependency surface becomes top-level and visible.
- **0.47.5** ✅ — **Pattern + provider registry inversion** (techniques 3+4): relocate `patterns._registry` **and** `providers._registry` state below `common` (into `common/{patterns,providers}/_registry.py`); delete the 13 `common→patterns` + 4 `common→providers` edges + the side-effect imports; hoist the freed sibling reads; retire the back-compat shims. Sub-slices 0.47.5–0.47.5d. *Highest architectural payoff; also unblocks T2.* (Provider half folded in here, ahead of its original 0.47.6 slot.)
- **0.47.6** ✅ — **Storage backend polymorphism** (technique 8): add `BaseBackend.keys_with_prefix` (default `[]`; memory + filesystem override), so `common.document_storage` lists keys via the contract instead of importing concrete backends. Removes the 2 `common→storages` edges and an encapsulation break (no more `isinstance` + private `_data`/`data_dir` poking).
- **0.47.7** — **Relocate `common/runtimes/server/*`** out of `common` → resolves 9 `common→services` edges **and PD-013**.
- **0.47.8** — **`job_inspect` inversion + runtime-factory registry** — last 4 + 3 upward edges.
- **0.47.9** — **Ratchet to zero + waivers:** flip `guard_deferred` to fail on any upward function-local import; re-evaluate the `patterns/wizard/** I001` isort waiver; optionally add `import-linter` layered contracts.

## Exit criteria

Upward function-local imports **35 → 0**; `guard_deferred` gating in `just ci`; the 81-module SCC broken (verify
with `grimp` SCC = trivial above `core`); `guard_core`/full suite green throughout; **T2 unblocked** (ApplicationHost
wiring imports are top-level). Breaking changes: none expected (internal moves); if `common/runtimes/server/*`
relocation changes any public import path, a `MIGRATION-0.47.md`.

## Measurement

Legacy count (matches audit): `grep -rEn '^[[:space:]]+(from palm[.]|import palm[.])' src/palm --include='*.py' | wc -l` → 594.
Precise metric (AST, excludes `TYPE_CHECKING`, classifies by layer direction): **287 runtime / 35 upward** — this
becomes `scripts/guard_deferred.py`.
