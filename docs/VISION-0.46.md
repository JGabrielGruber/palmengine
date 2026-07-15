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
| `0.46.0` | **Plan** — this VISION + `docs/VERSIONING.md` + AGENTS.md rules | — | the planning release |
| `0.46.1` | Bump `pydantic-settings ≥ 2.14.2`, refresh `uv.lock` | PD-028 | one-line security quick-win, ship immediately |
| `0.46.2` | **Green the suite** — fix/retire the 19 failing tests; make fakes contract-match prod signatures | PD-002, PD-003 | prerequisite for CI to go green |
| `0.46.3` | **Wire CI** — GitHub Actions runs `just check` on push/PR; matrix 3.11/3.12/3.13 | PD-001 | the core deliverable |
| `0.46.4` | Lint/format green + `.pre-commit-config.yaml` + audit-tool dependency group | PD-004, PD-006, PD-007 | `just lint-fix`; declare vulture/radon/xenon/bandit/pip-audit |
| `0.46.5` | Coverage floor (`--cov-fail-under`) + honest xenon gate / repo-wide complexity | PD-008, PD-005 | pick a threshold at/just below current 80.2% |

## Out of scope (later themes)

Structural refactors — `ApplicationHost` decomposition (T2), deferred-import/cycle cleanup (T3), observability
unification (T5), assist/MCP complexity (T4), adapter tests (T7). These land on the green baseline 0.46 creates.

## Decisions to capture as ADRs

- **ADR-016** — CI quality gate (what `just check` runs, the Python matrix, PR-blocking policy). Lands with `0.46.3`.
- Any change to the fitness-function contract (e.g. how test doubles are contract-checked) → ADR.

## Definition of done

`just check` green in CI · coverage + complexity gates active · T1 PD items flipped to done in `TECH-DEBT.md` ·
`STATUS.md` reflects 0.46 · `CHANGELOG.md` updated per patch.
