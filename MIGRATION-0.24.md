# Migration guide — 0.24 (definition revisioning & migration)

**Releases:** 0.24.1 (revisions) · 0.24.2 (rules + impact) · 0.24.3 (execution) · 0.24.4 (docs cleanup)  
**Prior:** [MIGRATION-0.23.md](MIGRATION-0.23.md)  
**Vision:** [docs/VISION-0.24.md](docs/VISION-0.24.md) · **ADR:** [docs/adr/007-definition-revisioning.md](docs/adr/007-definition-revisioning.md)

---

## Summary

0.24 introduces **append-only flow revisions**, **instance revision pins**, **migration rules**, an **impact query**, and **instance migration execution**. Transport paths stay under `/v1/api/definitions/…`; existing catalog CRUD verbs remain.

---

## What changed

### 0.24.1 — Flow revisioning

| Area | Before | After |
|------|--------|-------|
| `PUT /v1/api/definitions/flows/{id}` | Overwrote catalog record | **Appends** revision `latest + 1` |
| `POST /v1/api/definitions/flows` | Single record | Publishes **revision 1** |
| `GET /v1/api/definitions/flows/{id}` | Latest only | Optional `?revision=N` for explicit revision |
| `ProcessInstance` | Snapshot only | Adds `flow_revision` pin on submit |
| Repository keys | Single flow record | `flow:{id}:rev:{n}` + `latest` pointer |

**Integrator note:** Treat `update_flow` as **publish new revision**, not in-place edit. Instances keep their pinned snapshot until migrated.

### 0.24.2 — Migration rules + impact

| Area | Change |
|------|--------|
| Migration rules | `register_migration_rule()` in `palm/common/persistence/definition_migration.py` |
| Impact query | `GET /v1/api/definitions/flows/{flow_id}/impact?revision=N` |
| Service | `DefinitionService.analyze_impact(flow_id, target_revision=None)` |

### 0.24.3 — Instance migration

| Area | Change |
|------|--------|
| Migration execution | `POST /v1/api/definitions/instances/{instance_id}/migrate` |
| Body | `{"target_revision": N, "dry_run": true\|false}` |
| Instance metadata | `migration_status`, `migration_target_revision`, `migration_from_revision`, `migration_blockers` |
| Job sync | `update_instance_from_job` preserves `migration_*` keys |
| Example | `migrate-instance-demo` wizard in `examples/definitions/migrate_instance_demo.py` |

---

## REST reference (0.24+)

```bash
# Explicit revision
curl -s 'http://localhost:8080/v1/api/definitions/flows/onboard?revision=1'

# Impact — instances behind target (default: latest)
curl -s 'http://localhost:8080/v1/api/definitions/flows/onboard/impact'
curl -s 'http://localhost:8080/v1/api/definitions/flows/onboard/impact?revision=2'

# Dry-run migration
curl -s -X POST 'http://localhost:8080/v1/api/definitions/instances/inst-abc/migrate' \
  -H 'Content-Type: application/json' \
  -H 'X-Palm-Subject: operator' \
  -d '{"target_revision": 2, "dry_run": true}'

# Apply migration
curl -s -X POST 'http://localhost:8080/v1/api/definitions/instances/inst-abc/migrate' \
  -H 'Content-Type: application/json' \
  -H 'X-Palm-Subject: operator' \
  -d '{"target_revision": 2}'
```

---

## MCP / agent operators (0.24.4+)

| Tool | Purpose |
|------|---------|
| `palm_definitions_analyze_impact(flow_id, target_revision=None)` | Instances behind target revision |
| `palm_definitions_migrate_instance(instance_id, target_revision, dry_run=False)` | Dry-run or apply migration |

**Workflow:** impact → dry-run → apply. See `docs/mcp.txt` §14 and example `migrate-instance-demo`.

`palm_assist` paths (in-process):

- `definitions/flows/{flow_id}/impact` with `params.revision`
- `definitions/instances/{instance_id}/migrate` with `params.target_revision`, `params.dry_run`

---

## Legacy instances

| Case | Behavior |
|------|----------|
| `flow_revision` absent | Inferred from `flow_definition.revision` or `1` |
| No migration rule | Impact reports `snapshot_only`; migrate returns blockers |
| Already at target | `400` — target must be ahead of current pin |

---

## Breaking changes

| Change | Mitigation |
|--------|------------|
| `update_flow` appends revision | Do not assume overwrite; use impact + migrate for live instances |
| `FlowDefinition.to_dict()` | Serialized `format_version` (was `version` in older records — readers accept both) |

No REST path removals. Auth still required on migrate (`X-Palm-Subject` when enforced).

---

## Example demo

```bash
palm flow start migrate-demo-source    # revision 1 session
palm instance list
palm flow start migrate-instance-demo  # operator wizard
```

See [examples/README.md](examples/README.md#migrate-instance-demo-migrate-instance-demo).