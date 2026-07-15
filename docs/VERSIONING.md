# Palm — Versioning & Release Convention

**Status:** canonical (established 0.46.0). Applies to all future work.

Palm had a *de-facto* cadence (0.45.1 → 0.45.8, one feature per patch) but no written rule. This document is
that rule. It is referenced by `AGENTS.md` §5 and enforced by `AGENTS.md` §6.

## Scheme: `0.MINOR.PATCH` (pre-1.0)

Palm is pre-1.0, so the SemVer `MAJOR` slot stays `0` and stability guarantees are relaxed:

- **MINOR (`0.X`) = a theme.** One coherent arc of work — a capability, or a consolidation/debt goal. A minor
  **may** introduce breaking changes; when it does it ships a `MIGRATION-0.X.md`.
- **PATCH (`0.X.N`) = one shippable slice** within the theme — a single feature or tracked work-item (e.g. a
  `TECH-DEBT.md` `PD-NNN`). One focused change per patch.

> **Release cadence — embedded release.** Each slice is its own *commit*, but the **version is not bumped per
> commit** (every bump restamps 6+ doc surfaces — needless churn). We cut an **embedded release** — the
> `just bump-version` + `CHANGELOG` + doc-sync — per **minor or per patch-group**, grouping several slice-commits
> under one released version. Small steps in git; releases in batches. This is the organic palm flow.

> At **1.0** we switch to strict SemVer (MAJOR = breaking, MINOR = additive, PATCH = fix).

## The `X.0` planning release

`0.X.0` **opens** a minor. It carries the *plan*, not features:

- Adds `docs/VISION-0.X.md` — the theme's goal, scope, and the ordered list of patches it will ship.
- Adds/updates ADR(s) in `docs/adr/` for the structural decisions the theme will make.
- Execution starts at `0.X.1`.

**Rhythm per theme:** `0.X.0` plan → `0.X.1 … 0.X.N` execute (one slice each) → close the theme, open `0.(X+1).0`.

## Artifacts by level

**Per minor (`0.X`)**
- `docs/VISION-0.X.md` — **required** (the plan)
- `MIGRATION-0.X.md` — **required iff** the theme breaks API/contracts
- ADR(s) for significant structural decisions
- `STATUS.md` updated; `CHANGELOG.md` section

**Per slice-commit**
- Commit `feat(0.X): <summary>` (or `fix(0.X):` / `refactor(0.X):`) — one focused change; cite the tracked item (e.g. "closes PD-004"). **No version bump.**
- **Green `just check`** / `just ci` (lint + test + guards) — enforced in CI.

**Per embedded release (a minor or a patch-group)**
- `just bump-version 0.X.N` — once, covering the grouped slice-commits (version + doc-surface sync).
- `CHANGELOG.md` entry summarizing the group; `STATUS.md` updated.

## Version sources of truth & bump flow

Two files hold the version, kept in lockstep by `scripts/version_utils.py`:
- `pyproject.toml` `[project].version`
- `src/palm/__init__.py` `__version__`

Bump with (**at an embedded-release point — a minor or patch-group — not per commit**):

```
just bump-version 0.X.N        # → scripts/sync_version.py --set
```

This propagates the stamp to the **auto-synced** surfaces: `README.md`, `STATUS.md`, `docs/llms.txt`,
`docs/mcp.txt`, `docs/DOCKER.md`, `docs/index.html`. Verify with `just sync-version --check` and `just docs-check`.

> ⚠️ **Not auto-synced today:** `ARCHITECTURE.md`, `DEVELOPMENT.md`, `SCOPE.md`. They are stamped by hand and
> have drifted (TECH-DEBT `PD-019`). Update them manually on relevant changes, or extend `SYNC_TARGETS` in
> `scripts/sync_version.py`.

## Publishing

Publishing to PyPI is at maintainer discretion — not every patch must publish, and `X.0` planning releases are
typically not published. Release gate: `just release-prep` (docs-check + full-check + build). See
`DEVELOPMENT.md` → "Release & publishing".

## Current program — the debt-paydown line (0.46+)

The technical-debt register (`TECH-DEBT.md`) is executed **one theme per minor**. `0.46` opens the line with the
dependency root (T1 — the safety net). Subsequent themes are sequenced by the register's dependency roots (see
`TECH-DEBT.md` → Roadmap), **not** by strict T-number — e.g. import-cycle cleanup precedes the ApplicationHost
split. Security / one-line quick-wins may land early regardless of theme.
