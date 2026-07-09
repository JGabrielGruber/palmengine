# Palm Engine — Project Status

**Current Version:** `0.32.10`
**Last Updated:** July 9, 2026
**Maturity:** Wizard Experience · MCP operator adapter · Assist design entry · **WebSocket Assist + Portal dogfood** · **`palm_assist`** primary weak-LLM surface.

## Quick Overview

Palm is a lightweight, Python-first orchestration engine built on a clean **Behavior Tree** foundation. It excels at complex multi-step workflows, rich interactive wizards, compositional sub-flow orchestration, and transactional processes with durable state and human-in-the-loop participation.

**Distribution name:** `palmengine` (PyPI)  
**Import name:** `palm`  
**Recommended entrypoint:** `ApplicationHost` via `create_cli_host()` for CLI, or `ApplicationHost(profile=HostProfile.all_in_one())` for library use

## Architecture Snapshot

Palm follows a **layered, registry-driven** model with a strictly pure core:

- `palm/core/` — Pure foundational engines (Behavior Tree, Orchestration, Context, Storage, Resource, Event, Auth, Transform). **Zero external Palm imports allowed.**
- `palm/services/` — User-facing domain API (`definitions`, `execution/flows`, `execution/providers`, `system`, `assist`, `design`); `palm/common/services/` retains primitives only.
- `palm/common/` — Rich shared coordination layer (executions, plans, hooks, persistence, CQRS + schemas, compensation, transforms, runtime infrastructure).
- `palm/app/` — Application orchestration. `ApplicationHost` is the primary recommended orchestrator; `PalmApp` is infrastructure.
- `palm/patterns/`, `palm/providers/`, `palm/storages/` — Extensible plugin-style apps (`PatternApp` / `ProviderApp` + `bindings/`/`flow/` — see [docs/PATTERN-APPS.md](docs/PATTERN-APPS.md) and [docs/PROVIDER-APPS.md](docs/PROVIDER-APPS.md)).
- `palm/runtimes/` — Thin surfaces over the common runtime layer.

See [ARCHITECTURE.md](ARCHITECTURE.md) and [AGENTS.md](AGENTS.md) for full details and rules.

## Key Capabilities (Mature)

- Behavior Tree execution engine
- **Resource system (0.12)** — `ResourceDefinition`, `ResourceEngine`, `ResourceLeaf`, `ResourceCatalog`, `palm` provider
- Powerful Wizard pattern (validation, collection, transform, **resource** steps, parallel branches, backtracking, summary + commit)
- **Flow REST + Explorer (0.16)** — `/v1/api/flows/…` session REPL; Explorer SSR workspace; collection editor
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
| `/v1/api/flows` session REST | ✅ Shipped (0.16) |
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

## 0.15.4 — CQRS Schemas + Service Layer (Shipped)

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

**Agent guide:** [docs/MCP.md](docs/MCP.md) · **MCP operator guide:** [docs/mcp.txt](docs/mcp.txt) (`palm://agent/guide`) · **Project context:** [docs/llms.txt](docs/llms.txt)

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
| `docs/index.html`     | Good            | v0.16.5 badge + service API in featureList |
| `docs/mcp.txt`        | Good            | MCP operator guide (`palm://agent/guide` default) |
| `docs/llms.txt`       | Good            | Broader AI / project context |
| `docs/skills/palm/`   | Good            | Portable agent skill (+ MCP resources + Grok mirror) |
| `docs/DOCKER.md`      | Good            | Docker Compose stack, volumes, remote MCP |
| `docs/VISION-0.16.md` | Good            | 0.16 release vision |
| `docs/VISION-0.18-ASSIST.md` | Good     | Assist domain vision (planned) |
| `docs/adr/005-*.md`   | Good            | Service-domain API ADR |
| `docs/adr/006-*.md`   | Good            | Assist domain ADR (proposed) |
| `AGENTS.md`           | Good            | 0.16 service layer + MCP conventions |
| `DEVELOPMENT.md`      | Good            | Contributor setup + 0.16.5 release |
| `CHANGELOG.md`        | Good            | `[0.16.5]` service-domain API release |
| `RELEASE-0.16.5.md`   | Good            | Release checklist |
| `MIGRATION-0.16.md`   | Good            | Integrator upgrade guide |

