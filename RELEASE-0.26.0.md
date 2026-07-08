# Release checklist — 0.26.0 (Design hardening + CQRS bus parity)

**Theme:** Production-quality design orchestration and in-process MCP parity with ApplicationHost.

**Bundles:** 0.25.1–0.25.13 (post-0.25.0 hardening)

**Vision:** [docs/VISION-0.25.md](docs/VISION-0.25.md)  
**ADRs:** [008](docs/adr/008-design-service.md) · [009](docs/adr/009-service-cqrs-contributors.md)  
**Migration:** [MIGRATION-0.25.md](MIGRATION-0.25.md) (no breaking changes vs 0.25.0)

## Pre-ship

- [x] 0.25.2 correctness (`next_revision_for_flow`, commit re-impact, commit token errors)
- [x] 0.25.3 structural cleanup (envelope, proposal repo index)
- [x] 0.25.4 pattern `DesignContributorHook` registry
- [x] 0.25.5 pipeline design contributor
- [x] 0.25.6 design proposal demo + meta-flow
- [x] 0.25.7 design CQRS transport bindings
- [x] 0.25.8 registry-driven `DesignService.dispatch`
- [x] 0.25.9–0.25.12 `ServiceCqrsContributor` + standalone bus parity
- [x] 0.25.13 docs sync (AGENTS, MCP, STATUS)
- [x] MCP live verify: propose → impact → commit
- [x] Version **0.26.0**

## Verify

```bash
uv run pytest tests/test_design_service.py tests/test_design_cqrs.py \
  tests/test_design_dispatch.py tests/test_definitions_cqrs_standalone.py \
  tests/test_cqrs_bus_catalog_parity.py tests/test_mcp_design_in_process.py \
  tests/test_rest_design_routes.py tests/test_instance_migration.py -v
just guard-common
```

## Tag

```bash
git tag -a v0.26.0 -m "Palm Engine 0.26.0 — design hardening and CQRS bus parity"
```

## Publish (optional)

```bash
just release-prep
# Set PYPI_TOKEN, then:
just publish
```