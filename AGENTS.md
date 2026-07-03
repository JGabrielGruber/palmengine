# AGENTS.md

**Palm Engine Constitution**  
For AI coding agents and human developers  

*“Palm grows where the sun meets the sea.”*  
Orchestration should feel alive, truthful, and humane. Structure must serve clarity and longevity, never become a cage.

**Last updated:** July 2026 (0.23.0 shipped)

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
User / CLI / REST / MCP
        ↓
palm/runtimes/             ← Thin adapters per service domain (map transport → services)
        ↓
palm/app/                  ← ApplicationHost (primary orchestrator)
        ↓
palm/services/             ← User-facing API (definitions, execution, system, assist)
        ↓
palm/common/               ← CQRS buses, schemas, hooks, persistence, service primitives
        ↓
palm/core/                 ← PURE foundational engines (Behavior Tree, Orchestration,
                            Context, Storage, Resource, Event, Auth, Transform)
```

> **0.16** domain API lives in `palm/services/`; `palm/common/services/` retains `BaseService`, `errors`, `views` only. Vision: [docs/VISION-0.16.md](docs/VISION-0.16.md).

**Key layers and their roles:**

- **`palm/core/`** — Pure engines and primitives. Behavior Trees are the universal control-flow model. No external Palm imports allowed.
- **`palm/services/`** — User-facing business API (`DefinitionService`, `ExecutionService`, `SystemService`) composing schema-validated CQRS. Domain modules own `registry.py`. Runtimes call services; services do not import runtimes. Shared `BaseService` / views remain in `palm/common/services/`.
- **`palm/common/`** — The “middle layer” where most coordination lives. Execution plans, hooks, CQRS + `CqrsSchemaRegistry`, reliable events (outbox), compensation, transforms, and shared runtime infrastructure.
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

### Operating Palm via MCP (0.14 + 0.15 in-process)

Coding agents should use the MCP operator adapter to develop and test flows — not hand-written curl or JSON blobs.

| Step | Action |
|------|--------|
| Read first | [docs/MCP.md](docs/MCP.md) · `palm://agent/guide` ([docs/mcp.txt](docs/mcp.txt)) · `palm://agent/skill` ([docs/skills/palm](docs/skills/palm)) · project context [docs/llms.txt](docs/llms.txt) |
| Setup (local) | `uv sync --extra mcp` → connect `palm-mcp` stdio with `PALM_MCP_IN_PROCESS=1` (default in [`.grok/config.toml`](.grok/config.toml)) — **no REST server required** |
| Setup (remote) | `PALM_MCP_IN_PROCESS=0` → `just palm-server` (`:8080`) → `palm-mcp` proxies via `PALM_BASE_URL` |
| Grok (this repo) | [`.grok/config.toml`](.grok/config.toml) — `uv run --extra mcp palm-mcp`, in-process + `docs/mcp.txt` · skill [`docs/skills/palm/SKILL.md`](docs/skills/palm/SKILL.md) (mirrored in `.grok/skills/palm/`) |
| Operator loop | definitions → submit → inspect → input → wait on children → resume |

**Conventions:** session-first (`session_id` / `instance_id` in views, not `job_id`); plain `input` strings (`yes`, choice slugs, text); **0.20+** assistant default on assist (`question`, `choices`, `hint`, `actions`) · powertool default on `palm_flows_*` / flows dispatch (`operator_hint`); **0.21.5+** flows opt-in `format=assistant` on `palm_flows_session` and flows REST `?format=`; **0.21.7+** bare `palm_assist()` → operator-entry; `params.session_id` + `value`/`input` inferred for continuation; **0.21.10+** flows driving via `palm_assist(params={session_id, flow_id, value})` or aliases `flows/session-input` / `flows/session`; **0.21.11+** collection `params.edit={item_index, …}` and fuzzy menu tokens (`add`/`edit`/`done`/`continue`); resources for read, tools for write; **0.19+** stable proxy → `palm_assist(path=…)` or `alias=…` with `format=assistant|powertool` (catalog: `palm://assist/routes`); per-domain tools remain valid; collection menu → `palm_wizard_collection_action` or `palm_assist` collection params; interactive entry → `palm_assist` / `assist start` (CLI) / `/explorer/assist` (browser) / `palm_flows_create_session` (not `palm_processes_submit` on entry-flow processes); `resume-child-wait` only when `waiting_for_child`.

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
| CQRS schemas | `palm/patterns/<name>/bindings/cqrs/schemas.py` | Add `command_schemas` / `query_schemas` on `CqrsContributor`; optional `instance_status_query` for inspect |
| Service method | `palm/services/<domain>/` | Compose CQRS in domain `service.py`; register REST/MCP in domain `registry.py`; wire on host/context in `_wire_cqrs()` |
| MCP tool (0.16+) | `palm/runtimes/mcp/<domain>/` | Group tools by service domain (`flows`, `providers`, `definitions`, `system`); pattern contributors stay in pattern `bindings/mcp.py` |
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
- `docs/mcp.txt` should be maintained as the MCP operator guide (served as `palm://agent/guide` via `PALM_LLMS_TXT`).
- `docs/llms.txt` should be maintained as broader project context for AI agents.
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
