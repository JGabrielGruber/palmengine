# Palm Engine — Project Status

**Current Version:** `0.14.13` (shipping) · **0.15** service layer on master  
**Last Updated:** June 30, 2026  
**Maturity:** Wizard Experience shipped · **0.14 MCP** operator adapter · **0.15** CQRS schemas + service layer + in-process MCP.

## Quick Overview

Palm is a lightweight, Python-first orchestration engine built on a clean **Behavior Tree** foundation. It excels at complex multi-step workflows, rich interactive wizards, compositional sub-flow orchestration, and transactional processes with durable state and human-in-the-loop participation.

**Distribution name:** `palmengine` (PyPI)  
**Import name:** `palm`  
**Recommended entrypoint:** `ApplicationHost` via `create_cli_host()` for CLI, or `ApplicationHost(profile=HostProfile.all_in_one())` for library use

## Architecture Snapshot

Palm follows a **layered, registry-driven** model with a strictly pure core:

- `palm/core/` — Pure foundational engines (Behavior Tree, Orchestration, Context, Storage, Resource, Event, Auth, Transform). **Zero external Palm imports allowed.**
- `palm/common/services/` — User-facing API (`InternalService`, `DefinitionService`, `ExecutionService`, `InstanceSession`, `ReplSession`).
- `palm/common/` — Rich shared coordination layer (executions, plans, hooks, persistence, CQRS + schemas, compensation, transforms, runtime infrastructure).
- `palm/app/` — Application orchestration. `ApplicationHost` is the primary recommended orchestrator; `PalmApp` is infrastructure.
- `palm/patterns/`, `palm/providers/`, `palm/storages/` — Extensible plugin-style apps (`PatternApp` / `ProviderApp` + `bindings/`/`flow/` — see [docs/PATTERN-APPS.md](docs/PATTERN-APPS.md) and [docs/PROVIDER-APPS.md](docs/PROVIDER-APPS.md)).
- `palm/runtimes/` — Thin surfaces over the common runtime layer.

See [ARCHITECTURE.md](ARCHITECTURE.md) and [AGENTS.md](AGENTS.md) for full details and rules.

## Key Capabilities (Mature)

- Behavior Tree execution engine
- **Resource system (0.12)** — `ResourceDefinition`, `ResourceEngine`, `ResourceLeaf`, `ResourceCatalog`, `palm` provider
- Powerful Wizard pattern (validation, collection, transform, **resource** steps, parallel branches, backtracking, summary + commit)
- **Wizard REST + Explorer (0.13)** — `/v1/wizards`, HTMX workspace, collection editor
- 22 built-in transform rules + extensible `TransformEngine` (`enrich_resource` with `resource_ref`)
- Layered state schemas + scoped execution state
- Durable process instances with resume across restarts
- CQRS (Command + Query buses + projections including `resource_invocations`)
- Reliability primitives: Transactional outbox, Compensation handlers (resource undo), Webhook dispatch support
- Composable host roles (`ApplicationHost` + `HostProfile`)
- Rich CLI + REPL with live dashboard (`palm status`) and `palm resource *` commands
- Multiple runtimes (Embedded, Daemon, Server, CLI)
- **Palm Explorer** — SSR hub at `/explorer` (flows, jobs, instances, wizard workspace, **resources**); `GET /` redirects here
- **MCP operator adapter (0.14)** — `palm-mcp` stdio + native HTTP `/mcp`; 26 tools, 4 prompts, 10 resources; [docs/MCP.md](docs/MCP.md)
- **Service layer (0.15)** — schema-validated CQRS + `host.execution.on(instance_id)`; REST/MCP thin adapters; [docs/VISION-0.15.md](docs/VISION-0.15.md)

## 0.13 — Wizard Experience (Shipped)

**Vision document:** [docs/VISION-0.13.md](docs/VISION-0.13.md)  
**Operator guide:** [EXPLORER-WIZARD.md](EXPLORER-WIZARD.md)  
**Phase refactor:** [src/palm/patterns/wizard/MIGRATION-WIZARD-PHASES.md](src/palm/patterns/wizard/MIGRATION-WIZARD-PHASES.md)  
**Release checklist:** [RELEASE-0.13.0.md](RELEASE-0.13.0.md)

