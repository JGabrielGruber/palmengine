# ADR-016: CI Quality Gate — sovereign hermetic checks via NeonRoot (0.46)

## Status

**Accepted** — July 2026 (0.46.4, TECH-DEBT theme T1)

## Context

The audit found **PD-001**: the only workflow was `publish.yml`, so nothing ran tests/lint/typecheck on
change. As a result the suite, ruff, xenon, and a guard test all went red on `master` undetected
(fixed in 0.46.2/0.46.3). We need a gate that keeps them green.

Two forces shaped the choice:
- **Sovereignty.** The maintainer runs [NeonRoot](../../ci/Containerfile) — a local, offline-first
  disposable-workspace/sandbox tool — precisely to avoid cloud dependence. A cloud CI runner would cut
  against that.
- **Cleanliness.** Running checks against the working tree re-uses stale git-ignored state (the
  `data/` filesystem-storage dir, `.venv`, caches). We actually hit this: `--seed .` failed on a
  permission-denied file left in `data/` by a container-run server.

`just check`'s components: tests ✅ and guards ✅ are green; ruff ✅ (0.46.3); **mypy --strict is 379
errors** — overwhelmingly the `ApplicationHost` `Any`-typed service slots and missing annotations, i.e.
the T2 complexity debt (PD-009). Blocking CI on mypy would block on the refactor.

## Decision

1. **Gate via a NeonRoot sandbox, not cloud.** `just ci-sandbox` seeds a throwaway `palm-ci` container
   from **`git archive HEAD`** (git-tracked files only — no stale `data/`/`.venv`) and runs `just ci`
   inside it (`neonroot spawn --sandbox`). Hermetic, local, offline, reproducible.
2. **Image as tracked source.** [`ci/Containerfile`](../../ci/Containerfile) (Arch + git + just + uv;
   `UV_PYTHON=3.12`) is committed; the built image + vault live in a git-ignored `.neonroot/`.
   Build/refresh with `just ci-image`.
3. **`just ci` = the gate:** ruff check + `guard_core.py` + the **full** suite (`pytest -q` with
   `--extra cli --extra mcp --group dev`, matching the green baseline incl. MCP tests) — all blocking —
   **plus `mypy` report-only** (non-blocking) until the T2 typing debt is paid.
4. **Fast local gate:** [`.pre-commit-config.yaml`](../../.pre-commit-config.yaml) runs ruff check/format
   + core-purity guard on staged files at commit time (PD-006), using the project's pinned tools via
   `uv run` (no version drift).
5. **Provision the audit toolchain:** a `[dependency-groups] audit` group pins
   vulture/radon/xenon/bandit/pip-audit/autoflake so `just audit`/`complexity`/`refactor` run on a fresh
   checkout (PD-007).

## Consequences

- The green suite + lint are now enforceable hermetically without cloud CI; drift is caught locally.
- mypy is visible (report-only) but does not block — it will go blocking once the T2 refactor shrinks
  the 379 errors (tracked as PD-005 direction + the T2 theme).
- The gate requires podman + NeonRoot locally (the maintainer's setup); it is not a hosted PR check.
  If a hosted/mirror gate is later wanted, the same `just ci` runs unchanged under any runner.
- `ruff format` (a 335-file whole-repo reformat) is intentionally **not** part of the gate yet — only
  `ruff check`; pre-commit formats incrementally as files are touched.

## References

- [TECH-DEBT.md](../../TECH-DEBT.md) — PD-001/005/006/007, theme T1
- [docs/VISION-0.46.md](../VISION-0.46.md) — the T1 safety-net plan
- `ci/Containerfile`, `.pre-commit-config.yaml`, `justfile` (`ci`, `ci-image`, `ci-sandbox`)
- NeonRoot — `~/Projects/neonroot` (the maintainer's sovereign workspace/sandbox tool)