## 0.16.5 — Services Are the API (Shipped)

**Vision:** [docs/VISION-0.16.md](docs/VISION-0.16.md)  
**ADR:** [docs/adr/005-service-domain-api.md](docs/adr/005-service-domain-api.md)  
**Migration:** [MIGRATION-0.16.md](MIGRATION-0.16.md)  
**Release checklist:** [RELEASE-0.16.5.md](RELEASE-0.16.5.md)

| Component | Status |
|-----------|--------|
| `palm/services/` domain extraction | ✅ Shipped |
| Per-service registries (definitions, flows, providers, system) | ✅ Shipped |
| REST `/v1/api/…` per-domain handlers | ✅ Shipped |
| MCP remount by service (breaking tool names) | ✅ Shipped |
| Delete legacy wizard/catalog handlers | ✅ Shipped |
| `execution/flows` ≠ `execution/providers` | ✅ Shipped |
| Definition catalog CRUD on new surface | ✅ Shipped |
| Provider invoke on `/v1/api/providers/…` | ✅ Shipped |

## 0.17 — Service Completion (Shipped)

**Design:** [docs/superpowers/specs/2026-07-01-0.17-service-completion-design.md](docs/superpowers/specs/2026-07-01-0.17-service-completion-design.md)  
**Plan:** [docs/superpowers/plans/2026-07-01-0.17-service-completion.md](docs/superpowers/plans/2026-07-01-0.17-service-completion.md)  
**Migration:** [MIGRATION-0.17.md](MIGRATION-0.17.md)

| Phase | Theme | Status |
|-------|-------|--------|
| 0.17.0 | System REST parity — delete `/v1/jobs`, `/v1/instances` monolith | ✅ Shipped |
| 0.17.1 | `ProcessExecutionService` + `/v1/api/processes` | ✅ Shipped |
| 0.17.2 | Palm provider remote alignment | ✅ Shipped |
| 0.17.3 | OpenAPI from per-service registries | ✅ Shipped |

## 0.18 — Assist Domain (Shipped)

**Vision:** [docs/VISION-0.18-ASSIST.md](docs/VISION-0.18-ASSIST.md)  
**Design:** [docs/superpowers/specs/2026-07-01-assist-domain-design.md](docs/superpowers/specs/2026-07-01-assist-domain-design.md)  
**Plan:** [docs/superpowers/plans/2026-07-01-assist-domain.md](docs/superpowers/plans/2026-07-01-assist-domain.md)  
**ADR:** [docs/adr/006-assist-domain.md](docs/adr/006-assist-domain.md)  
**Migration:** [MIGRATION-0.18.md](MIGRATION-0.18.md) · **Release:** [RELEASE-0.18.0.md](RELEASE-0.18.0.md)

| Phase | Theme | Status |
|-------|-------|--------|
| 0.18.0 | Assist MVP — REST `/v1/api/assist/…`, `host.assist`, `palm-operator-entry` | ✅ Shipped |

## 0.19 — Stable MCP proxy (Shipped)

**Migration:** [MIGRATION-0.19.md](MIGRATION-0.19.md) · **Release:** [RELEASE-0.19.0.md](RELEASE-0.19.0.md)

| Phase | Theme | Status |
|-------|-------|--------|
| 0.19.0 | `palm_assist` MCP proxy + contributor aliases | ✅ Shipped |
| 0.19.1 | Compact coercion for in-process flow session dispatch | ✅ Shipped |

## 0.20 — Assistant vs Powertool Views (Shipped)

