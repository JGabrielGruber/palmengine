# Local Document & KV Resource Providers — 0.28 Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development or executing-plans for phased delivery. Checkboxes track progress.

**Goal:** Add `kv` and `file` resource providers with `auto` backend (filesystem storage → durable keys, else memory), then wire coconut-npc cross-session persistence keyed by `player_name`.

**Architecture:** Two ProviderApps (`kv`, `file`) at the edge; shared document storage adapters in `palm/common/resource/`; runtime binding for StorageEngine access; coconut example as regression profile.

**Tech Stack:** Python 3.12+, existing ResourceEngine/StorageEngine, ProviderApp pattern from `rest`/`palm`.

**Vision:** [docs/VISION-0.28.md](../../VISION-0.28.md)  
**Design:** [docs/superpowers/specs/2026-07-08-document-kv-providers-design.md](../specs/2026-07-08-document-kv-providers-design.md)

**Depends on:** 0.27 shipped (design propose_resource, resource preflight, coconut-npc example)

---

## Locked decisions

| # | Decision |
|---|----------|
| 1 | Cross-session coconut keyed by `player_name` |
| 2 | `kv` ships before `file`; coconut uses `kv` only in 0.28.2 |
| 3 | `backend: auto` default on kv resources |
| 4 | Storage keys: `palm:resources:kv:{namespace}:{logical_key}` |
| 5 | `get` missing key returns success with `{found: false}` not failure |

---

## Phase 0.28.0 — `kv` provider

### Task 1: Shared document storage adapter

**Files:**
- Create: `src/palm/common/resource/document_storage.py`
- Test: `tests/test_document_storage.py`

- [ ] `MemoryKvStore` — thread-safe get/set/delete/list_prefix
- [ ] `StorageKvBackend` — wraps `StorageEngine` with key prefix helper
- [ ] `resolve_kv_backend(name: str, storage, backend_name)` — implements `auto|memory|storage`
- [ ] Unit tests for each backend + auto resolution

### Task 2: KvProvider app

**Files:**
- Create: `src/palm/providers/kv/` (provider.py, app.py, registry.py, bindings/resource/{descriptor,invoke}.py, flow/params.py)
- Modify: `src/palm/providers/_apps.py` — add `"kv"` to `INSTALLED_PROVIDERS`
- Test: `tests/test_kv_provider.py`

- [ ] `KvProvider` extends `BaseProvider` with `invoke()` dispatching get/put/delete/list
- [ ] `KvInvokeParams` dataclass: namespace, backend, default, value, prefix
- [ ] `describe()` lists four actions with param hints
- [ ] `register_runtime_binding` in `ready()` wires storage from host runtime
- [ ] Tests: memory round-trip, storage round-trip, list prefix, `{{ state }}` binding via ResourceEngine

### Task 3: Resource definitions helper

**Files:**
- Create: `examples/definitions/coconut_resources.py`
- Modify: `examples/README.md` — mention local kv resources

- [ ] `load-coconut-player`, `save-coconut-player` definitions
- [ ] `register_definitions()` hook

**Verification:**

```bash
uv run pytest tests/test_document_storage.py tests/test_kv_provider.py -q
```

---

## Phase 0.28.1 — `file` document provider

### Task 4: FileDocumentStore

**Files:**
- Modify: `src/palm/common/resource/document_storage.py`
- Test: `tests/test_document_storage.py` (extend)

- [ ] `FileDocumentStore` — read/write/delete/exists/list under `documents_root`
- [ ] Reuse path safety from `FilesystemStorageBackend` patterns
- [ ] Atomic write via temp file + rename
- [ ] Tests: json round-trip, traversal blocked, list glob

### Task 5: FileProvider app

**Files:**
- Create: `src/palm/providers/file/`
- Modify: `src/palm/providers/_apps.py` — add `"file"`
- Test: `tests/test_file_provider.py`

