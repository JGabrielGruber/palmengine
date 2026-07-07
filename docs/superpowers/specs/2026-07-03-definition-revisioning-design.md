# Definition Revisioning & Migration Design

**Status:** Approved (July 3, 2026)  
**Version target:** 0.24 vision · **Implementation:** 0.24.1 (revisions) · 0.24.2 (migration rules) · 0.24.3 (execution hooks)  
**Builds on:** [0.16 services API](../../VISION-0.16.md) · [0.23 mutation guard](../../../MIGRATION-0.23.md)  
**Vision:** [docs/VISION-0.24.md](../../VISION-0.24.md)  
**Blocks:** [Design Service (0.25)](2026-07-03-design-service-design.md)

---

## Problem

[`DefinitionRepository`](../../../src/palm/common/persistence/definition_repository.py) treats each flow as a single mutable record. [`ProcessInstance`](../../../src/palm/instances/process_instance.py) snapshots `flow_definition` at submit ([`flow_submission.py`](../../../src/palm/common/executions/flow_submission.py)), so running sessions survive catalog overwrites — but operators cannot:

- List or restore prior revisions
- Pin instances to a known revision explicitly
- Upgrade live instances to a newer revision safely
- Report which instances lag behind `latest`

[`FlowDefinition.to_dict()`](../../../src/palm/definitions/flow.py) includes `"version": 1` — this is **serialization format**, renamed in specs to `format_version` during implementation to avoid confusion with semantic `revision`.

---

## Goal

1. **Append-only flow revisions** in `DefinitionRepository`
2. **`flow_revision` pin** on `ProcessInstance` (+ retain snapshot for resume integrity)
3. **`DefinitionMigrationRule`** registry in `palm/common/transforms/rules/`
4. **Impact query v0** — instances affected by a revision bump
5. **Migration metadata** on instance persistence hooks (0.24.3)

Core purity unchanged. No new engines in `palm/core/`.

---

## Principle

```
Read (latest or specific revision)
    ↓
definitions service
    ↓
DefinitionRepository  flow:{id}:rev:{n}  +  flow:{id}:latest → n
    ↓
Submit flow
    ↓
ProcessInstance { flow_id, flow_revision, flow_definition snapshot }
    ↓
Publish new revision (0.24.1) or migrate instance (0.24.2+)
```

**Design Service (0.25)** sits above publish + migrate; not in 0.24 implementation.

---

## Revision model

### Identifiers