**Migration:** [MIGRATION-0.20.md](MIGRATION-0.20.md) · **Design:** [docs/superpowers/specs/2026-07-01-assistant-powertool-views-design.md](docs/superpowers/specs/2026-07-01-assistant-powertool-views-design.md)

| Release | Theme | Status |
|---------|-------|--------|
| 0.20.0 | Design spec — assistant (compose + human) vs powertool (compact) | ✅ Shipped |
| 0.20.1 | `view_registry.py` in common — thin format dispatch | ✅ Shipped |
| 0.20.2 | `assist/views.py` — compose pipeline + enricher registry | ✅ Shipped |
| 0.20.3 | Assist session defaults; start returns first turn | ✅ Shipped |
| 0.20.4 | `palm_assist` `format=assistant` default | ✅ Shipped |
| 0.20.5 | `MIGRATION-0.20.md`, docs, verification | ✅ Shipped |

## 0.21 — Assistant Expansion (Planned)

**Design:** [docs/superpowers/specs/2026-07-01-assistant-expansion-design.md](docs/superpowers/specs/2026-07-01-assistant-expansion-design.md)

| Release | Theme | Status |
|---------|-------|--------|
| 0.21.0 | Design spec — CLI, Explorer, actions, flows opt-in | ✅ Shipped |
| 0.21.1 | CLI `assist *` commands + `render_assistant_panel` | ✅ Shipped |
| 0.21.2 | Explorer assist catalog + `assist_workspace` | ✅ Shipped |
| 0.21.3 | Explorer HTMX verbs + handoff CTA + nav | ✅ Shipped |
| 0.21.4 | `actions` block + production enrichers + REST catalog/flows | ✅ Shipped |
| 0.21.5 | Opt-in `format=assistant` on flows REST/MCP | ✅ Shipped |
| 0.21.6 | `MIGRATION-0.21.md`, docs, verification | ✅ Shipped |
| 0.21.7 | Weak-LLM MCP hotfixes (boot, null params, bare assist) | ✅ Shipped |

## 0.21.7+ — Weak-LLM MCP (Shipped)

**Design:** [docs/superpowers/specs/2026-07-01-assistant-weak-llm-improvements-design.md](docs/superpowers/specs/2026-07-01-assistant-weak-llm-improvements-design.md)  
**Plan:** [docs/superpowers/plans/2026-07-01-0.21.7-weak-llm-mcp.md](docs/superpowers/plans/2026-07-01-0.21.7-weak-llm-mcp.md)

| Release | Theme | Status |
|---------|-------|--------|
| 0.21.7 | Hotfixes: MCP boot, null params, bare `palm_assist` | ✅ Shipped |
| 0.21.8 | Collection `add` + `value` one-shot | ✅ Shipped |
| 0.21.9 | `format=assistant` on flows mutations + collection `actions` | ✅ Shipped |
| 0.21.10 | Unified `palm_assist` for flows driving | ✅ Shipped |
| 0.21.11 | Edit shortcuts, fuzzy menu, priority intent | ✅ Shipped |
| 0.21.12 | Weak-LLM playbook + conversation replay harness | ✅ Shipped |

| 0.22.0 | Agent skill MCP resources, `docs/mcp.txt` operator guide, Docker docs | ✅ Shipped |
| 0.22.1 | Mutation envelope protocol (`mutation.mutations_allowed`) | ✅ Shipped |
| 0.23.0 | `input_token` strict mode (`PALM_MCP_REQUIRE_INPUT_TOKEN`) | ✅ Shipped |
| 0.23.1 | Inspect-only non-terminal catalog (`operator-entry/inspect`) | ✅ Shipped |

**0.23 deferred:** `palm-compose-guide` scenario, process handoff, `create_params` mapping, WebSocket assist stream.

**0.23.2 prep (local):** mutation gate cleanup committed — single `FlowSession.input` choke point, `MutationRejectedError`; not released until requested.

