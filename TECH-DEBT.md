# Palm — Technical-Debt Register

**Audited commit:** `8413d0e` (v0.45.8, master, clean worktree) · **Date:** 2026-07-15 ·
**Tools:** radon/xenon/vulture/bandit/pip-audit (via `uvx`), ruff, mypy, pytest-cov, `scripts/guard_core.py`.
**Regenerate:** re-run the commands in [§ Methodology](#methodology--reproducibility) on this SHA; raw
artifacts live in [`docs/audit/`](docs/audit/). This document **catalogs** debt and suggests directions
only — refactor design & execution are out of scope ([§ Non-goals](#non-goals)).

> Scope: comprehensive audit, weighted toward **architecture/coupling**, **tests/coverage/CI**, and
> **dead-code/dupes/hygiene**; docs-drift, conventions, and dependency/security are cataloged at lower priority.

---

## Executive summary

Palm has an **intact foundation** but **eroding enforcement and composition seams**. Graded against its own
constitution (`AGENTS.md` §1):

| 🟢 healthy | 🟡 eroding | 🔴 breached |
|---|---|---|
| Core Purity · Registry Extension | Explicit Boundaries · Truth-Seeking · Minimal Magic | **Single Responsibility · Documentation-as-Code · Testability First** |

The three 🔴s are the story: the code that was supposed to keep everything else honest — **tests, CI, and
docs** — fell behind the 0.45.x *feature-per-patch* cadence, and the **composition root** (`ApplicationHost`)
plus the **assist/MCP surface** absorbed most of the growth.

**Top findings (by priority):**

1. **No CI runs tests/lint/typecheck/guards** — only `publish.yml`. Nothing gates quality. *(PD-001)*
2. **The test suite fails on master** — 19 genuine failures (incl. a `guard-common` fitness test), from tests & fakes that lagged production API changes. Invisible because of #1. *(PD-002, PD-003)*
3. **Known-vuln runtime dependency** — `pydantic-settings 2.14.1` (GHSA-4xgf-cpjx-pc3j), fixed in 2.14.2. *(PD-028)*
4. **`ApplicationHost` god-object** — 1170 LOC, 89 methods, 29 `@property`; #1 churn hotspot. Breaks the project's own SRP rule. *(PD-009)*
5. **595 deferred (function-local) imports** used to dodge circular deps — a systemic layering escape valve. *(PD-012)*
6. **Three overlapping observability APIs** (`event_plane`/`ops`/`control_plane`) with magic-string bus IDs and a live deprecated alias. *(PD-018)*
7. **Docs stamp ~30 minors behind** (ARCHITECTURE.md @0.13.13) and ADRs stop at 014 (013 missing). *(PD-019, PD-020)*

**Headline metrics:** 814 src files / 75.5k LOC (tests 265 / 30.9k) · overall coverage **80.2%** (runtimes
69.6%, core 92.8%) · **19 tests failing** on master · lint **RED**, xenon **RED**, guard-common **RED**,
guard-core **GREEN** · 595 deferred imports · 48 functions rank D–F complexity · largest file 1170 LOC.

---

## Themes

- **T1 — No CI, and a red master.** The absence of any quality gate (publish-only CI) let the suite, the lint, the complexity gate, and a fitness test all go red on master unnoticed. → PD-001…008. *(The 🔴 for Testability.)*
- **T2 — The composition root is a god-object.** `ApplicationHost` + `cqrs_wiring` + `inbound_service` concentrate lifecycle, wiring, execution, and status on one class/seam. → PD-009…011. *(The 🔴 for SRP.)*
- **T3 — Deferred imports as a layering escape valve.** 595 function-local palm imports (registration-by-side-effect + circular-dep avoidance) hide the true dependency graph. → PD-012, PD-013.
- **T4 — The assist/MCP + CLI surfaces are the complexity & coverage sink.** Highest complexity (CC up to 112) meets lowest coverage (6–35%) here. → PD-014…017.
- **T5 — Three observability vocabularies.** `event_plane`/`ops`/`control_plane` overlap, nest, and speak in magic strings. → PD-018.
- **T6 — Docs-as-code is unenforced.** Version stamps and ADRs lag the code by dozens of releases despite it being a stated invariant. → PD-019…021. *(The 🔴 for Docs-as-Code.)*
- **T7 — Placeholders & untested adapters shipped as installed.** Postgres/Mongo/GraphQL adapters and parquet/dag/etl scaffolds are registered but empty/untested. → PD-022, PD-023.
- **T8 — Navigability & convention drift.** Broad error-swallowing, pervasive filename reuse, magic constants, inconsistent module naming. → PD-024…027.
- **T9 — Dependency & security hygiene.** A CVE'd dep, unguarded `urlopen` schemes, empty extras. → PD-028…030.

---

## Debt register (master table)

Sorted by **Priority = (Severity × Reach) / Effort**, primary-dimension items nudged up. Severity S1(critical)…S4(cosmetic).
Effort XS/S/M/L/XL. Conf = confidence. Full evidence in the per-item blocks below.

| ID | Title | Theme | Cat | Sev | Reach | Effort | Prio | Conf |
|----|-------|:---:|-----|:---:|-------|:---:|:---:|------|
| PD-001 | No test/lint/typecheck/guard CI (publish-only) | T1 | ci-tooling | S1 | systemic | S | 16 | confirmed |
| PD-028 | `pydantic-settings 2.14.1` known vuln (runtime dep) | T9 | dependency-security | S3 | systemic | XS | 12 | confirmed |
| PD-002 | Test suite fails on master (19 genuine failures) | T1 | test-coverage | S1 | systemic | M | 11 | confirmed |
| PD-004 | Lint gate RED on master (~133 ruff findings) | T1 | ci-tooling | S3 | layer | XS | 9 | confirmed |
| PD-003 | Test doubles drift from prod signatures | T1 | test-coverage | S2 | layer | S | 8 | confirmed |
| PD-018 | Three overlapping observability APIs + magic-string buses | T5 | architecture | S2 | layer | M | 5 | confirmed |
| PD-009 | `ApplicationHost` god-object (1170 LOC / 89 methods) | T2 | architecture | S1 | systemic | XL | 4 | confirmed |
| PD-012 | 595 deferred imports masking circular deps | T3 | architecture | S2 | systemic | L | 4 | confirmed |
| PD-010 | `cqrs_wiring` composition-root coupling | T2 | architecture | S2 | layer | L | 3 | confirmed |
| PD-013 | Dual `server/` trees (common vs runtimes) | T3 | architecture | S3 | layer | M | 3 | confirmed |
| PD-014 | assist/MCP + CLI complexity hotspots (CC≤112) | T4 | complexity | S2 | layer | L | 3 | confirmed |
| PD-022 | DB adapters untested (postgres/mongo/graphql) | T7 | test-coverage | S2 | layer | L | 3 | confirmed |
| PD-024 | 163 broad `except Exception`, several swallow errors | T8 | convention | S3 | layer | M | 3 | confirmed |
| PD-029 | `urllib.urlopen` with no scheme allowlist (9 sites) | T9 | dependency-security | S3 | layer | M | 3 | confirmed |
| PD-030 | Empty extras `postgres=[]`/`mongodb=[]` (drivers unpinned) | T7/T9 | dependency-security | S3 | module | S | 3 | confirmed |
| PD-019 | Doc version stamps ~30 minors behind | T6 | doc-drift | S3 | layer | M | 3 | confirmed |
| PD-020 | ADR discipline broken (013 missing, stops at 014) | T6 | doc-drift | S3 | layer | M | 3 | confirmed |
| PD-031 | `docs-check` gate RED on master (skill/mcp-data mirror drift) | T6 | ci-tooling | S3 | module | S | 3 | confirmed |
| PD-006 | `.pre-commit-config.yaml` missing (half-wired) | T1 | ci-tooling | S3 | module | S | 3 | confirmed |
| PD-007 | Audit tools referenced but undeclared in pyproject | T1 | ci-tooling | S3 | module | S | 3 | confirmed |
| PD-015 | `mcp/in_process.py` 871 LOC / 35% cov / churn 20 | T4 | complexity | S2 | module | L | 2 | confirmed |
| PD-016 | Large SSR explorer files (992/941 LOC) | T4 | complexity | S3 | module | M | 2 | confirmed |
| PD-023 | Placeholder features registered as installed | T7 | placeholder | S3 | module | M | 2 | confirmed |
| PD-008 | No coverage threshold (`--cov-fail-under`) | T1 | ci-tooling | S4 | module | XS | 2 | confirmed |
| PD-005 | xenon gate RED + only scans `core/` in `just complexity` | T1 | ci-tooling | S3 | layer | L | 2 | confirmed |
| PD-017 | runtimes layer 69.6% cov; coldest files near-0% | T4 | test-coverage | S3 | layer | L | 2 | confirmed |
| PD-011 | `inbound_service.py` 725 LOC mixed responsibilities | T2 | complexity | S3 | module | L | 1 | confirmed |
| PD-026 | Magic numbers (24) + hardcoded hosts/ports (15) | T8 | convention | S4 | layer | S | 1 | confirmed |
| PD-027 | Inconsistent leading-underscore module naming | T8 | convention | S4 | layer | S | 1 | confirmed |
| PD-021 | Root markdown sprawl (28 RELEASE + 14 MIGRATION) | T6 | doc-drift | S4 | layer | M | 0.7 | confirmed |
| PD-025 | Pervasive filename reuse hurts navigability | T8 | convention | S4 | systemic | M | 0.7 | confirmed |

---

## Per-item detail

### T1 — No CI, and a red master

**PD-001 — No test/lint/typecheck/guard CI (publish-only).** `S1 · systemic · Effort S · Testability(§1), Review-Checklist(§6)`
- Evidence: `.github/workflows/` contains only `publish.yml` (build+publish). No job runs `pytest`, `ruff`, `mypy`, `guard-core`, or `guard-common`. `ls .github/workflows/` (06-tooling.txt).
- Risk: every gate below (PD-002/004/005 + guard-common) is red on master and nobody is alerted. No Python matrix despite advertising 3.11/3.12/3.13.
- Blocks: PD-002, PD-004, PD-005 (a gate only matters once CI enforces it). **Root quick-win.**
- Direction: add a CI workflow running `just check` (lint+typecheck+test-quick+guards) on push/PR; matrix the 3 Pythons.

**PD-002 — Test suite fails on master (19 genuine failures).** `S1 · systemic · Effort M · Testability`
- Evidence: `uv run --with pytest-cov pytest` → exit 1, **19 failed** (05-pytest-cov.log). All fail **in isolation** too (05-isolation-experiment.txt) → not ordering artifacts. Spans server-wizard, MCP, design-dispatch, flows-dispatch, studio, rest-routes, docs, palm-provider tests. Includes `test_modular_apps.py::test_palm_provider_app_manifest` — a **guard-common** test → `just check` is red.
- Risk: no green baseline; refactoring is unsafe; the fitness functions the project relies on are themselves failing.
- Direction: fix/retire the 19; then wire PD-001 so it can't recur.

**PD-003 — Test doubles drift from production signatures.** `S2 · layer · Effort S · Testability`
- Evidence (verified tracebacks, 05-tests-ci.md): `_FakeRestClient.flows_session_input() got an unexpected keyword argument 'input_token'` (prod `runtimes/mcp/flows/tools.py:194` added the param); `KeyError: 'propose_dashboard'` (new design command absent from the test's `_CONCRETE_PATHS`); palm manifest 4-vs-9 actions.
- Risk: hand-maintained fakes/expected-maps silently rot as prod APIs evolve — the root pattern behind PD-002.
- Direction: derive fakes from the real interface (Protocol/ABC) or contract-test the fake against the real signature.

**PD-004 — Lint gate RED on master (~133 ruff findings).** `S3 · layer · Effort XS`
- Evidence: `uv run ruff check src/palm tests examples` → exit 1; `--statistics`: 61 I001 (unsorted), 25 F401 (`datetime.UTC` unused), 15 RUF100 (unused `noqa: BLE001`), 3 F841, … (09-conventions.txt). Mostly `--fix`-able.
- Direction: `just lint-fix` + `just format`; then enforce via PD-001.

**PD-005 — xenon gate RED + `just complexity` only scans `core/`.** `S3 · layer · Effort L`
- Evidence: `uvx xenon --max-average A --max-modules B src/palm` → exit 1, ~40 modules rank C/D/E (03-xenon.txt). The `justfile complexity` recipe runs `radon cc` on `src/palm/core/` only, so the failing modules are never surfaced locally.
- Direction: fix the worst modules (overlaps PD-014) or set an honest threshold; run radon repo-wide.

**PD-006 — `.pre-commit-config.yaml` missing.** `S3 · module · Effort S` — `just setup` runs `pre-commit install` and `pre-commit` is a dev dep, but no config file exists → nothing runs (06-tooling.txt).

**PD-007 — Audit tools referenced but undeclared.** `S3 · module · Effort S` — `justfile` `audit`/`complexity`/`security`/`refactor` call vulture/radon/xenon/bandit/pip-audit/autoflake, none declared in `pyproject.toml` → recipes fail on a fresh checkout (00-baseline.txt). Direction: add a `dev`/`audit` dependency group.

**PD-008 — No coverage threshold.** `S4 · module · Effort XS` — no `--cov-fail-under` in `pyproject`/`justfile`; coverage can silently regress.

### T2 — The composition root is a god-object

**PD-009 — `ApplicationHost` god-object.** `S1 · systemic · Effort XL · SRP(§1), no-god-classes(§6)`
- Evidence: `src/palm/app/host/application_host.py` = **1170 LOC, 89 `def`, 29 `@property`, 5 `_wire_*`, 1 class** (01, 02). **#1 churn** (38 touches / 400 commits, 10-churn.txt). 13 `except Exception` (09). Mixes lifecycle, CQRS wiring, execution (`execute`/`ask`/`submit_*`/`invoke_resource`), lazy service accessors, and 3 status methods.
- Risk: every new surface/feature accretes here; the instability magnet of the codebase.
- Depends-on: PD-012 (breaking import cycles enables clean extraction).
- Direction: extract role/subsystem objects (CQRS wiring, host-profile roles, status/observability, inbound) off the class.

**PD-010 — `cqrs_wiring` composition-root coupling.** `S2 · layer · Effort L` — `app/host/cqrs_wiring.py` churn 21, 55% cov; `ApplicationHost._wire_cqrs` is a 123-line root with many function-local imports (02, 10-hotspots.csv). Direction: declarative contributor registration instead of a hand-wired root.

**PD-011 — `inbound_service.py` mixed responsibilities.** `S3 · module · Effort L` — 725 LOC, 9 `except Exception`, polling+dispatch+http in one module (01, 09).

### T3 — Deferred imports as a layering escape valve

**PD-012 — 595 deferred imports masking circular deps.** `S2 · systemic · Effort L · Explicit-Boundaries, Minimal-Magic`
- Evidence: 595 function-local `from palm.` / `import palm.` lines (02-deferred-imports.txt); top: `mcp/in_process.py` 34, `application_host.py` 29, `app/app.py` 14, `common/__init__.py` 12. Corroborated by the ruff `patterns/wizard I001` waiver and CHANGELOG startup-cycle fixes.
- Risk: the real dependency graph is hidden; import order becomes load-bearing; refactors trip latent cycles.
- Direction: map cycles (`uvx pydeps --show-cycles`), then hoist imports by inverting a few dependencies (interfaces in `core`/`common`, side-effect registration via explicit `ready()` rather than import).

**PD-013 — Dual `server/` trees.** `S3 · layer · Effort M` — both `src/palm/common/runtimes/server/` and `src/palm/runtimes/server/` exist (two `transport/`, `ssr/`, `surface.py`, `cqrs.py`) (04-duplicate-basenames.txt), blurring the "thin surface vs shared infra" boundary. Direction: document the split crisply or consolidate.

### T4 — assist/MCP + CLI complexity & coverage sink

**PD-014 — assist/MCP + CLI complexity hotspots.** `S2 · layer · Effort L · Minimal-Magic, Testability`
- Evidence (03-complexity-summary.txt, 10-hotspots.csv): 48 blocks rank D–F; worst `shape_dispatch_result` **CC 112** (`mcp/assist/shape/result.py`, 52% cov), `map_dispatch_to_rest` 65 (`mcp/assist/rest_map.py`, 6.5% cov), `render_status_dashboard` 62 (`cli/commands/dashboard.py`), `menu_for_assist` 49 (`assist/catalog/menu.py`, 41% cov), `run_doctor` 44, `dispatch_system` 44. High complexity ∩ low coverage ∩ high churn.
- Direction: decompose the dispatch/shape/render mega-functions; add unit tests as they shrink.

**PD-015 — `mcp/in_process.py` big+cold+churned.** `S2 · module · Effort L` — 871 LOC, 35% cov, churn 20, 34 deferred imports, 6 broad excepts (01, 02, 05). The single worst-conditioned file after `application_host.py`.

**PD-016 — Large SSR explorer files.** `S3 · module · Effort M` — `ssr/explorer/components.py` 992, `forms.py` 941 (01); HTML-string builders that could be templated/split.

**PD-017 — runtimes coverage 69.6%; coldest files near-0%.** `S3 · layer · Effort L` — coldest: `mcp/assist/rest_map.py` 6.5%, `cli/tui/prompt.py` 11%, `cli/tui/completion.py` 15%, `mcp/assist/operator.py` 17%, `rest/design/handlers.py` 18% (05-coverage-by-layer.txt).

### T5 — Three observability vocabularies

**PD-018 — Overlapping status APIs + magic-string buses + live deprecated alias.** `S2 · layer · Effort M · SRP, Minimal-Magic`
- Evidence (02-architecture.txt): `event_plane_status()` (l.899), `ops_status()` (l.939), `control_plane_status()` (l.987) on `ApplicationHost`; bus identity as string literals `"host_fallback"/"runtime"/"host"/"internal"` (l.901-924); `work_drain_background` emitted as a "deprecated alias" (l.1026) alongside `work_drain_running`.
- Direction: one observability model with typed bus identities; fold the three status methods into a single report with sub-views; drop the deprecated alias on the next minor.

### T6 — Docs-as-code is unenforced

**PD-019 — Version stamps ~30 minors behind.** `S3 · layer · Effort M · Docs-as-Code(§5)` — ARCHITECTURE.md 0.13.13, STATUS.md 0.39.0, README.md 0.34.5, DEVELOPMENT.md 0.16.5, SCOPE.md 0.13.0 vs code 0.45.8 (08-docs.txt). Reuse the existing `scripts/sync_version.py` + `scripts/docs_check.py` (already wired but not gating).

**PD-020 — ADR discipline broken.** `S3 · layer · Effort M` — `docs/adr/` runs 001–012 then 014; **013 missing**; most post-0.25 features (through 0.45) have no ADR despite the "every significant decision needs an ADR" rule (08-docs.txt).

**PD-021 — Root markdown sprawl.** `S4 · layer · Effort M` — 28 `RELEASE-*.md` + 14 `MIGRATION-*.md` (50 root `.md` total) overlap the 82 KB `CHANGELOG.md` (08-docs.txt). Direction: move point-release notes under `docs/releases/`.

**PD-031 — `docs-check` gate RED on master.** `S3 · module · Effort S · Docs-as-Code, ci-tooling` *(found while opening 0.46.0)*
- Evidence: `just docs-check` → exit 1. `docs/skills/palm/SKILL.md` + 3 references (+ a `.grok/` copy) are out of sync with their `src/palm/runtimes/mcp/data/` / `.grok/skills/` mirrors — **pre-existing committed drift** (files unchanged in worktree). Separately, `just bump-version` stamps `docs/llms.txt`/`docs/mcp.txt` but does **not** propagate to their `mcp/data/` mirrors, so every bump re-breaks docs-check unless the mirrors are hand-copied. `CHANGELOG.md` is also missing all 0.45.x entries.
- Risk: another silently-red gate (cf. PD-002/004/005); `just release-prep` fails at docs-check.
- Direction: sync the skill mirrors (source of truth = `docs/skills/`); make `sync_version.py` (or a `just` recipe) copy the `mcp/data` + `.grok` mirrors as part of the bump. Fits 0.46 T1's "green the gates."

### T7 — Placeholders & untested adapters

**PD-022 — DB adapters untested.** `S2 · layer · Effort L · Testability` — `providers/postgres`, `providers/graphql`, `storages/postgres`, `storages/mongodb` have only registry-presence assertions; no behavioral round-trips (05-adapter-gaps.txt). Ties to PD-030.

**PD-023 — Placeholder features registered as installed.** `S3 · module · Effort M · Truth-Seeking` — `common/transforms/rules/parquet_load.py` raises "not implemented yet"; `providers/graphql`/`providers/postgres` docstrings say "(placeholder)"; `patterns/dag`/`patterns/etl` are single-pass scaffolds (04-placeholders.txt). *Note:* dag/etl are STATUS-documented "honest placeholders" (partially accepted); the sharper concern is advertised-but-empty providers. Direction: gate placeholders behind an explicit "experimental" flag or don't register them.

### T8 — Navigability & convention drift

**PD-024 — Broad `except Exception` swallowing.** `S3 · layer · Effort M · Truth-Seeking` — 163 occurrences; densest `application_host.py` 13, `inbound_service.py` 9, `ssr/explorer/actions.py` 7 (09-conventions.txt); several degrade-to-fallback blocks discard the error, hiding failures in exactly the observability/wiring paths. Direction: narrow exception types; log-and-reraise or record structured errors.

**PD-025 — Pervasive filename reuse.** `S4 · systemic · Effort M` — 100+ basenames reused across layers (04-duplicate-basenames.txt). **Verified NOT logic duplication:** `job_state`×2, `observability`×3, `state_snapshot`×3 are distinct-responsibility modules (e.g. `state_snapshot` = model / persistence-helper / hook across three layers) — coherent per SRP but hard to navigate. Direction: convention for disambiguating names; rely on the (legitimate, expected) `app.py`/`registry.py`/`provider.py` plugin uniformity but rename genuine ambiguities.

**PD-026 — Magic numbers + hardcoded hosts/ports.** `S4 · layer · Effort S` — 24 `limit=200/100/50` literals, 15 `127.0.0.1`/`:8080`/`localhost:8080` (09-conventions.txt). Direction: pull into settings/constants.

**PD-027 — Inconsistent leading-underscore module naming.** `S4 · layer · Effort S` — 20 `_*.py` modules (`_apps.py`, `_registry.py`, `_params.py`, `_view_meta.py`, `_dates.py`, …) while structurally similar files elsewhere are not underscored (09-conventions.txt).

### T9 — Dependency & security hygiene

**PD-028 — `pydantic-settings 2.14.1` known vuln.** `S3(security) · systemic · Effort XS` — `pip-audit`: GHSA-4xgf-cpjx-pc3j, fixed 2.14.2 (07-pip-audit.txt). It's a **runtime** dep (`pyproject` `pydantic-settings>=2.2,<3`), so shipped installs are exposed. Direction: bump floor to `>=2.14.2` and refresh `uv.lock`. **Quick-win.**

**PD-029 — `urllib.urlopen` without scheme allowlist.** `S3 · layer · Effort M` — 9 `urlopen` sites (webhook `common/events/external.py:76`, `app/host/inbound_service.py:452`, palm `events_client`/`flow/remote/client`, `providers/rest/.../http.py`, `mcp/rest_client.py`); no scheme guard found (bandit B310 Medium, 05-adapter-gaps.txt). For config/user-supplied URLs this is an SSRF / `file://`-read surface. Direction: validate `http(s)` scheme before `urlopen`.

**PD-030 — Empty extras / unpinned drivers.** `S3 · module · Effort S` — `pyproject` `postgres = []`, `mongodb = []` while those providers/storages ship — drivers are neither pinned nor installable; ties to PD-022.

---

## Prioritization view

**Quick wins (high impact / low effort) — do these first; several are the dependency roots that unblock the rest:**
- PD-001 add a CI `just check` gate · PD-028 bump `pydantic-settings` · PD-004 `just lint-fix` · PD-003 refresh drifted fakes → PD-002 green suite · PD-006/007 pre-commit + audit deps · PD-008 coverage floor · PD-019 run the existing `sync_version.py`.

**Strategic refactors (high impact / high effort) — schedule after the suite is green & CI enforces it:**
- PD-009 decompose `ApplicationHost` · PD-012 break the deferred-import cycles (unblocks PD-009) · PD-014/PD-015 tame the assist/MCP complexity+coverage sink · PD-018 unify observability · PD-022 adapter test suite · PD-013 consolidate server trees.

**Fill-ins (low/low):** PD-026, PD-027, PD-021. **Defer (low impact / high effort):** PD-025 mass rename, `archive/` migration, SSR SPA relocation.

**Dependency roots:** PD-001 → (PD-002, PD-004, PD-005); PD-012 → PD-009. Fix roots first.

---

## Roadmap — themes → minors (0.46+)

Executed **one theme per minor** per [`docs/VERSIONING.md`](docs/VERSIONING.md): each minor opens with a
`VISION-0.X.md` plan (`0.X.0`) and ships its PD items as feature patches (`0.X.1…`). This table is the **live
tracker** — flip items as they close. Order follows the dependency roots above, **not** strict T-numbers.

| Minor | Theme | Status | Notes |
|---|---|---|---|
| **0.46** | **T1 — Safety net (green suite + CI)** | 🔜 planned · [VISION-0.46](docs/VISION-0.46.md) | Dependency root; must land first. Slices PD-001/002/003/004/005/006/007/008 + PD-028 |
| next | T3 — deferred-import / cycle cleanup | queued | Precedes T2 (PD-009 depends-on PD-012) |
| next | T2 — ApplicationHost decomposition | queued | After T3 |
| next | T5 — observability unification | queued | Likely breaks API → `MIGRATION` doc |
| later | T4 — assist/MCP complexity + coverage | queued | |
| later | T7 — adapters & placeholders | queued | |
| later | T6 / T8 / T9 — docs, conventions, security hygiene | queued | Fold quick-wins (e.g. PD-028) opportunistically |

Exact minor numbers beyond 0.46 are assigned when each theme starts. Security / one-line quick-wins may land
early regardless of theme.

**Closed:** PD-028 (0.46.1 — CVE bump) · **PD-002, PD-003** (0.46.2 — full test suite green, 22→0; +2 latent prod bugs fixed: session_input 404, non-wizard inspect guard).

---

## Accepted trade-offs (logged, not defects)

Verified as deliberate; documented here so the audit doesn't re-flag them:
- **SHA1 in `common/websocket/frames.py:28`** — RFC 6455 `Sec-WebSocket-Accept` handshake (protocol-mandated, not security-sensitive). Bandit B324 false positive; optionally silence with `usedforsecurity=False`.
- **E501 line-length ignored** — deliberate ruff policy (`pyproject`); **`B008`** likewise.
- **`patterns/wizard/** I001` isort waiver** — intentional import order for circular-import safety (documented in `pyproject`).
- **`patterns/dag` & `patterns/etl` placeholders** — STATUS-documented "honest placeholders."
- **`archive/` (104 files)** — AGENTS.md §7 archive policy; import-guarded, reference-only.
- **common→patterns registry bridges (11)** — documented autoload seam; `test_common_boundary.py` accepts it. (Latent coupling-direction risk; watch, don't fix.)
- **Hand-rolled stdlib HTTP/WS server & client** — deliberate zero-web-framework philosophy. Not debt per se; its costs surface as PD-029 (scheme hardening) and part of PD-014/PD-024.
- **`repomix-output.xml` (5.4 MB) & `.coverage` on disk** — **untracked/gitignored**; local hygiene only, *not* repo debt (verified via `git ls-files`).

---

## Methodology & reproducibility

Pinned to `8413d0e`. Missing tools run via `uvx` / `uv run --with` (never installed into the project). Full raw
outputs in [`docs/audit/`](docs/audit/). Guard scripts are authoritative and override heuristic tools.

| Step | Command | Artifact |
|------|---------|----------|
| 0 Baseline | `git rev-parse HEAD`; `uv run python --version`; tool `--version` probes | `00-baseline.txt` |
| 1 Inventory | `find src/palm -name '*.py' -exec wc -l {} + \| sort -rn` | `01-inventory.txt` |
| 2 Architecture | `python scripts/guard_core.py`; `just guard-common`; deferred-import grep; boundary greps; method census | `02-*.txt` |
| 3 Complexity | `uvx radon cc src/palm -s -a`; `uvx radon mi`; `uvx xenon --max-average A --max-modules B src/palm` | `03-*.txt` |
| 4 Dead/dupe | `uvx vulture src/palm --min-confidence 80`; `uvx autoflake --check`; placeholder & basename greps | `04-*.txt` |
| 5 Tests/cov | `uv run --with pytest-cov pytest --cov=src/palm --cov-report=json`; isolation experiment | `05-*.{md,txt,json}` |
| 6 CI/tooling | inspect `.github/workflows/`, pre-commit, coverage-gate, pyproject | `06-tooling.txt` |
| 7 Deps/sec | `uv run --with pip-audit pip-audit`; `uvx bandit -r src/palm -ll -ii` | `07-*.txt` |
| 8 Docs | `scripts/docs_check.py`; version-stamp & ADR greps | `08-docs.txt` |
| 9 Conventions | `ruff check --statistics`; magic-value & cruft greps | `09-*.txt` |
| 10 Hotspots | churn × LOC × max-CC × coverage join | `10-hotspots.csv`, `10-churn.txt` |
| 11 Scorecard | synthesize 2–10 vs AGENTS.md §1 | `11-principle-scorecard.md` |

Verification gate applied to every `confirmed` item: one automated signal **plus** a live re-derived `path:line`;
plugin dynamic-dispatch false-positives excluded (vulture vs `INSTALLED_*`); guard scripts trump heuristics
(guard-core PASS → no core-purity item filed); deliberate trade-offs moved to the section above.

---

## Non-goals

- **No refactor design or implementation, and no edits to `src/`.** This document catalogs debt and suggests
  directions only; the fixes are a separate, later effort.
- Audit tools are run ephemerally, not added to project deps as part of the analysis (though "add them + a CI
  gate" is itself a register item — PD-001/PD-007).
