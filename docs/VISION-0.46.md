# VISION 0.46 — The Safety Net (Testability & CI)

**Theme:** TECH-DEBT **T1** — "No CI, and a red master."
**Why first:** this is the dependency root of the whole debt program. Right now the suite fails on `master`
(19 tests), `ruff`/`xenon`/`guard-common` are red, and nothing runs in CI to catch it. **No structural refactor
(ApplicationHost, imports, observability) is safe until the tests pass and CI enforces them.** 0.46 builds the
net; later minors do the trapeze work.

See [TECH-DEBT.md](../TECH-DEBT.md) (theme T1, items PD-001…008 + PD-028) and
[docs/VERSIONING.md](VERSIONING.md) for how this minor is structured.

## Goal / exit criteria

- `just check` is **green locally *and* in CI** on every push/PR.
- A coverage floor and an honest complexity gate are active (no silent regression).
- All T1 register items closed; `guard-common` and `guard-core` both green again.

## Slices (patches)

Ordered smallest-risk / highest-leverage first, so the net closes progressively.

| Patch | Slice | Closes | Notes |
|-------|-------|--------|-------|
| `0.46.0` ✅ | **Plan** — this VISION + `docs/VERSIONING.md` + AGENTS.md rules | — | the planning release |
| `0.46.1` ✅ | Bump `pydantic-settings ≥ 2.14.2`, refresh `uv.lock` | PD-028 | one-line security quick-win |
| `0.46.2` ✅ | **Green the suite** — fixed all **22** failures (not 19 — a fuller env ran more) + 2 real prod bugs | PD-002, PD-003 | prerequisite for CI |
| `0.46.3` ✅ | **Lint green** — `ruff check` passes (~130 fixes) | PD-004 | *reordered before CI* so the gate turns on green |
| `0.46.4` ✅ | **CI gate** — sovereign hermetic `just ci` / `just ci-sandbox` (NeonRoot); pre-commit; audit deps; mypy report-only | PD-001, PD-006, PD-007 | ADR-016 — *NeonRoot, not GitHub Actions*: local/offline/hermetic |
| `0.46.5` | Coverage floor (`--cov-fail-under`) | PD-008 | pick a threshold at/just below current 80.2% |

> **Plan vs actual:** lint (0.46.3) and CI (0.46.4) were swapped from the original plan so the gate turns on
> already-green; CI is a **NeonRoot sovereign sandbox** (git-seeded, hermetic) rather than cloud GitHub Actions,
> with **mypy report-only** (its 379 errors are the T2 `ApplicationHost` typing debt). xenon/complexity moved
> out of 0.46 into the T4 theme.

## Out of scope (later themes)

Structural refactors — `ApplicationHost` decomposition (T2), deferred-import/cycle cleanup (T3), observability
unification (T5), assist/MCP complexity (T4), adapter tests (T7). These land on the green baseline 0.46 creates.

## Decisions to capture as ADRs

- **ADR-016** ✅ — CI quality gate: sovereign hermetic checks via NeonRoot (`just ci-sandbox`), mypy report-only. Landed with `0.46.4`.
- Any change to the fitness-function contract (e.g. how test doubles are contract-checked) → ADR.

## Definition of done

`just check` green in CI · coverage + complexity gates active · T1 PD items flipped to done in `TECH-DEBT.md` ·
`STATUS.md` reflects 0.46 · `CHANGELOG.md` updated per patch.