## 0.24 — Definition Revisioning & Migration (vision)

**Vision:** [docs/VISION-0.24.md](docs/VISION-0.24.md)  
**Design:** [docs/superpowers/specs/2026-07-03-definition-revisioning-design.md](docs/superpowers/specs/2026-07-03-definition-revisioning-design.md)  
**ADR:** [docs/adr/007-definition-revisioning.md](docs/adr/007-definition-revisioning.md)  
**Plan:** [docs/superpowers/plans/2026-07-03-definition-revisioning.md](docs/superpowers/plans/2026-07-03-definition-revisioning.md)

| Component | Status |
|-----------|--------|
| Vision + spec + ADR (0.24 design release) | ✅ Documented |
| Flow revisioning (`publish_flow_revision`, instance `flow_revision`) | ✅ 0.24.1 (0.25.0) |
| Migration rules + impact query | ✅ 0.24.2 (0.25.0) |
| Migration execution hooks + demo flow | ✅ 0.25.0 |
| Documentation + MCP surface cleanup | ✅ 0.24.4 (0.25.0) |
| **Design Service** | ✅ 0.25.0 — propose/validate/impact/commit + auto-migrate |

**Release:** [RELEASE-0.25.0.md](RELEASE-0.25.0.md) · **Migration:** [MIGRATION-0.24.md](MIGRATION-0.24.md) · [MIGRATION-0.25.md](MIGRATION-0.25.md)

### 0.25.1–0.26.0 (shipped locally)

| Phase | Theme | Status |
|-------|-------|--------|
| 0.25.2–0.25.5 | Correctness, structure, contributors | ✅ Shipped |
| 0.25.6 | Dogfooding demo | ✅ Shipped |
| 0.25.7 | Design CQRS transport | ✅ Shipped |
| 0.25.8 | Registry-driven design dispatch | ✅ Shipped |
| 0.25.9–0.25.12 | Service CQRS contributors + bus parity | ✅ Shipped ([ADR-009](docs/adr/009-service-cqrs-contributors.md)) |
| 0.25.13 | Docs sync (AGENTS, MCP, STATUS) | ✅ Shipped |
| **0.26.0** | PyPI cut + CHANGELOG + MCP guides | ✅ Shipped |

**Plan:** [docs/superpowers/plans/2026-07-08-cqrs-bus-parity-and-0.26.md](docs/superpowers/plans/2026-07-08-cqrs-bus-parity-and-0.26.md)

## 0.27 — Compositional Design Parity (planned)

**Vision:** [docs/VISION-0.27.md](docs/VISION-0.27.md)  
**ADR:** [docs/adr/010-prompt-state-interpolation.md](docs/adr/010-prompt-state-interpolation.md)  
**Plan:** [docs/superpowers/plans/2026-07-08-compositional-design-parity-0.27.md](docs/superpowers/plans/2026-07-08-compositional-design-parity-0.27.md)  
**Reference flow:** `coconut-npc` ([examples/definitions/coconut_npc.py](examples/definitions/coconut_npc.py))

| Phase | Theme | Status |
|-------|-------|--------|
| 0.27.0 | Design transform schema parity + `coconut-npc` example | ✅ Shipped |
| 0.27.1 | Wizard prompt `{{ state.* }}` interpolation (ADR-010) | ✅ Shipped |
| 0.27.2 | Design service: `propose_resource` | ✅ Shipped |
| 0.27.3 | Resource doctor preflight + step failure modes | ✅ Shipped |
| 0.27.4 | Branching playbook MCP reference | ✅ Shipped |

## 0.28 — Local Document Resources (shipped)

**Vision:** [docs/VISION-0.28.md](docs/VISION-0.28.md)  
**Design:** [docs/superpowers/specs/2026-07-08-document-kv-providers-design.md](docs/superpowers/specs/2026-07-08-document-kv-providers-design.md)  
**Plan:** [docs/superpowers/plans/2026-07-08-document-kv-providers-0.28.md](docs/superpowers/plans/2026-07-08-document-kv-providers-0.28.md)

