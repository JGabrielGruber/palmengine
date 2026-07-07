# Migration guide — 0.25 (Design Service)

**Releases:** 0.25.0 MVP · 0.25.2–0.25.4 completion (durable proposals, auto-migrate, agent safety)  
**Prior:** [MIGRATION-0.24.md](MIGRATION-0.24.md)  
**Vision:** [docs/VISION-0.25.md](docs/VISION-0.25.md) · **ADR:** [docs/adr/008-design-service.md](docs/adr/008-design-service.md)

---

## Summary

0.25 adds the **Design Service** — structured **propose → validate → impact → commit** for flow definition evolution atop 0.24 revisioning. Agents should prefer `palm_design_*` (or `palm_assist` design paths) over direct `palm_definitions_*` writes.

**Final PyPI release** bundles the full 0.24 migration stack and complete 0.25 Design Service.

---

## What changed

| Area | Behavior |
|------|----------|
| Service | `host.design` / `ctx.design` — sixth service domain |
| Proposals | Durable `StorageEngine` keys `palm:design:proposals:{id}` when storage is active |
| Commit | Publishes revision append (0.24.1) then **auto-migrates** impact-compatible instances |
| Agent safety | `commit_token` from validate/impact `mutation` block; strict via `PALM_MCP_REQUIRE_INPUT_TOKEN` |
| MCP | `palm_design_*` tools + `palm_assist` aliases (`design/propose`, `design/commit`, …) |
| Coexistence | `DefinitionService` direct writes remain for integrators and Explorer |

---

## REST reference

```bash
# Propose
curl -s -X POST 'http://localhost:8080/v1/api/design/proposals' \
  -H 'Content-Type: application/json' \
  -H 'X-Palm-Subject: operator' \
  -d '{"flow": {"name": "my-flow", "pattern": "wizard", "options": {"steps": []}}}'

# Validate / impact / commit
curl -s -X POST 'http://localhost:8080/v1/api/design/proposals/prop-abc/validate' -H 'X-Palm-Subject: operator'
curl -s 'http://localhost:8080/v1/api/design/proposals/prop-abc/impact'
curl -s -X POST 'http://localhost:8080/v1/api/design/proposals/prop-abc/commit' \
  -H 'Content-Type: application/json' \
  -H 'X-Palm-Subject: operator' \
  -d '{"commit_token": "<from mutation block>"}'
```

Commit response includes `migrations` summary (`attempted`, `succeeded`, `failed`, `skipped_blocked`, `results`).

---

## MCP / agent workflow

```
palm_design_propose_flow(body) → palm_design_validate → palm_design_impact → palm_design_commit
```

Or via assist:

```
palm_assist(alias="design/propose", params={body: {...}})
palm_assist(alias="design/impact", params={proposal_id: "prop-..."}, format="assistant")
palm_assist(path=["design","proposals","prop-...","commit"], params={commit_token: "..."})
```

### Strict commit token

When `PALM_MCP_REQUIRE_INPUT_TOKEN=1`:

1. `palm_design_validate` or `palm_design_impact` → copy `mutation.commit_token`
2. `palm_design_commit(proposal_id, commit_token=...)` — required on every commit

---

## Auto-migrate semantics

On `commit_proposal`:

1. Revision is published (append-only; not rolled back on migration failure)
2. Instances marked **compatible** in impact analysis are migrated to the new revision
3. **Blocked** instances are skipped and listed in `migrations.skipped_blocked`
4. **snapshot_only** / no rule instances are skipped (`skipped_other`)
5. Per-instance failures appear in `migrations.results` with `status: failed`

Retry failed migrations manually: `palm_definitions_migrate_instance` (0.24.3).

---

## Examples

- `examples/definitions/design_proposal_demo.py` — propose through commit with auto-migrate

---

## References

- [docs/MCP.md](docs/MCP.md) — Design tools table
- [docs/superpowers/plans/2026-07-07-design-service-plus.md](docs/superpowers/plans/2026-07-07-design-service-plus.md)