| Component | Status |
|-----------|--------|
| `/v1/wizards` REST surface | ✅ Shipped |
| `build_wizard_view()` read model | ✅ Shipped |
| Explorer wizard workspace (HTMX) | ✅ Shipped |
| Collection overview + add/edit/remove UI | ✅ Shipped |
| Wizard phase modularization (`phases/`) | ✅ Shipped |
| SSR + REST test coverage | ✅ Shipped |

## 0.12 — Compositional Power (Shipped)

**Vision document:** [docs/VISION-0.12.md](docs/VISION-0.12.md)  
**Migration:** [MIGRATION-0.12.md](MIGRATION-0.12.md)  
**ADR:** [docs/adr/001-compositional-power-resources.md](docs/adr/001-compositional-power-resources.md)

## Pattern app alignment (June 2026)

| Pattern | Structure | Status |
|---------|-----------|--------|
| wizard | Full `bindings/` + `flow/` + phases | ✅ Reference implementation |
| parallel | `bindings/` + `flow/` (branch, scope, merge) | ✅ Aligned |
| pipeline | `bindings/definitions` + `behavior_tree` | ✅ Aligned |
| dag, etl | `bindings/definitions` + `flow/` scaffold | ✅ Honest placeholders |

ADR: [docs/adr/002-pattern-apps-and-common-boundaries.md](docs/adr/002-pattern-apps-and-common-boundaries.md)

## Provider app alignment (June 2026)

| Provider | Structure | Status |
|----------|-----------|--------|
| palm | Full `bindings/` + `flow/` | ✅ Reference implementation |
| rest | `bindings/resource` + `bindings/transport` | ✅ Real HTTP (stub fallback without base_url) |
| graphql, postgres | `app.py` only | ✅ Honest stubs |

ADR: [docs/adr/003-provider-apps.md](docs/adr/003-provider-apps.md)

## 0.15 — CQRS Schemas + Service Layer (Shipped on master)

**Vision:** [docs/VISION-0.15.md](docs/VISION-0.15.md)  
**ADR:** [docs/adr/004-cqrs-schemas-service-layer.md](docs/adr/004-cqrs-schemas-service-layer.md)  
**Spec:** [docs/superpowers/specs/2026-06-30-cqrs-schemas-service-layer-design.md](docs/superpowers/specs/2026-06-30-cqrs-schemas-service-layer-design.md)

| Component | Status |
|-----------|--------|
| `CqrsSchemaRegistry` + contributor schemas | ✅ 0.15a |
| `BaseService`, `InternalService` | ✅ 0.15b |
| REST/MCP inspect → services | ✅ 0.15b–c |
| `PalmInProcessBackend` (`PALM_MCP_IN_PROCESS`) | ✅ 0.15c |
| `DefinitionService` + catalog routes | ✅ 0.15d |
| `ExecutionService`, `InstanceSession`, `ReplSession` | ✅ 0.15e |
| Docs + ADR 004 | ✅ 0.15f |

```bash
# Local MCP (no palm server)
PALM_MCP_IN_PROCESS=1 uv run --extra mcp palm-mcp

# Instance-centric API
host.execution.on(instance_id).input("yes")
```

## 0.14 — MCP Operator (Shipped)

**Agent guide:** [docs/MCP.md](docs/MCP.md) · **Agent context:** [docs/llms.txt](docs/llms.txt)

| Component | Status |
|-----------|--------|
| `palm-mcp` stdio adapter (FastMCP) | ✅ Phase 1 |
| REST: resume-child-wait, resume-wizard-tick, instance tree | ✅ Phase 1 |
| Operator tools (inspect, input, list waiting, submit) | ✅ Phase 2a |
| Definition catalog REST + MCP resources | ✅ Phase 2b |
| Pattern MCP contributor registry | ✅ Phase 3 |
| Pattern MCP tools (wizard collection, parallel branches) | ✅ Phase 3 |
| MCP operator prompts | ✅ Phase 3 |
| REST: cancel job, validate flow, doctor | ✅ Phase 4 |
| MCP debug + lifecycle tools (Tier 3) | ✅ Phase 4 |
| Native HTTP MCP on `/mcp` (streamable-http) | ✅ Phase 5 |
| `palm_invoke_resource`, `palm_compose_status` | ✅ Phase 5 |
| App-level MCP contributor registry | ✅ Phase 5 |
| MCP module split (`tools.py`, `resources.py`) | ✅ Phase 6 |
| Plain-string wizard input coercion | ✅ Phase 6 |
| SSE MCP (`/mcp/sse`, `/mcp/messages`) | ✅ Phase 6 |

