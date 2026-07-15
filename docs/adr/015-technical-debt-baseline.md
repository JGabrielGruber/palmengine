# ADR-015: Technical-Debt Baseline & Audit Methodology (0.45)

## Status

**Accepted** — July 2026

(Note: this ADR also closes a numbering gap — the `docs/adr/` series jumped 012 → 014; 013 was never
written. See PD-020 in [TECH-DEBT.md](../../TECH-DEBT.md).)

## Context

The 0.45.x line ships **one feature per patch** (0.45.1 → 0.45.8). That cadence is great for momentum but has
let debt accumulate at a few seams faster than it is paid down, and — because the only CI workflow is
`publish.yml` — the project's own quality gates went red on `master` **without anyone being alerted**:

- `pytest` — **19 genuine failures** (tests & fakes lagged production API changes).
- `ruff check` — RED (~133 findings).
- `xenon` — RED (~40 modules over the project's own complexity threshold).
- `guard-common` — RED (a stale fitness test).
- Only `guard-core` is GREEN (core purity holds).

We need a **repeatable, evidence-backed baseline** of where Palm stands relative to its own constitution
(`AGENTS.md` §1), so refactor work can be prioritized against data rather than intuition — and so drift can be
re-measured each release.

## Decision

1. **Run a comprehensive technical-debt audit** pinned to a commit SHA, weighted toward architecture/coupling,
   tests/coverage/CI, and dead-code/hygiene (docs/conventions/security cataloged at lower priority).
2. **Publish a living register** at repo-root [`TECH-DEBT.md`](../../TECH-DEBT.md) — a scannable master table
   (`PD-NNN`, severity, reach, effort, priority) + per-item detail + themes + a prioritization quadrant.
3. **Grade the code against `AGENTS.md` §1** via a Green/Yellow/Red principle scorecard; every 🔴/🟡 must map to
   register items.
4. **Keep raw metrics reproducible** under [`docs/audit/`](../audit/) (`00`–`11`), each entry storing the exact
   command that produced it. Audit tools (radon/xenon/vulture/bandit/pip-audit) run via `uvx`/`uv run --with`,
   **not** added to project dependencies.
5. **Verification gate:** an item is `confirmed` only with one automated signal **plus** a live re-derived
   `path:line`. Guard scripts trump heuristics (guard-core PASS → no core-purity item). Deliberate trade-offs
   (SHA1 WS handshake, E501 policy, wizard isort waiver, dag/etl placeholders, `archive/`) are logged as
   *accepted*, not defects.
6. **This ADR does not authorize any refactor.** Fixes are a separate effort, sequenced from the register's
   dependency roots (CI + green suite first, then the strategic decompositions).

## Consequences

- There is now a single, prioritized source of truth for debt; new debt should be appended as `PD-NNN` and old
  items closed as fixed.
- The audit is re-runnable on any future SHA (`docs/audit/` commands), so debt can be tracked per release.
- The most valuable near-term action falls out of the data: **wire CI to run `just check`** (PD-001) so the
  gates that are silently red can never regress unnoticed again — the dependency root for most other work.
- Adopting the register implies a light ongoing cost: keeping `TECH-DEBT.md` current, and (recommended) adding
  the audit tool group to `pyproject` so `just audit` runs on a fresh checkout.

## References

- [TECH-DEBT.md](../../TECH-DEBT.md) — the register and methodology appendix
- [`docs/audit/`](../audit/) — raw metric artifacts (`00`–`11`), pinned to `8413d0e`
- `AGENTS.md` §1 (Enduring Principles), §5 (Documentation Discipline), §6 (Review Checklist)
- `scripts/guard_core.py`, `just guard-common`, `scripts/docs_check.py` — existing fitness functions leveraged
