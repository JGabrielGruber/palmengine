# Design: Document & KV Resource Providers (0.28)

**Date:** 2026-07-08  
**Status:** Proposed  
**Vision:** [VISION-0.28.md](../../VISION-0.28.md)

---

## Problem

Flows and wizards need local read/write resources during design and runtime. Today authors must use `rest` (needs `base_url`), embed logic in transforms, or rely on instance state that does not survive a new `flow start`.

Coconut NPC (`coconut-npc`) demonstrates branching but cannot remember a returning traveler. We want **cross-session persistence keyed by `player_name`** without standing up HTTP or Postgres.

---

## Requirements

### Functional

1. **`kv` provider** — get/put/delete/list JSON-compatible values by string key.
2. **`file` provider** — read/write/delete/exists/list documents by relative path.
3. **`backend: auto`** on `kv` — use `StorageEngine` when host uses durable filesystem storage; else in-memory.
4. **Param binding** — `resource_id` and params support `{{ state.key }}` (existing ResourceEngine behavior).
5. **Coconut** — load player profile after name entry; save on reputation change and farewell.
6. **Design Service** — validate and propose `kv`/`file` resource definitions.

### Non-functional

- Path traversal safe for `file` provider (same rules as `FilesystemStorageBackend`).
- Thread-safe in-memory KV per provider instance (RLock).
- Atomic file writes for `file` provider.
- No imports from `palm.providers` into `palm/core/`.

---

## Approaches considered

### A. Single `document` provider with `backend` param (rejected)

One provider, `backend: memory|file|storage`. Simpler catalog but blurs key-value vs path semantics and makes design validation ambiguous.

### B. Two providers + shared storage adapter (recommended)

- `kv` — key-oriented; `list` uses prefix.
- `file` — path-oriented; `list` uses directory glob.
- Shared `palm/providers/_shared/document_storage.py` (or `palm/common/resource/document_storage.py`) for memory dict + storage key mapping + filesystem document I/O.

**Why:** Matches author mental models; REST stays HTTP-shaped; KV stays Redis-shaped.

### C. Extend StorageEngine with public resource API (rejected)

Expose StorageEngine directly in resource steps. Violates layer boundaries — resources should go through ResourceEngine + providers.

---

## Architecture

```
ResourceDefinition (provider: kv | file)
        ↓
ResourceEngine.invoke()
        ↓
KvProvider / FileProvider  (palm/providers/)
        ↓
DocumentStorageAdapter     (palm/common/resource/ or provider bindings)
        ├─ MemoryKvStore     (process-local)
        ├─ StorageKvBackend  (StorageEngine keys palm:resources:kv:…)
        └─ FileDocumentStore (documents_root/*.json)
```

### Runtime binding

Register via `register_runtime_binding()` in provider `ready()`:

```python
def bind_kv_runtime(runtime: BaseRuntime) -> None:
    KvProvider.set_storage(runtime.storage, backend_name=runtime.storage.backend_name)
```

`auto` resolution:

| Host storage `backend_name` | `auto` resolves to |
|----------------------------|-------------------|
| `filesystem` | `storage` |
| `memory` or tests | `memory` |
| other durable backends | `storage` (same key namespace) |

Explicit `params.backend` always wins over `auto`.

### KV key layout

```
resource_id: "players/{{ state.player_name }}"
params.namespace: "coconut"   # default "default"

Storage key: palm:resources:kv:coconut:players:<name>
Memory key:  coconut:players:<name>
```

### File document layout

```
resource_id: "coconut/players/{{ state.player_name }}.json"
params.documents_root: null  # → settings data_dir / "documents"

Path: <data_dir>/documents/coconut/players/alice.json
```

---

## Provider contracts

### `kv` actions

| Action | Params | Result `data` |
|--------|--------|---------------|
| `get` | `namespace?`, `backend?`, `default?` | `{found, value}` |
| `put` | `namespace?`, `backend?`, `value` or bound state | `{key, written}` |
| `delete` | `namespace?`, `backend?` | `{key, deleted}` |
| `list` | `namespace?`, `prefix?`, `backend?` | `{keys: [...]}` |