- [ ] Actions: read, write, delete, exists, list
- [ ] Default `documents_root` from settings `data_dir / documents`
- [ ] Runtime binding for data_dir resolution
- [ ] Integration test with EmbeddedRuntime + resource_ref

**Verification:**

```bash
uv run pytest tests/test_file_provider.py tests/test_document_storage.py -q
```

---

## Phase 0.28.2 — Coconut cross-session persistence

### Task 6: Wire coconut flow

**Files:**
- Modify: `examples/definitions/coconut_npc.py`
- Create: `tests/test_coconut_npc_persistence.py`

- [ ] After `player_name`: resource step `load-coconut-player` → `player_profile`
- [ ] Transform `hydrate_profile`: merge defaults, increment `visit_count`, surface `is_returning`
- [ ] Transform `sync_profile`: copy `reputation`, `coconuts_owned`, `last_topic` into `player_profile`
- [ ] Resource save after `reputation` (or mood_line) and at `farewell`
- [ ] Optional prompt tweak when `visit_count > 1`
- [ ] Test: two `flow start` with same name → `visit_count == 2`, reputation persisted

### Task 7: MCP dogfood smoke

- [ ] Manual: `palm_flows_create_session(coconut-npc)` → complete once → restart → same name sees returning copy
- [ ] Document in `docs/skills/palm/references/branching-flows.md` (persistence section)

**Verification:**

```bash
uv run pytest tests/test_coconut_npc_persistence.py tests/test_coconut_npc_flow.py -q
palm flow start coconut-npc  # manual twice with same name
```

---

## Phase 0.28.3 — Design + doctor + docs

### Task 8: Design contributors

**Files:**
- Create: `src/palm/providers/kv/bindings/design.py`
- Create: `src/palm/providers/file/bindings/design.py`
- Test: `tests/test_design_kv_file_contributor.py`

- [ ] Validate action ∈ allowed set, backend enum, namespace slug safety
- [ ] `palm_design_propose_resource` accepts kv/file proposals

### Task 9: Doctor preflight extension

**Files:**
- Modify: `src/palm/common/resource/preflight.py`
- Modify: `src/palm/common/runtimes/server/diagnostics.py`
- Test: extend `tests/test_resource_operator_ergonomics_0273.py` or new file

- [ ] Report `kv_backend_resolved`, `file_documents_root`, `file_writable`
- [ ] Issue when file resources exist but root not writable

### Task 10: Docs + release

**Files:**
- Create: `docs/adr/011-local-document-resources.md`
- Modify: `CHANGELOG.md`, `STATUS.md`, `AGENTS.md` (provider table), `docs/PROVIDER-APPS.md`

- [ ] ADR accepted
- [ ] STATUS 0.28 phase table
- [ ] Commit: `feat(0.28.0): kv resource provider` (per phase)

**Verification:**

```bash
just guard-common
just docs-check
uv run pytest tests/test_kv_provider.py tests/test_file_provider.py tests/test_coconut_npc_persistence.py -q
```

---

## File map

| Path | 0.28 role |
|------|-----------|
| `src/palm/common/resource/document_storage.py` | Memory + storage + file adapters |
| `src/palm/providers/kv/` | KV resource provider |
| `src/palm/providers/file/` | File document provider |
| `examples/definitions/coconut_resources.py` | load/save resource defs |
| `examples/definitions/coconut_npc.py` | Cross-session wiring |
| `docs/VISION-0.28.md` | Release vision |
| `docs/adr/011-local-document-resources.md` | Architecture decision |

---

## Risk notes

- **Binding `value` from state** — `put` may need `bind_resource_params` for `value: "{{ state.player_profile }}"`; verify ResourceEngine merges dict values correctly before implementation.
- **Concurrent writes** — single-key last-write-wins; document in ADR.
- **Example autoload order** — `coconut_resources.py` must register before flow references resources; use separate module imported from `coconut_npc.py` `register_definitions`.