```bash
uv sync --extra mcp && just palm-server    # REST + /mcp HTTP
just mcp-inspector                       # MCP Inspector UI
```

## Areas Under Active Improvement
- WebSocket runtime surface for live wizard/job streaming
- Explorer inline validation for collection field errors
- Saga-style compensation patterns beyond single-resource undo
- KernelLeaf / GPU execution research (non-goal for 0.13)

## Known Limitations & Technical Debt

- Documentation consistency enforced via `just docs-check` and `just guard-common` (wired into `just check` / `just release-prep`)
- Field-phase cancel in Explorer may not always map to wizard cancel (use REST/CLI for edge cases)
- Standalone `ServerRuntime` may return empty resource invocation rows when projections aren't wired

## Documentation Health

| Document              | Status          | Notes |
|-----------------------|------------------|-------|
| `README.md`           | Good            | 0.13 Explorer + 0.14 MCP agent section |
| `ARCHITECTURE.md`     | Good            | Pattern apps + MCP stdio/HTTP surfaces |
| `docs/MCP.md`         | Good            | **Agent development guide** — setup, workflows, tool inventory |
| `docs/PATTERN-APPS.md`| Good            | Canonical PatternApp + bindings/flow guide |
| `docs/PROVIDER-APPS.md`| Good           | Canonical ProviderApp + bindings/flow guide |
| `docs/adr/002-*.md`   | Good            | Pattern/common boundary ADR |
| `docs/adr/003-*.md`   | Good            | Provider app layout ADR |
| `EXPLORER-WIZARD.md`  | Good            | Human operator + integrator guide |
| `docs/VISION-0.13.md` | Good            | Release vision |
| `docs/index.html`     | Good            | v0.14.13 badge + MCP in featureList |
| `docs/llms.txt`       | Good            | AI context + 0.15 service layer + MCP in-process (`palm://agent/guide`) |
| `docs/VISION-0.15.md` | Good            | Service layer release vision |
| `docs/adr/004-*.md`   | Good            | CQRS schemas + service layer ADR |
| `AGENTS.md`           | Good            | Service layer + MCP in-process conventions |
| `DEVELOPMENT.md`      | Good            | Contributor setup; 0.15 service layer on master |
| `CHANGELOG.md`        | Good            | `[0.14.9]` MCP Operator section complete |
| `RELEASE-0.14.9.md`   | Good            | Release checklist |

## Priorities & Next Steps

Cleanup track: [docs/superpowers/specs/2026-06-30-0.15-cleanup-track-design.md](docs/superpowers/specs/2026-06-30-0.15-cleanup-track-design.md)

1. ~~**0.15.1 hygiene**~~ — ✅ ruff fix + format (`f44d36f`); wizard `I001` exempt in `pyproject.toml`
2. **0.15.0 release prep** (optional) — version bump, CHANGELOG, `RELEASE-0.15.0.md` — [plan](docs/superpowers/plans/2026-06-30-0.15.0-release-hygiene.md)
3. ~~**0.15.2**~~ — ✅ REST validation → `CqrsSchemaRegistry`; serializer imports; MCP dual-backend docs — [plan](docs/superpowers/plans/2026-06-30-0.15.2-dedupe.md)
4. ~~**0.15.3**~~ — ✅ legacy aliases + shims removed on master — [plan](docs/superpowers/plans/2026-06-30-0.15.3-legacy-cleanup.md)
5. Definition catalog write paths via `DefinitionService` (0.16+)
6. Full OpenAPI from `CqrsSchemaRegistry` + service views (0.16+)
7. WebSocket surface for live wizard prompts (0.16+)

## Useful Links

- [CHANGELOG.md](CHANGELOG.md)
- [EXPLORER-WIZARD.md](EXPLORER-WIZARD.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [AGENTS.md](AGENTS.md)
- [DEVELOPMENT.md](DEVELOPMENT.md)
- [docs/MCP.md](docs/MCP.md) — agent development with Palm MCP
- [RELEASE-0.14.9.md](RELEASE-0.14.9.md) — release checklist
- Examples: `examples/README.md`

## How to Contribute

Follow the guidance in [DEVELOPMENT.md](DEVELOPMENT.md) and [AGENTS.md](AGENTS.md).  
All significant architectural changes should be accompanied by an ADR and documentation updates.