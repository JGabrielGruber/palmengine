# Principle scorecard — palm graded against its own AGENTS.md §1 (SHA 8413d0e)

Each of the 8 "non-negotiable" principles, scored 🟢 healthy / 🟡 eroding / 🔴 breached, with the
audit artifact backing it. This is the rhetorical spine of the executive summary.

| # | Principle | Score | Evidence (artifact) |
|---|-----------|:---:|---------------------|
| 1 | **Single Responsibility** | 🔴 | `ApplicationHost` 1170 LOC / 89 methods / 29 `@property` (02); 48 blocks rank D–F, ~40 modules fail the project's own xenon gate (03). |
| 2 | **Explicit Boundaries** | 🟡 | Layer arrows mostly hold (0 services→runtimes, 0 patterns→up) BUT 595 deferred imports as escape valve, 11 common→patterns registry bridges, dual `server/` trees (02). |
| 3 | **Core Purity** | 🟢 | `guard_core.py` PASS; `core/` 92.8% covered (02-guard-core, 05). |
| 4 | **Registry-Based Extension** | 🟢 | Uniform `_apps.py` / `INSTALLED_*` plugin model; providers/patterns/storages self-register (04, 02). Note: import-side-effect registration is what forces much of #2's deferred-import pressure. |
| 5 | **Documentation as Code** | 🔴 | ARCHITECTURE.md 0.13.13, STATUS.md 0.39.0, README 0.34.5 vs code 0.45.8; ADR 013 missing, series stops at 014 (08). The project's own rule: "doc debt == bug." |
| 6 | **Testability First** | 🔴 | Suite RED on master — 19 genuine failures incl a guard-common fitness test; no test CI; DB adapters untested; runtimes 69.6% cov (05). |
| 7 | **Human-First + Truth-Seeking** | 🟡 | Product is built for it (assist/wizard/compensation/observability) but observability itself is fragmented (3 status vocabularies) and 163 broad `except Exception` (13 in ApplicationHost) swallow errors (02, 09). |
| 8 | **Minimal Magic** | 🟡 | Explicit registries are good, but 595 deferred imports, magic-string bus IDs, and 29 `Any`-typed lazy service slots undercut it (02, 09). |

**Tally:** 🔴×3 (SRP, Docs-as-Code, Testability) · 🟡×3 (Boundaries, Truth-Seeking, Minimal-Magic) · 🟢×2 (Core Purity, Registry Extension).

**Reading:** the *foundation* the constitution most cares about (core purity, registry extension) is intact —
the erosion is at the **seams that grew fastest under the feature-per-patch cadence**: the composition root
(ApplicationHost), the assist/MCP surface, and the enforcement layer (tests, CI, docs) that was supposed to
keep the rest honest. Every 🔴 maps to register theme T1/T2/T6.
