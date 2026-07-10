# ADR-011: Local Document & KV Resource Providers (0.28)

## Status

**Accepted** — July 2026 (Palm 0.28.0–0.28.3 shipped incrementally)

## Context

Palm 0.27 shipped compositional design parity and `propose_resource`, but local flow data still required REST `base_url`, ad-hoc transforms, or ephemeral instance state. The **`coconut-npc`** reference flow needed cross-session memory keyed by `player_name` without standing up HTTP or Postgres.

Resource providers already adapt external systems through `ResourceEngine` ([ADR-001](001-compositional-power-resources.md), [ADR-003](003-provider-apps.md)). Platform `StorageEngine` remains separate from resource steps — instances, definitions, and snapshots are not the same as flow-authored document data.

## Decision

1. **Two providers, one shared adapter layer**
   - **`kv`** — key-oriented `get` / `put` / `delete` / `list` (prefix scan) for JSON-compatible blobs.
   - **`file`** — path-oriented `read` / `write` / `delete` / `exists` / `list` for documents under `documents_root` (0.28.1 provider app).
   - Shared helpers in `palm/common/resource/document_storage.py` (`MemoryKvStore`, `StorageKvBackend`, `resolve_kv_backend`).

2. **`backend: auto` on `kv`** — When the host uses durable filesystem storage, `auto` resolves to `storage` and persists under `palm:resources:kv:{namespace}:{logical_key}` (slashes in logical keys normalize to `:`). Otherwise `auto` resolves to in-memory storage for the process.

3. **Runtime binding at the edge** — `KvProvider` receives `StorageEngine` via `register_runtime_binding()` in provider `ready()`. Core and `palm.common` never import `palm.providers`.

4. **Cross-session coconut (0.28.2)** — `load-coconut-player` / `save-coconut-player` resource definitions use `kv`, namespace `coconut`, keys `players/{{ state.player_name }}`.

5. **Design + doctor parity (0.28.3)**
   - Provider design contributors validate `kv`/`file` proposals (`action`, `backend`, namespace slug, path safety).
   - `palm_system_doctor` `resource_preflight` reports `kv.backend_resolved`, `kv.namespaces`, `file.documents_root`, `file.writable`; issues when file resources exist but the root is not writable.

6. **Tiered hot/cold KV (0.29.0)**
   - `backend: tiered` — bounded hot `MemoryKvStore`, write-through cold tier.
   - Cold storage uses durable `StorageEngine` when the host storage backend is durable; otherwise JSON spill under `data_dir/palm/kv-cold/`.
   - `hot_max_keys` (default 500) controls LRU eviction from hot; cold retains all keys.
   - Promote-on-read reloads cold keys into hot.

7. **Semantics**
   - `get` on a missing key returns success with `{found: false}` (not a failure).
   - Single-key last-write-wins; no transactions across keys.
   - `file` paths must be relative; traversal (`..`, absolute paths) rejected at validate and invoke time.

## Alternatives considered

| Alternative | Why not chosen |
|-------------|----------------|
| Single `document` provider with `backend` param | Blurs key vs path mental models; weaker design validation |
| Expose `StorageEngine` directly in resource steps | Breaks ResourceEngine / provider boundary |
| REST shim for local JSON files | Requires `base_url`; poor operator ergonomics for examples |

## Consequences

- Authors persist wizard state across sessions without external services.
- `palm_design_propose_resource` accepts `kv` proposals today; `file` validation ships before the `file` ProviderApp (0.28.1).
- Doctor surfaces local backend mode for operators and MCP agents.
- Tests: `test_kv_provider.py`, `test_coconut_npc_persistence.py`, `test_design_kv_file_contributor.py`, extended doctor preflight tests.

## References

- [VISION-0.28.md](../VISION-0.28.md)
- [document-kv-providers-design.md](../superpowers/specs/2026-07-08-document-kv-providers-design.md)
- `examples/definitions/coconut/resources.py`
- `src/palm/common/resource/document_storage.py`