# AGENTS.md

**Palm Engine Constitution**  
For AI coding agents and human developers  

*“Palm grows where the sun meets the sea.”*  
Orchestration should feel alive, truthful, and humane. Structure must serve clarity and longevity, never become a cage.

**Last updated:** June 2026 (0.14 MCP + 0.13 architecture)

---

## 1. Enduring Principles

These principles are non-negotiable. They exist so that Palm can evolve for a decade without descending into complexity debt.

| Principle | Meaning | Why it enables longevity |
|---------|--------|--------------------------|
| **Single Responsibility** | One reason to change per module, class, or function | Prevents god objects and tangled growth |
| **Explicit Boundaries** | Clear contracts between layers. Prefer composition and registries over inheritance and implicit magic | Makes the system understandable at any scale |
| **Core Purity** | `palm/core/` must never import from any other Palm package | The foundation stays stable and testable forever |
| **Registry-Based Extension** | New capabilities are added by registering at the edges, never by modifying core contracts | Evolutionary architecture without core erosion |
| **Documentation as Code** | Documentation, ADRs, and architectural summaries are maintained with the same rigor as source code | Prevents knowledge rot as the project grows |
| **Testability First** | Core logic and critical paths must be unit-testable in isolation | Enables confident refactoring and long-term maintenance |
| **Human-First + Truth-Seeking** | Interactive flows, backtracking, compensation, and observability are first-class concerns | The engine serves people, not the other way around |
| **Minimal Magic** | Prefer readable, explicit code over clever dynamic behavior | Reduces cognitive load and surprises over time |

---

## 2. Current Architecture Snapshot (0.10+)

Palm follows a **layered, registry-driven** architecture with a pure core.

```
User / CLI / Services
        ↓
palm/app/                  ← ApplicationHost (primary orchestrator)
        ↓
palm/common/               ← Shared coordination (executions, plans, hooks, cqrs,
                            compensation, transforms, runtimes base, persistence)
        ↓
palm/core/                 ← PURE foundational engines (Behavior Tree, Orchestration,
                            Context, Storage, Resource, Event, Auth, Transform)
```

**Key layers and their roles:**

- **`palm/core/`** — Pure engines and primitives. Behavior Trees are the universal control-flow model. No external Palm imports allowed.
- **`palm/common/`** — The “middle layer” where most coordination lives. This is where execution plans, hooks, CQRS, reliable events (outbox), compensation, transforms, and shared runtime infrastructure reside.
- **`palm/app/`** — Application-level orchestration. `ApplicationHost` (with composable `HostProfile` roles) is the recommended entry point for most use cases. `PalmApp` is infrastructure.
- **`palm/patterns/`, `palm/providers/`, `palm/storages/`** — Extensible “Django-style apps”. Each capability lives in its own subpackage with `registry.py`.
- **`palm/runtimes/`** — Thin surfaces (CLI, embedded, daemon, server). Heavy lifting lives in `palm.common.runtimes`.
- **`palm/definitions/` + `palm/instances/`** — Stable contracts and durable state.

**Core invariants that must never be broken:**
- `palm/core/` imports nothing from outside itself.
- All extension happens through registries (never by editing core files).
- Registries use `threading.RLock` and are populated at bootstrap time.
- Job state transitions happen only through `RunResult` + `OrchestrationEngine.apply_result()`.
- Persistence and resume are first-class (via `InstancePersistenceHook` and state snapshots).

### Operating Palm via MCP (0.14)

Coding agents should use the MCP operator adapter to develop and test flows — not hand-written curl or JSON blobs.

| Step | Action |
|------|--------|
| Read first | [docs/MCP.md](docs/MCP.md) and MCP resource `palm://agent/guide` ([docs/llms.txt](docs/llms.txt)) |
| Setup | `uv sync --extra mcp` → `just palm-server` (REST on `:8080`) → connect `palm-mcp` stdio |
| Grok (this repo) | [`.grok/config.toml`](.grok/config.toml) — `uv run --extra mcp palm-mcp` |
| Operator loop | definitions → submit → inspect → input → wait on children → resume |

**Conventions:** instance-first (`instance_id`, not `job_id`); plain `input` strings (`yes`, choice slugs, text); compact inspect by default; resources for read, tools for write; `palm_wizard_collection_action` on collection steps; `palm_resume_child_wait` when `waiting_for_child`.

**Extending MCP** (when adding tools, not just using them): pattern contributors via `register_mcp_contributor()` in `PatternApp.ready()`; app contributors via `register_app_mcp_contributor()` in `palm/app/mcp_registry.py`; adapter code in `palm/runtimes/mcp/` (operator logic belongs in `palm/common/operator/`).

---

## 3. Core Purity Rules (Strict)

Nothing inside `src/palm/core/` may import from:
- `palm.app`, `palm.common`, `palm.patterns`, `palm.providers`, `palm.storages`, `palm.runtimes`, `palm.definitions`, `palm.instances`, or `palm.utils`

Violation of this rule is considered a serious architectural defect.

---

## 4. How to Add or Extend Palm

Follow these patterns. They exist so growth remains orderly.