| Field | Meaning |
|-------|---------|
| `flow_id` | Stable identity — existing `FlowDefinition.definition_id` |
| `revision` | Monotonic integer per `flow_id`, starting at `1` |
| `format_version` | Serialization schema version (today's `version: 1` field, renamed in impl) |
| `content_hash` | Optional SHA-256 of canonical `to_dict()` for dedup / audit (0.24.1 nice-to-have) |

### Repository layout

Storage keys under existing prefix `palm:definitions`:

```
palm:definitions:flow:{flow_id}:rev:{revision}   → FlowDefinition record
palm:definitions:flow:{flow_id}:latest           → int (revision number)
palm:definitions:flow:{flow_id}:revs             → list[int] (revision index, optional cache)
```

In-memory cache mirrors the same structure. `register_flow` becomes **`publish_flow_revision`** (append); existing `save_flow` paths delegate to publish in 0.24.1.

### Resolution rules

| Operation | Behavior |
|-----------|----------|
| `get_flow(flow_id)` | Resolve `latest` revision |
| `get_flow(flow_id, revision=3)` | Load explicit revision |
| `list_flow_revisions(flow_id)` | Return `[{revision, published_at, content_hash?}]` |
| `publish_flow_revision(body)` | Parse body → assign `revision = latest + 1` → persist → update `latest` |

### Backward compatibility

| Case | Behavior |
|------|----------|
| Existing storage records (no `:rev:` keys) | On first read, treat as `revision=1`, migrate key layout lazily or via `palm doctor` migration command |
| Existing instances (`flow_revision` absent) | `null` → implicit revision from snapshot; impact query uses snapshot diff vs latest |
| `DefinitionService.update_flow` | 0.24.1 impl: delegates to `publish_flow_revision` (breaking semantics change — document in `MIGRATION-0.24.md` at 0.24.1 ship) |

### Process and resource revisions

Spec now; implement after flows prove stable:

- `process:{id}:rev:{n}` — same pattern
- `resource:{id}:rev:{n}` — same pattern

0.24.1 scope: **flows only**.

---

## Instance model

### `ProcessInstance` additions

```python
flow_revision: int | None = None  # explicit pin; None = legacy implicit
```

Rules:

1. **On submit:** set `flow_revision` to resolved revision at submit time; keep `flow_definition` snapshot as today
2. **On resume:** prefer pinned snapshot; do not auto-upgrade to catalog `latest`
3. **On migration success:** bump `flow_revision`, update snapshot, record `migration_status: succeeded` in metadata

### Job metadata

[`flow_submission.py`](../../../src/palm/common/executions/flow_submission.py) copies `flow_definition` into job metadata. Also copy `flow_revision` for inspect views.

---

## DefinitionService API (0.24.1 implementation)

Existing methods gain revision awareness:

| Method | 0.24.1 change |
|--------|---------------|
| `get_flow(flow_id, *, revision=None)` | Optional `revision` param |
| `list_flows()` | Each row includes `latest_revision` |
| `create_flow(body)` | Publishes `revision=1` |
| `update_flow(flow_id, body)` | Publishes `revision=latest+1` (no overwrite) |
| `publish_flow_revision(flow_id, body)` | **New** — explicit publish |
| `list_flow_revisions(flow_id)` | **New** |

REST/MCP: optional `?revision=` on get; new routes spec'd for 0.24.1 impl plan.

---

## Migration primitives (0.24.2)

### `DefinitionMigrationRule`

Location: `palm/common/transforms/rules/definition_migration.py` (new)

```python
@dataclass(frozen=True)
class MigrationContext:
    flow_id: str
    from_revision: int
    to_revision: int
    instance_id: str
    state: dict[str, Any]  # blackboard snapshot

class DefinitionMigrationRule(BaseTransformRule):
    flow_id: str
    from_revision: int
    to_revision: int

    def can_migrate(self, ctx: MigrationContext) -> tuple[bool, list[str]]: ...
    def migrate_state(self, ctx: MigrationContext) -> dict[str, Any]: ...
```

Register via existing `register_transform()` or dedicated `register_migration_rule()` if transform namespace is too narrow — **prefer transform registry** for consistency with [`palm/common/transforms/`](../../../src/palm/common/transforms/).

### Compatibility classes

| Flag | Meaning |
|------|---------|
| `compatible` | Migration rule exists and `can_migrate` passes |
| `snapshot_only` | No rule; instance stays on old snapshot |
| `blocked` | Rule exists but `can_migrate` fails — list blockers |

### Impact query v0

**Query:** `AnalyzeDefinitionImpactQuery(flow_id, target_revision?)`

**Response:**

```json
{
  "flow_id": "onboard",
  "latest_revision": 4,
  "target_revision": 4,
  "instances": [
    {
      "instance_id": "inst-abc",
      "current_revision": 3,
      "compatible": true,
      "blockers": []
    }
  ],
  "summary": { "total": 12, "behind_latest": 5, "blocked": 1 }
}
```

Implementation: scan `InstanceIndexProjection` for matching `flow_id`; compare `flow_revision` or snapshot hash.

Service home: `DefinitionService.analyze_impact()` or `SystemService` — **prefer definitions domain** (catalog concern).

---

## Migration execution (0.24.3)

### Instance metadata

Extend [`InstancePersistenceHook`](../../../src/palm/common/hooks/instance_persistence.py) metadata:

```json
{
  "migration_status": "pending|running|succeeded|failed",
  "migration_target_revision": 4,
  "migration_from_revision": 3,
  "migration_blockers": []
}
```

### Execution path

1. Operator or future Design Service requests migration for `instance_id` → `target_revision`
2. Load rule for `(flow_id, from_revision, to_revision)`
3. Run `migrate_state` on blackboard snapshot
4. On success: update instance `flow_revision` + snapshot; clear migration metadata
5. On failure: set `migration_status: failed`; optional [`CompensationCoordinator`](../../../src/palm/common/compensation/) rollback if multi-step migration flow used

### Example migration flow (catalog definition)

Wizard pattern flow `palm-migrate-instance`:

1. Confirm target revision + show impact summary
2. Dry-run migration rule
3. Apply state transform
4. Summary + commit

Spec only in 0.24 vision; ship example in `examples/definitions/` at 0.24.3.

---

## CQRS (0.24.1+ implementation)

| Command / Query | Owner |
|-----------------|-------|
| `PublishFlowRevisionCommand` | `palm/services/definitions/bindings/cqrs/` (new bindings package or extend parsers) |
| `ListFlowRevisionsQuery` | definitions |
| `AnalyzeDefinitionImpactQuery` | definitions (0.24.2) |
| `RequestInstanceMigrationCommand` | definitions or execution/flows (0.24.3 — TBD in plan) |

Schemas register via `CqrsSchemaRegistry` contributor on definitions domain.

---

## Testing strategy

| Area | Tests |
|------|-------|
| Repository | `test_definition_repository_revisions.py` — publish, get latest, get by revision, list |
| Instance pin | `test_flow_submission_revision.py` — submit sets `flow_revision` |
| Migration rule | `test_definition_migration_rule.py` — can_migrate, migrate_state |
| Impact | `test_definition_impact_query.py` — behind_latest counts |
| Backward compat | Legacy instance without `flow_revision` still resumes |

---

## Explicit non-goals (0.24)

- Design Service (`palm/services/design/`)
- Governance approval workflows
- Blockchain / immutable external audit
- Automatic background migration of all instances on publish
- Explorer revision UI

---

## References

- Vision: [VISION-0.24.md](../../VISION-0.24.md)
- ADR: [007-definition-revisioning.md](../../adr/007-definition-revisioning.md)
- Plan: [definition-revisioning.md](../plans/2026-07-03-definition-revisioning.md)
- Deferred: [design-service-design.md](2026-07-03-design-service-design.md)