| Phase | Theme | Status |
|-------|-------|--------|
| 0.28.0 | `kv` resource provider (memory + auto/storage) | ✅ Shipped |
| 0.28.1 | `file` document provider | ✅ Shipped |
| 0.28.2 | Coconut cross-session persistence (`player_name`) | ✅ Shipped |
| 0.28.3 | Design contributors + doctor + docs | ✅ Shipped |

## 0.29 — Tiered KV (shipped)

| Phase | Theme | Status |
|-------|-------|--------|
| 0.29.0 | `backend: tiered` hot/cold KV with LRU eviction | ✅ Shipped |

## Priorities & Next Steps

**0.28** — local document/KV resource providers (shipped). **0.29** — tiered KV for RAM-constrained hosts (shipped).

### 0.30 — Assist Design Entry (active)

**Vision:** [docs/VISION-0.30.md](docs/VISION-0.30.md)  
**Design:** [docs/superpowers/specs/2026-07-08-assist-design-entry-design.md](docs/superpowers/specs/2026-07-08-assist-design-entry-design.md)  
**Plan:** [docs/superpowers/plans/2026-07-08-assist-design-entry-0.30.md](docs/superpowers/plans/2026-07-08-assist-design-entry-0.30.md)

| Phase | Theme | Status |
|-------|-------|--------|
| 0.30.0 | Vision + design + plan + STATUS/AGENTS (docs-only) | ✅ Documented |
| 0.30.1 | Pipeline action-merge + intent visibility + operator-entry design CTAs | ✅ Shipped |
| 0.30.2 | `design-entry` assist scenario shell | ✅ Shipped |
| 0.30.3 | Handoff polish; `kind: design` + post-terminal CTAs | ✅ Shipped |
| 0.30.4 | Weak-LLM: `palm_design_publish_flow` one-shot + compact design CTAs | ✅ Shipped |
| 0.30.5 | Skip design summary confirm; `palm_assist(params={body})` → publish | ✅ Shipped |
| 0.30.6 | Flow usage + resources: assistant flows, coconut entry, resource CTAs | ✅ Shipped |
| **0.30.7** | **PyPI/GitHub bundle** of 0.27–0.30.6 (from last cut 0.26.0) | ✅ Release |
| 0.30.8 | Terminal complete blurb + lean Send answer / Run again CTAs | ✅ Shipped |

**Boundaries:** Assist discovers and guides; Design Service owns propose → impact → commit. Bare `palm_assist()` remains operator-entry; design is a sibling intent/scenario.

### 0.31 — MCP Meta-Surface (active, open-ended)

**Vision:** [docs/VISION-0.31.md](docs/VISION-0.31.md)  
**Design:** [docs/superpowers/specs/2026-07-08-mcp-meta-surface-design.md](docs/superpowers/specs/2026-07-08-mcp-meta-surface-design.md)  
**Plan:** [docs/superpowers/plans/2026-07-08-mcp-meta-surface-0.31.md](docs/superpowers/plans/2026-07-08-mcp-meta-surface-0.31.md)

| Phase | Theme | Status |
|-------|-------|--------|
| 0.31.0 | Vision + design + open ladder (docs-only) | ✅ Documented |
| 0.31.1 | `PALM_MCP_SURFACE` profiles + catalog inventory | ✅ Shipped |
| 0.31.2 | Assist-complete happy paths (assist-only dogfood) | ✅ Shipped |
| 0.31.3 | Progressive docs (L0/L1/L2) + publish CTAs → palm_assist | ✅ Shipped |
| 0.31.4 | `assist/discover` (no second tool) + docs/AGENTS refresh | ✅ Shipped |
| **0.31.5** | **PyPI/GitHub bundle** of 0.30.8 + 0.31.0–0.31.4 | ✅ Release |
| 0.31.6+ | Open field (Code Mode, host gateways, size logging, …) | ⬜ Open |