`value` for `put` may come from `params.value` or wizard `output_key` merge pattern in resource step.

### `file` actions

| Action | Params | Result `data` |
|--------|--------|---------------|
| `read` | `documents_root?`, `format?: json\|text` | `{content, path}` |
| `write` | `documents_root?`, `content` or `value` | `{path, bytes}` |
| `delete` | `documents_root?` | `{path, deleted}` |
| `exists` | `documents_root?` | `{path, exists}` |
| `list` | `documents_root?`, `glob?` | `{paths: [...]}` |

---

## Coconut NPC integration

### New definitions (`examples/definitions/coconut_resources.py`)

```python
LOAD_COCONUT_PLAYER = ResourceDefinition(
    name="load-coconut-player",
    provider="kv",
    action="get",
    resource_id="players/{{ state.player_name }}",
    params={"namespace": "coconut", "backend": "auto", "default": {}},
    output_key="player_profile",
)

SAVE_COCONUT_PLAYER = ResourceDefinition(
    name="save-coconut-player",
    provider="kv",
    action="put",
    resource_id="players/{{ state.player_name }}",
    params={
        "namespace": "coconut",
        "backend": "auto",
        "value": "{{ state.player_profile }}",
    },
)
```

### Flow changes (`coconut_npc.py`)

1. After `player_name` — resource step `load-coconut-player` → `player_profile` dict.
2. Transform `merge_profile` — seed `reputation` from profile if present; increment `visit_count`.
3. After `mood_line` (or `reputation`) — transform updates `player_profile` blob; resource step `save-coconut-player`.
4. At `farewell` — final save with `last_topic`, `coconuts_owned`.

### UX copy

Returning player (visit_count > 1): adjust `build_greeting` or add conditional prompt via transform lookup on `visit_count`.

---

## Design Service

Extend provider design contributors:

- `palm/providers/kv/bindings/design.py` — validate actions, namespace, backend enum.
- `palm/providers/file/bindings/design.py` — validate path segments, no `..`.

`impact_scan` for resource proposals unchanged (flows referencing `resource_ref`).

---

## Doctor preflight (0.28.3)

Extend `build_resource_preflight()`:

```json
{
  "kv_backend": "auto→storage",
  "file_documents_root": "/path/to/data/documents",
  "file_writable": true
}
```

Issues when `file` resources registered but root not writable.

---

## Error handling

| Error | Remediation hint |
|-------|------------------|
| Key not found on `get` | Return `{found: false, value: default}` — not a failure |
| Path escapes root | Fail with clear path safety message |
| Storage not open | `auto` falls back to memory with metadata warning, or fail if `backend=storage` explicit |

---

## Testing strategy

| Layer | Tests |
|-------|-------|
| KV memory | get/put/delete/list unit tests |
| KV storage | integration with `FilesystemStorageBackend` |
| KV auto | memory host vs filesystem host |
| File provider | read/write round-trip, traversal rejection |
| Coconut | two flow starts, same `player_name`, `visit_count == 2` |
| Design | propose_resource valid for kv/file |
| MCP | invoke load/save in-process |

---

## File map (implementation)

| Path | Role |
|------|------|
| `src/palm/providers/kv/` | KvProvider app |
| `src/palm/providers/file/` | FileProvider app |
| `src/palm/common/resource/document_storage.py` | Shared adapters |
| `examples/definitions/coconut_resources.py` | Resource defs |
| `examples/definitions/coconut_npc.py` | Flow wiring |
| `tests/test_kv_provider.py` | Provider unit tests |
| `tests/test_coconut_npc_persistence.py` | Cross-session regression |
| `docs/adr/011-local-document-resources.md` | ADR (at implementation) |

---

## Open questions (deferred)

- **SQLite provider** — 0.29+ if tabular queries needed.
- **Per-tenant namespaces from auth** — use `namespace: "{{ state.tenant_id }}"` manually for now.
- **Compaction / TTL** — out of scope; operators delete keys explicitly.