# Release checklist — 0.25.0 (definition revisioning + Design Service)

**Theme:** Safe catalog evolution — append-only flow revisions, instance migration, and agent-first Design Service.

**Bundles:** 0.24.1–0.24.4 (revisioning & migration) · 0.25.0–0.25.5 (Design Service completion)

**Vision:** [docs/VISION-0.24.md](docs/VISION-0.24.md) · [docs/VISION-0.25.md](docs/VISION-0.25.md)  
**ADRs:** [007](docs/adr/007-definition-revisioning.md) · [008](docs/adr/008-design-service.md)  
**Migration:** [MIGRATION-0.24.md](MIGRATION-0.24.md) · [MIGRATION-0.25.md](MIGRATION-0.25.md)

## Pre-ship

- [x] Flow revisioning (`publish_flow_revision`, instance `flow_revision` pin)
- [x] Migration rules + impact query + instance migration execution
- [x] Design Service (`propose` → `validate` → `impact` → `commit`)
- [x] Durable design proposals (`StorageEngine`)
- [x] Auto-migrate compatible instances on design commit
- [x] Commit token gate + `palm_assist` design paths
- [x] Wizard design contributor
- [x] MCP `palm_design_*` + `palm_definitions_analyze_impact` / `migrate_instance`
- [x] `MIGRATION-0.24.md`, `MIGRATION-0.25.md`, ADR-008
- [x] Version **0.25.0**

## Verify

```bash
uv run pytest tests/test_definition_repository_revisions.py \
  tests/test_definition_migration_rule.py \
  tests/test_definition_impact_query.py \
  tests/test_instance_migration.py \
  tests/test_design_service.py \
  tests/test_wizard_design_contributor.py \
  tests/test_rest_design_routes.py -v
just guard-common
just docs-check
```

## Tag

```bash
git tag -a v0.25.0 -m "Palm Engine 0.25.0 — definition revisioning, migration, and Design Service"
```

## Publish (optional)

```bash
just release-prep
# Set PYPI_TOKEN, then:
just publish
```