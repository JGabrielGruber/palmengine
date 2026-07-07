# Design Service+ Implementation Plan (0.25.1–final release)

**Goal:** Complete Design Service and ship **one PyPI release** bundling 0.24 revisioning/migration (0.24.1–0.24.4) and 0.25 design orchestration.

**ADR:** [docs/adr/008-design-service.md](../../adr/008-design-service.md)  
**Vision:** [docs/VISION-0.25.md](../../VISION-0.25.md)  
**Spec:** [docs/superpowers/specs/2026-07-03-design-service-design.md](../specs/2026-07-03-design-service-design.md)  
**Foundation:** [definition-revisioning plan](2026-07-03-definition-revisioning.md) (0.24.1–0.24.4 ✅ local)

## Locked decisions

| # | Decision |
|---|----------|
| 1 | **Single final release** — PyPI ships the full 0.24 migration stack + complete Design Service together |
| 2 | **Auto-migrate on commit** — `commit_proposal` migrates impact-compatible instances after revision publish |
| 3 | **CQRS below business rules** — `DesignService` methods are authoritative; CQRS bindings are late transport plumbing (0.25.7) |
| 4 | **ADR-008** — [008-design-service.md](../../adr/008-design-service.md) |

---

## Phase 0.25.1 — Documentation hygiene

- [x] ADR-008
- [x] This plan committed
- [x] `VISION-0.25.md` — status: implemented (local), release pending
- [x] `design-service-design.md` — MVP shipped; deltas for 0.25.2–0.25.4
- [x] `MIGRATION-0.25.md` — operator workflow, auto-migrate semantics, agent policy
- [ ] `definition-revisioning.md` — mark 0.24 + 0.25.0 tasks complete
- [x] `STATUS.md` — 0.25+ phases table; release gate note
- [x] `AGENTS.md` — ADR-008 cross-ref
- [ ] MCP tool descriptions — steer agents to `palm_design_*`
- [x] `examples/definitions/design_proposal_demo.py`

**Commit:** `docs(0.25.1): ADR-008, MIGRATION-0.25, plan sync`

---

## Phase 0.25.2 — Durable proposal store

**Files:**

- `src/palm/services/design/proposal.py` — extract `ProposalRepository` protocol
- `src/palm/services/design/storage_proposal_repository.py` — `palm:design:proposals:{id}`
- `src/palm/app/host/application_host.py` — wire storage-backed repo when `StorageEngine` initialized

**Tasks:**

- [x] `StorageProposalRepository` CRUD + list by `flow_id` / `status`
- [x] Index key or list scan for `list_proposals`
- [x] Host factory: in-memory for tests, storage for production host
- [x] Tests: propose → persist → reload host → `get_proposal` succeeds

**Commit:** `feat(0.25.2): durable StorageEngine design proposals`

---

## Phase 0.25.3 — Auto-migrate on commit

**Files:**

- `src/palm/services/design/service.py` — extend `commit_proposal`
- `tests/test_design_service.py` — auto-migrate scenarios

**Behavior:**

1. Validate + publish revision (unchanged)
2. Re-run or reuse impact analysis for `target_revision`
3. For each instance with `compatible` (per impact flags): call `definitions.migrate_instance(instance_id, target_revision=committed_revision)`
4. Skip `blocked` / `snapshot_only` instances
5. Return commit result:

```json
{
  "proposal_id": "...",
  "flow_id": "...",
  "revision": 3,
  "flow": { "...": "..." },
  "migrations": {
    "attempted": 2,
    "succeeded": 1,
    "failed": 1,
    "skipped_blocked": 1,
    "results": [ { "instance_id": "...", "status": "ok|failed|skipped", "detail": "..." } ]
  }
}
```

**Tasks:**

- [x] `commit_proposal` post-publish migration loop
- [x] Respect migration rules (`can_migrate` false → skipped with reason)
- [x] Tests with `migrate_instance_demo` fixtures / test doubles
- [x] REST/MCP response includes `migrations` block
- [x] Document auto-migrate in `MIGRATION-0.25.md`

