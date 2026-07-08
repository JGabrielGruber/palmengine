# Vision 0.28 — Local Document Resources

**Theme:** Dumb edge resource providers for flow-owned data — key-value and file documents — so compositional wizards can read/write local state without REST URLs or database drivers.

**Status:** Planned (post **0.27**)  
**Depends on:** [0.27 Compositional Design Parity](VISION-0.27.md) ✅ · [0.12 Compositional Power](VISION-0.12.md)  
**Design:** [document-kv-providers-design.md](superpowers/specs/2026-07-08-document-kv-providers-design.md)  
**Plan:** [document-kv-providers-0.28.md](superpowers/plans/2026-07-08-document-kv-providers-0.28.md)  
**Reference flow:** `coconut-npc` cross-session player profile

---

## Why 0.28

**0.27** made resources agent-safe to design, invoke, and debug. Dogfooding still hits a wall when flows need **local, structured persistence**:

| Symptom | Root cause |
|---------|------------|
| Design-time flows need placeholder data stores | Only `rest` / `palm` / stub DB providers exist |
| Coconut NPC has no memory across visits | Wizard answers live in instance state only |
| Authors reach for REST or custom code for JSON blobs | No first-class **document** or **KV** resource provider |
| Dev vs prod persistence differs | No `auto` backend that prefers filesystem, falls back to memory |

**StorageEngine** (platform: instances, definitions, snapshots) and **ResourceEngine** (flow steps) stay separate. 0.28 adds **resource providers** that are thin adapters over document/KV storage — not new platform storage backends.

---

## Goal

| Shift | From (0.27) | To (0.28) |
|-------|-------------|-----------|
| Local flow data | Ad-hoc or REST | **`kv` and `file` resource providers** |
| Design-time prototyping | External services or skips | **In-memory KV** works out of the box |
| Durable local data | Manual file I/O | **`file` provider** + `auto` backend on filesystem storage |
| Reference branching flow | Stateless coconut | **Cross-session player profile** keyed by `player_name` |

**Non-goals for 0.28:**

- SQLite/SQL query provider (defer 0.29+)
- Replacing `StorageEngine` or `DefinitionRepository`
- Full document DB (indexes, queries, transactions beyond single-key CRUD)
- Game/NPC product features beyond coconut as regression profile

---

## What ships (target)

### 0.28.0 — `kv` resource provider

- Provider `kv` with actions: `get`, `put`, `delete`, `list` (prefix scan).
- `resource_id` = logical key (supports `{{ state.* }}` binding).
- Param `backend`: `auto` | `memory` | `storage` (default `auto`).
- **`auto`:** filesystem storage active → delegate to `StorageEngine` under `palm:resources:kv:{namespace}:`; else in-memory dict.
- Runtime binding hook (like `palm` provider) for storage access.
- Design contributor + `palm_design_propose_resource` validation.

### 0.28.1 — `file` document provider

- Provider `file` with actions: `read`, `write`, `delete`, `exists`, `list`.
- Documents under configurable `documents_root` (default aligned with filesystem storage `data_dir`).
- JSON and plain-text payloads; atomic writes (reuse filesystem storage patterns).
- Doctor preflight: writable root, path safety.

### 0.28.2 — Coconut cross-session persistence

- Resource definitions: `load-coconut-player`, `save-coconut-player` (`kv`, namespace `coconut`).
- Flow steps: load after `player_name`; save after `reputation` and at `farewell`.
- Persisted profile: `reputation`, `visit_count`, `coconuts_owned`, `last_topic`, timestamps.
- Returning player with same `player_name` sees merged state (e.g. visit count, prior reputation).
- Regression tests + MCP dogfood note in branching playbook.

### 0.28.3 — Operator ergonomics

- Doctor `resource_preflight` extension for `kv`/`file` backends.
- MCP tool descriptions + `palm://agent/references/design-flows` resource loop for local providers.
- `examples/README.md` cross-link.

---

## Locked decisions

| # | Decision |
|---|----------|
| 1 | **Two providers** — `kv` (structured blobs) and `file` (path-shaped documents); not one overloaded provider |
| 2 | **`auto` default** — truth-seeking durable path when filesystem storage is active; memory otherwise |
| 3 | **Cross-session coconut** — keyed by `player_name`, not instance id |
| 4 | **Core purity** — providers in `palm/providers/`; storage delegation via runtime binding in `palm/common/` |
| 5 | **Dumb KV** — no SQL, no server; list-by-prefix only |
| 6 | **Design parity** — resources proposed via Design Service like 0.27.2 |

---

## Success criteria

- [ ] `palm_providers_invoke(resource_ref="load-coconut-player", …)` works in-process without `base_url`.
- [ ] `palm flow start coconut-npc` twice with same name restores `visit_count` / reputation.
- [ ] `palm_system_doctor` reports `kv` backend mode (`memory` vs `storage`).
- [ ] `palm_design_propose_resource` accepts `kv` and `file` proposals.
- [ ] `just guard-common` · targeted pytest · no core imports from providers.

---

## Related

- [PROVIDER-APPS.md](PROVIDER-APPS.md)
- [VISION-0.27.md](VISION-0.27.md) · coconut reference flow
- [ADR-001 Compositional Power](adr/001-compositional-power-resources.md)