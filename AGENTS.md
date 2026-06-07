# AGENTS.md

Constitution for AI coding agents and human developers working on Palm.

## Core Principles

- **Single Responsibility Principle (SRP)**: One reason to change per class, module, and function.
- **Separation of Concerns**: Strict boundaries between core engines, concrete implementations, definitions, and runtimes.
- **Open/Closed Principle**: Extend via registries and new modules; avoid modifying core contracts.
- **Testability**: Core logic must be unit-testable without side effects.
- **Explicit over Implicit**: Readable, self-documenting code over clever shortcuts.

## Architecture Rules (0.6.0)

### 1. Core Layer (`src/palm/core/`) — PURE

- **Invariant:** Nothing inside `src/palm/core/` may import from outside `palm/core/`.
- Contains abstract bases, registries, shared primitives, and engine skeletons:
  - `behavior_tree/` — patterns and blackboard execution
  - `resource/` — provider coordination
  - `storage/` — backend coordination
  - `orchestration/` — job lifecycle
  - `context/` — scoped execution metadata
  - `event/` — observability bus
  - `auth/` — authentication primitives
- Shared modules: `base.py`, `exceptions.py`, `registry.py`

### 2. Layers (outside core)

| Package | Role |
|---------|------|
| `palm/common/` | Shared coordination — plans, submission, hooks, persistence, pattern builder |
| `palm/patterns/` | **Extensible** — wizard, DAG, ETL (register via `pattern_registry`) |
| `palm/providers/` | **Extensible** — REST, GraphQL, Postgres providers |
| `palm/storages/` | **Extensible** — memory, Postgres, MongoDB, filesystem backends |
| `palm/definitions/` | Flow and process definition models |
| `palm/instances/` | Durable process instance snapshots |
| `palm/runtimes/` | Embedded, CLI, server, daemon surfaces |
| `palm/executions/` | Backward-compat re-exports of `palm.common` (prefer `common` for new code) |
| `palm/utils/` | Cross-cutting helpers (core must not import utils) |

### 3. Archive (`archive/`)

- All pre-0.4.0 code (legacy CLI, old core engines, old tests, wizards).
- **Never import from `archive/` in new code.**

### 4. Folder Discipline

- One primary class per file in core engines.
- Register concretes at module import time in patterns/providers/storages.

## Forbidden Patterns

- Core importing from patterns, providers, storages, runtimes, or CLI.
- Monolithic god classes.
- `eval()` or overly dynamic magic in core.
- New features in `archive/`.

## When Adding Features

- New pattern → `palm/patterns/<name>.py` + register in `pattern_registry`
- New provider → `palm/providers/<name>.py` + register in `provider_registry`
- New storage → `palm/storages/<name>.py` + register in `storage_registry`
- Shared submission / plan / hook logic → `palm/common/<area>/` (not `patterns/`)
- New engine capability → extend the relevant `palm/core/<engine>/` module only
- Always add tests under `tests/`

## Review Checklist

- [ ] Core purity preserved (no external imports in `palm/core/`)
- [ ] SRP respected
- [ ] Registrations wired on import
- [ ] Tests included
- [ ] Docs updated if structure or entry points change
- [ ] No imports from `archive/`

---

Last updated: June 2026 (0.6.0)