**Theme:** Progressive disclosure — thin host tool catalog; `palm_assist` as meta-execute; measure catalog/turn size. Default surface stays **full** until assist-only is proven.

### 0.32 — WebSocket Assist & Portal Backend (active, open-ended)

**Vision:** [docs/VISION-0.32.md](docs/VISION-0.32.md)  
**Design:** [docs/superpowers/specs/2026-07-09-websocket-assist-portal-design.md](docs/superpowers/specs/2026-07-09-websocket-assist-portal-design.md)  
**Plan:** [docs/superpowers/plans/2026-07-09-websocket-assist-portal-0.32.md](docs/superpowers/plans/2026-07-09-websocket-assist-portal-0.32.md)

| Phase | Theme | Status |
|-------|-------|--------|
| 0.32.0 | Vision + protocol draft + Portal arc (docs-only) | ✅ Documented |
| 0.32.1 | Real WebSocket transport MVP (hello/ping on `/ws/v1/assist`) | ✅ Shipped |
| 0.32.2 | Assist channel (dispatch ↔ turn frames) | ✅ Shipped |
| 0.32.3 | Input schema on turns + bind/reconnect + auth mode | ✅ Shipped |
| 0.32.4 | Portal dogfood chat shell (`/portal/`) | ✅ Shipped |
| 0.32.5 | Human-first dogfood (auto-start demos, summary no→back, action hygiene) | ✅ Shipped |
| 0.32.6 | Portal first-turn fix (input schema no longer clobbers assist turns) | ✅ Shipped |
| 0.32.7 | Portal auto-open operator-entry + correct bind after auto-start | ✅ Shipped |
| 0.32.8 | Auto-continue introduction steps (land on real work) | ✅ Shipped |
| 0.32.9 | Optional field Skip + schema required fix + finish blurb | ✅ Shipped |
| 0.32.10 | Portal UX: split intro/menu bubbles, themed scroll, pending state | ✅ Shipped |
| 0.32.11+ | Open (edit UX, events, PWA, Android, …) | ⬜ Open |

**Theme:** Human real-time transport for Assist — same meta-dispatch as MCP — toward floating **Portal** PWA and later mobile assistant. WS live on `/ws/v1/assist`; Portal dogfood at `/portal/`.

**Also tracked:** [weak-LLM deferred](docs/superpowers/specs/2026-07-01-assistant-weak-llm-improvements-design.md) — `palm-compose-guide`, process handoff · **0.23.2** mutation gate (local). WebSocket assist stream **moves into 0.32**.


## Useful Links

- [CHANGELOG.md](CHANGELOG.md)
- [EXPLORER-WIZARD.md](EXPLORER-WIZARD.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [AGENTS.md](AGENTS.md)
- [DEVELOPMENT.md](DEVELOPMENT.md)
- [docs/MCP.md](docs/MCP.md) — agent development with Palm MCP
- [RELEASE-0.16.5.md](RELEASE-0.16.5.md) — release checklist
- [MIGRATION-0.16.md](MIGRATION-0.16.md) — upgrade from 0.15.x
- [MIGRATION-0.24.md](MIGRATION-0.24.md) — definition revisioning & instance migration (0.24+)
- [MIGRATION-0.25.md](MIGRATION-0.25.md) — Design Service operator workflow (0.25+)
- [RELEASE-0.25.0.md](RELEASE-0.25.0.md) — 0.25.0 release checklist
- Examples: `examples/README.md`

## How to Contribute

Follow the guidance in [DEVELOPMENT.md](DEVELOPMENT.md) and [AGENTS.md](AGENTS.md).  
All significant architectural changes should be accompanied by an ADR and documentation updates.