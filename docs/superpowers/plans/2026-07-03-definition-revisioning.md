# Definition Revisioning Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans or subagent-driven-development for implementation. This document is the DAG for **0.24.1+ code** — not executed in the 0.24 vision release.

**Goal:** Append-only flow revisions, instance revision pins, migration rules, and impact queries — foundation for Design Service (0.25).

**Architecture:** Repository key layout + `ProcessInstance.flow_revision` + transform-registry migration rules. No `palm/core/` changes. Definitions service owns catalog verbs.

**Tech Stack:** Python 3.11+, Palm `ApplicationHost`, `DefinitionRepository`, `TransformEngine`, `pytest`, `just guard-common`

**Design spec:** [docs/superpowers/specs/2026-07-03-definition-revisioning-design.md](../specs/2026-07-03-definition-revisioning-design.md)

**Vision:** [docs/VISION-0.24.md](../../VISION-0.24.md)

**Prerequisite:** 0.23.1 shipped; 0.23.2 mutation-gate cleanup committed (optional bundle)

---

## File map

| Area | Create | Modify |
|------|--------|--------|
| Definitions domain | `FlowRevision` helpers in `definitions/flow.py` | `definition_repository.py`, `process_instance.py` |
| Submission | — | `flow_submission.py`, `instance_sync.py`, `job_context.py` |
| Service | `services/definitions/revisions.py` (optional) | `services/definitions/service.py`, `registry.py` |
| Migration | `common/transforms/rules/definition_migration.py` | transform registry bootstrap |
| Impact | CQRS query + handler | `services/definitions/service.py` |
| Hooks | — | `common/hooks/instance_persistence.py` |
| Example | `examples/definitions/migrate_instance_demo.py` | — |
| Docs (per release) | `MIGRATION-0.24.md`, `RELEASE-0.24.x.md` | `STATUS.md`, `CHANGELOG.md` |
| Tests | `test_definition_repository_revisions.py`, `test_definition_migration_rule.py`, `test_definition_impact_query.py` | `test_flow_submission.py` |

---

## Phase 0.24.1 — Flow revisioning

### Task 1: Repository revision keys

**Files:** `src/palm/common/persistence/definition_repository.py`

- [ ] **Step 1:** Test `publish_flow_revision` assigns monotonic revision
- [ ] **Step 2:** Test `get_flow(id, revision=2)` loads explicit revision
- [ ] **Step 3:** Test `get_flow(id)` resolves latest
- [ ] **Step 4:** Test `list_flow_revisions(id)` returns index
- [ ] **Step 5:** Lazy compat: legacy single-key records → `revision=1`

Run: `uv run pytest tests/test_definition_repository_revisions.py -v`

### Task 2: FlowDefinition revision field

**Files:** `src/palm/definitions/flow.py`

- [ ] Add `revision: int | None` on dataclass
- [ ] Rename serialized `version` → `format_version` in `to_dict` / `from_dict` (with backward compat read for `version`)
- [ ] `publish` sets `revision` on record

### Task 3: Instance pin

**Files:** `src/palm/instances/process_instance.py`, `src/palm/common/executions/flow_submission.py`, `src/palm/common/persistence/instance_sync.py`

- [ ] Add `flow_revision: int | None` to `ProcessInstance`
- [ ] Submit path sets revision from resolved flow
- [ ] Persistence round-trip tests

Run: `uv run pytest tests/test_flow_submission.py tests/test_instance_persistence.py -v`

### Task 4: DefinitionService methods

**Files:** `src/palm/services/definitions/service.py`, `registry.py`

- [ ] `get_flow(..., revision=None)`
- [ ] `publish_flow_revision(flow_id, body)`
- [ ] `list_flow_revisions(flow_id)`
- [ ] `update_flow` → publish `latest+1`
- [ ] `create_flow` → publish `revision=1`

### Task 5: REST/MCP optional revision param

**Files:** `runtimes/server/surfaces/rest/definitions/handlers.py`, `runtimes/mcp/definitions/tools.py`

- [ ] `GET flow?revision=` query param
- [ ] Document semantic change in `MIGRATION-0.24.md`

### Task 5 commit

```bash
git commit -m "feat(0.24.1): append-only flow definition revisions"
```

---

## Phase 0.24.2 — Migration rules + impact query

### Task 6: DefinitionMigrationRule

**Files:** `src/palm/common/transforms/rules/definition_migration.py`

- [ ] `MigrationContext` dataclass
- [ ] `DefinitionMigrationRule` base with `can_migrate`, `migrate_state`
- [ ] `register_migration_rule()` or `@transform_rule` alias
- [ ] Example rule for wizard step rename in tests

Run: `uv run pytest tests/test_definition_migration_rule.py -v`

### Task 7: Impact query

**Files:** definitions CQRS bindings, `service.py`

- [ ] `AnalyzeDefinitionImpactQuery` + handler
- [ ] Scan instance projection by `flow_id`
- [ ] Compare `flow_revision` vs latest; run `can_migrate` when rule exists
- [ ] `DefinitionService.analyze_impact(flow_id, target_revision=None)`

Run: `uv run pytest tests/test_definition_impact_query.py -v`

### Task 7 commit

```bash
git commit -m "feat(0.24.2): definition migration rules and impact query"
```

---

## Phase 0.24.3 — Migration execution hooks

### Task 8: Instance migration metadata

**Files:** `src/palm/common/hooks/instance_persistence.py`, `services/definitions/service.py` or `execution/flows/service.py`

- [ ] `request_instance_migration(instance_id, target_revision)`
- [ ] Metadata: `migration_status`, `migration_target_revision`, blockers
- [ ] Apply rule → update instance state + `flow_revision` + snapshot
- [ ] Failed migration sets `migration_status: failed`

### Task 9: Example migration flow

**Files:** `examples/definitions/migrate_instance_demo.py`

- [ ] Wizard flow: confirm → dry-run → apply → summary
- [ ] Document in `examples/README.md`

### Task 9 commit

```bash
git commit -m "feat(0.24.3): instance migration hooks and demo flow"
```

---

## Phase 0.25.0 — Design Service (separate plan)

See [design-service-design.md](../specs/2026-07-03-design-service-design.md). Depends on 0.24.1–0.24.3.

| Task | Summary |
|------|---------|
| 0.25a | `palm/services/design/` skeleton + `host.design` |
| 0.25b | Proposal store + `propose_flow` / `commit_proposal` |
| 0.25c | MCP `palm_design_*` + REST `/v1/api/design/…` |
| 0.25d | `register_design_contributor()` + docs |

---

## Verification (each phase)

```bash
uv run pytest tests/test_definition_repository_revisions.py \
  tests/test_definition_migration_rule.py \
  tests/test_definition_impact_query.py -v
just guard-common
just docs-check   # when REST/OpenAPI touched
```

---

## Release policy

- **0.24 vision release:** docs only (this plan + spec + ADR + vision)
- **0.24.1+:** ship when usefulness confirmed; one descriptive release per feature slice preferred
- `MIGRATION-0.24.md` at first breaking semantic change (`update_flow` → append revision)