**Commit:** `feat(0.25.3): auto-migrate compatible instances on design commit`

---

## Phase 0.25.4 — Agent safety + assist aliases

**Files:**

- `src/palm/services/design/service.py` — commit gate (validation required; optional token)
- `src/palm/runtimes/mcp/design/tools.py` — strict commit token
- `src/palm/services/assist/registry.py` or dispatch table — design routes
- `src/palm/common/operator/` — assistant view for impact/commit choices

**Tasks:**

- [x] Commit requires prior successful `validate_proposal` on same proposal
- [x] Optional `commit_token` from validate/impact inspect (mirror 0.23 `input_token`)
- [x] `PALM_MCP_REQUIRE_INPUT_TOKEN` applies to `palm_design_commit`
- [x] `palm_assist` paths: `design/propose`, `design/validate`, `design/impact`, `design/commit`, `design/list`, `design/discard`
- [x] Assistant view: human-first impact summary with commit / discard choices
- [x] Tests: strict mode rejects commit without token

**Commit:** `feat(0.25.4): design commit safety and palm_assist aliases`

---

## Phase 0.25.5 — Pattern design contributors (recommended)

**Files:**

- `src/palm/patterns/wizard/bindings/design.py` (or equivalent)
- Register in wizard `PatternApp.ready()`

**Tasks:**

- [ ] Wizard contributor: step slug uniqueness, collection schema sanity
- [ ] Register via `register_design_contributor()`
- [ ] Test: invalid proposal → blocker in `validate_proposal`

**Commit:** `feat(0.25.5): wizard design validation contributor`

---

## Phase 0.25.6 — Dogfooding (stretch)

- [ ] `examples/definitions/design_proposal_demo.py` end-to-end with auto-migrate
- [ ] Optional meta-flow sketch for agent guide updates (document only if not implemented)

**Commit:** `examples(0.25.6): design proposal demo with auto-migrate`

---

## Phase 0.25.7 — CQRS transport bindings (deferred)

> **Policy:** Business rules already live in `DesignService`. This phase adds bus-level transport only.

**Files:**

- `src/palm/services/design/bindings/cqrs/`
- `src/palm/app/host/cqrs_wiring.py`
- `schema_bootstrap.py` — design command/query schemas

**Tasks:**

- [ ] `ProposeFlowDefinitionCommand`, `CommitDesignProposalCommand`, etc.
- [ ] Register design CQRS contributor
- [ ] Bus tests; REST/MCP may continue calling service directly

**Commit:** `feat(0.25.7): design CQRS transport bindings`

---

## Final release gate

Ship PyPI only when all **required** phases are green:

| Gate | Phase |
|------|-------|
| 0.24.1–0.24.4 local + docs | Foundation |
| 0.25.1 docs | Hygiene |
| 0.25.2 durable proposals | Required |
| 0.25.3 auto-migrate | Required |
| 0.25.4 agent safety + assist | Required |
| `MIGRATION-0.24.md` + `MIGRATION-0.25.md` | Operator guides |
| `RELEASE-0.25.md` or combined release notes | Release checklist |

**Version bump:** TBD at release request (bundles 0.24 + 0.25; PyPI currently `0.23.1`).

---

## Verification (each phase)

```bash
uv run pytest tests/test_design_service.py tests/test_rest_design_routes.py \
  tests/test_instance_migration.py tests/test_definition_impact_query.py \
  tests/test_definition_repository_revisions.py -v
just guard-common
just docs-check   # when REST/MCP/docs touched
```

---

## Orthogonal (not blocking final release)

| Item | Track |
|------|-------|
| 0.23 deferred (`palm-compose-guide`, process handoff, WebSocket) | 0.26+ assist |
| 0.23.2 mutation gate release | Can bundle with 0.25.4 |
| Explorer visual designer | Future |
| Process/resource revisioning | 0.27+ per ADR-007 |