| What you want to add | Where it goes | How |
|----------------------|---------------|-----|
| New pattern (wizard, parallel, dag, etc.) | `palm/patterns/<name>/` | `pattern.py` + `app.py` (PatternApp) + `registry.py` + `bindings/definitions/builder.py`. Add to `INSTALLED_PATTERNS` in `patterns/_apps.py`. See [docs/PATTERN-APPS.md](docs/PATTERN-APPS.md) |
| New provider (REST, GraphQL, Postgres, etc.) | `palm/providers/<name>/` | `provider.py` + `app.py` (ProviderApp) + `registry.py` + `bindings/` + `flow/` as needed. Add to `INSTALLED_PROVIDERS`. See [docs/PROVIDER-APPS.md](docs/PROVIDER-APPS.md) |
| New storage backend | `palm/storages/<name>/` | Same structure. Add to `INSTALLED_STORAGES` (use optional extras when drivers are needed) |
| New transform rule | `palm/common/transforms/rules/` | Implement `BaseTransformRule`, register with `register_transform()` or `@transform_rule` |
| CQRS command or query | Pattern-owned: `palm/patterns/<name>/bindings/cqrs/` | Register via `register_cqrs_contributor()` in `PatternApp.ready()`. Generic buses live in `palm/common/cqrs/` |
| New host role / capability | `palm/app/host/` | Extend `HostProfile` or add to `ApplicationHost` wiring |
| Compensation handler | During definition bootstrap | Register on `default_compensation_registry()` |
| New runtime surface | `palm/runtimes/<name>/` | Keep thin. Put logic in `palm.common.runtimes` |
| MCP tool, resource, or prompt | `palm/runtimes/mcp/` + pattern or app `app.py` | Pattern: `register_mcp_contributor()`. App: `register_app_mcp_contributor()`. See [docs/MCP.md](docs/MCP.md) |
| Cross-cutting coordination | `palm/common/<area>/` | executions, plans, hooks, persistence, etc. |
| Application-level orchestration | `palm/app/` | Prefer `ApplicationHost` over direct `PalmApp` usage |

**Never:**
- Add new logic directly into core engines
- Create new top-level packages without strong justification
- Put pattern-specific logic in `palm/common/`

---

## 5. Documentation & Knowledge Discipline (Critical for Longevity)

Documentation is not optional. It is part of the system.

- Every significant architectural decision **must** have an ADR (Architecture Decision Record) in `.github/ISSUE_TEMPLATE/adr.md` or a dedicated `docs/adr/` folder.
- Major changes to public API, layer responsibilities, or reliability primitives **must** update:
  - `README.md`
  - `ARCHITECTURE.md`
  - `DEVELOPMENT.md`
  - `AGENTS.md` (this file)
  - `MIGRATION-*.md` when breaking changes occur
- A living `STATUS.md` (or `docs/STATUS.md`) must exist and be kept reasonably current. It is the single source of truth for the current state of the project.
- `docs/llms.txt` should be maintained as high-quality context for AI agents (served as `palm://agent/guide`).
- `docs/MCP.md` is the canonical guide for agent development with Palm MCP (setup, workflows, tool inventory).
- When updating the website (`docs/index.html`), structured data (JSON-LD) and feature highlights must reflect current capabilities.

**Rule:** If the code and the documentation diverge, the documentation debt must be treated as seriously as a bug.

---

## 6. Review Checklist (Before Merge)

- [ ] Core purity preserved (`palm/core/` has no external Palm imports)
- [ ] SRP respected — no god classes or mixed responsibilities
- [ ] Extension done via registries (not by modifying core contracts)
- [ ] Thread-safety respected for all registries
- [ ] Tests added/updated (unit + integration where appropriate)
- [ ] Documentation updated (README, ARCHITECTURE, ADRs, STATUS.md, etc.)
- [ ] No imports from `archive/`
- [ ] Public API surface is explicit (`__all__` where relevant)
- [ ] Backward compatibility or clear deprecation path considered
- [ ] `palm doctor` and example flows still work (when relevant)
- [ ] `just guard-common` passes (no pattern-specific logic in `palm.common`)

---

## 7. Archive Policy

Everything under `archive/` is historical reference only.  
**New code must never import from `archive/`.**

When a component is truly deprecated and removed from active use, it may eventually move to `archive/`, but only after a proper migration path and deprecation period.

---

## 8. Spirit of the Project

Palm should remain:
- **Simple at the core**, powerful at the edges
- **Human-first** — wizards, backtracking, compensation, and observability are not afterthoughts
- **Truth-seeking** — explicit state, durable instances, and honest error handling
- **Evolutionary** — registries and hooks allow major new capabilities without rewriting the foundation
- **Reference-quality** — clean boundaries, excellent documentation, and high testability so others can learn from it

We optimize for **long-term clarity and maintainability** over short-term cleverness.

---

## 9. How to Update This Constitution

This document is living. When the architecture evolves significantly (new major layer, fundamental shift in extension model, new reliability primitive, etc.), update this file through a pull request accompanied by an ADR when appropriate.

The goal is not rigidity, but **intentional, documented evolution**.
