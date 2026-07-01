# Changelog

All notable changes to Palm are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.21.6] — 2026-07-01

**0.21 release complete** — migration guide, agent docs, verification.

### Added

- **`MIGRATION-0.21.md`** — CLI/Explorer entry, `actions` block, flows `format=assistant` opt-in
- **`RELEASE-0.21.6.md`** — release checklist and verify commands

### Changed

- **`docs/MCP.md`**, **`docs/llms.txt`**, **`AGENTS.md`** — 0.21 human surfaces and flows opt-in documented
- **`MIGRATION-0.20.md`** — cross-link to 0.21 shipped features
- **Version** `0.21.6` on documentation surfaces

## [0.21.5] — 2026-07-01

**Flows assistant opt-in** — human envelope on business sessions without changing defaults.

### Added

- **`palm_flows_session(format="assistant")`** — opt-in assistant envelope (`question`, `choices`, `hint`)
- **Flows REST** `?format=assistant|powertool|verbose` on session inspect routes

### Changed

- **`palm_flows_session`** default `format` is `powertool` (`compact` alias retained)
- **`shape_dispatch_result`** flows branch delegates to `shape_flow_session_view` when `params.format=assistant`
- **`palm_assist`** on flows session paths respects `params.format=assistant` (tool-level `format` alone still powertool)

## [0.21.4] — 2026-07-01

**Assistant envelope depth** — `actions` block and production enrichers.

### Added

- **`actions` block** — progressive disclosure from `next_commands` (`label`, `path`, `alias`)
- **`AssistContributor.assistant_enricher`** — auto-registers on `register_assist_contributor`
- **Operator-entry enricher** — handoff CTA in `examples/definitions/operator_entry.py`
- **REST** `GET /v1/api/assist/catalog/flows` — parity with assist dispatch command

### Changed

- **`AssistSessionContext.to_dict`** — includes `actions` on `format=assistant`

## [0.21.3] — 2026-07-01

**Explorer assist HTMX** — interactive session verbs in the browser.

### Added

- **POST** `/explorer/assist/session/{id}/input|backtrack|cancel|handoff` — HTMX partial updates on `#assist-workspace`
- **`assist_input_form`**, **`assist_handoff_form`**, **`assist_session_toolbar`** — choice buttons + text input
- **`assist_handoff_result`** — handoff card with link to flows submit

### Changed

- **`assist_workspace`** — interactive forms replace read-only 0.21.2 placeholder

## [0.21.2] — 2026-07-01

**Explorer assist panel** — catalog, start, and assistant workspace.

### Added

- **`/explorer/assist`** — scenario catalog and detail pages
- **`assist_workspace`** — SSR consumer of assistant envelope (`question`, `choices`, `compose`)
- **`ExplorerFetcher`** assist methods — `list_assist_scenarios`, `start_assist_scenario`, `get_assist_session`
- **Tests** — `tests/test_explorer_assist_ssr.py`

### Changed

- **Explorer nav** — Assist entry in sidebar and overview link card

## [0.21.1] — 2026-07-01

**CLI assist commands** — REPL consumes 0.20 assistant envelope.

### Added

- **`assist list|start|input|handoff|status|cancel`** — CLI commands via `host.assist`
- **`render_assistant_panel`** — Rich panel for `question`, `choices`, `hint`, `handoff_ready`
- **`dispatch_repl_line`** — plain REPL input routes to assist when session active
- **`CliContext.active_assist_session_id`** — assist session tracking
- **Tests** — `tests/test_cli_assist.py`

### Changed

- **REPL welcome** — recommends `assist start operator-entry`
- **`help`** — assist command section

## [0.21.0] — 2026-07-01

**Design** — Assistant expansion: human surfaces + envelope depth (implementation 0.21.1–0.21.6).

### Added

- **Spec** — [docs/superpowers/specs/2026-07-01-assistant-expansion-design.md](docs/superpowers/specs/2026-07-01-assistant-expansion-design.md): CLI `assist *` commands, Explorer `/explorer/assist` panel, `actions` block, opt-in flows `format=assistant`

## [0.20.5] — 2026-07-01

**0.20 release complete** — migration guide, agent docs, verification.

### Added

- **`MIGRATION-0.20.md`** — assistant vs powertool migration for assist surfaces
- **`RELEASE-0.20.5.md`** — release checklist and verify commands

### Changed

- **`docs/llms.txt`** — 0.20.5 agent rules (two view modes, typical session examples)
- **`docs/MCP.md`** — `palm_assist` `format` param; link to `MIGRATION-0.20.md`
- **`AGENTS.md`** — assistant/powertool conventions for MCP operators

## [0.20.4] — 2026-07-01

**`palm_assist` format default** — assistant on assist paths; powertool on flows/system.

### Added

- **`palm_assist` `format` param** — default `assistant`; `powertool` / `verbose` opt-in
- **`shape_dispatch_result`** + **`resolve_dispatch_format`** in assist MCP dispatch

### Changed

- Flows/system paths dispatched via `palm_assist` remain **powertool** regardless of tool default
- REST assist dispatch forwards `format` query param when set

## [0.20.3] — 2026-07-01

**Assist session defaults** — assistant envelope on service + REST; start returns first turn.

### Changed

- **`AssistSessionContext.to_dict`** — defaults to `format=assistant`; `verbose` and `powertool` opt-in
- **`start_scenario`** — returns first assistant turn (question + choices), not ids-only
- **REST assist handlers** — `?format=assistant|powertool|verbose` on session routes
- **MCP assist dispatch** — passthrough assistant envelopes (`question` field)

## [0.20.2] — 2026-07-01

**Assistant views** — compose + humanize pipeline registered from assist domain.

### Added

- **`palm/services/assist/views.py`** — `build_assistant_view`, compose-always pipeline, humanized envelope
- **`register_assistant_enricher`** on assist registry — per-scenario post-humanize hooks
- **`OperatorViewContext.handoff_ready`** — assist handoff shaping
- **Tests** — `tests/test_assistant_view.py`

### Changed

- **`AssistService`** — registers `assistant` view builder at construction

## [0.20.1] — 2026-07-01

**Operator view registry** — thin format dispatch in common; powertool registered by default.

### Added

- **`palm/common/operator/view_registry.py`** — `OperatorViewContext`, `register_operator_view_builder`, `build_operator_view`, `compact` → `powertool` alias
- **Tests** — `tests/test_operator_view_registry.py`

## [0.20.0] — 2026-07-01

**Design** — Assistant vs Powertool operator view split (implementation 0.20.1–0.20.5).

### Added

- **Spec** — [docs/superpowers/specs/2026-07-01-assistant-powertool-views-design.md](docs/superpowers/specs/2026-07-01-assistant-powertool-views-design.md): assistant (compose + human) default on assist surfaces; powertool (today's compact) on flows/system; thin `view_registry` in common

## [0.19.1] — 2026-07-01

**Bugfix** — `palm_assist` compact shaping for in-process flow session dispatch.

### Fixed

- **`compact_dispatch_result`** — coerce `SessionContext` dataclass results to dicts before compact branching so `palm_assist` flow session inspect/input returns slim operator snapshots (not verbose `result` blobs)

## [0.19.0] — 2026-07-01

**Stable MCP proxy** — single `palm_assist` dispatch tool for agent config stability.

Migration: [MIGRATION-0.19.md](MIGRATION-0.19.md) · Vision: [docs/VISION-0.18-ASSIST.md](docs/VISION-0.18-ASSIST.md)

### Added

- **`palm_assist`** MCP tool — parametric `path` / `alias` / `params` dispatch
- **`palm://assist/routes`** — generated command-path catalog + contributor aliases
- **`mcp_aliases`** on `AssistContributor` — stable alias map (`operator-entry/start`, etc.)
- **`assist_dispatch`** on in-process and REST MCP backends
- **Tests** — `test_palm_assist_tool.py`, `test_assist_mcp_aliases.py`

### Changed

- **`docs/MCP.md`**, **`docs/llms.txt`** — document `palm_assist` operator loop
- Per-domain MCP tools (`palm_flows_*`, …) **unchanged** — migration optional

## [0.18.0] — 2026-07-01

**Assist domain MVP** — fifth service for conversational operator guidance and handoff.

Migration: [MIGRATION-0.18.md](MIGRATION-0.18.md) · Vision: [docs/VISION-0.18-ASSIST.md](docs/VISION-0.18-ASSIST.md)

### Added

- **`palm/services/assist/`** — `AssistService`, `AssistSession`, command registry, grammar
- **`host.assist`** — wired on `ApplicationHost` and `ServerContext`
- **REST `/v1/api/assist/…`** — scenarios, session verbs, doctor shortcut, handoff
- **`palm-operator-entry`** — assist catalog scenario (`examples/definitions/operator_entry.py`)
- **`palm/app/assist_registry.py`** — app-level assist contributor registry
- **OpenAPI Assist group** — `openapi_registry.py` aggregates assist routes
- **Tests** — `test_assist_*`, `test_operator_entry_flow.py`

### Changed

- **`INSTALLED_SERVICES`** — includes `"assist"`
- **`STATUS.md`**, **`docs/MCP.md`**, **`docs/llms.txt`**, **`AGENTS.md`** — assist surface documented
- **ADR-006** — status Accepted

### Notes

- MCP unchanged in 0.18; stable `palm_assist` proxy deferred to 0.19
- Assist wizards support existing `step_kind: resource` compositional steps

## [0.17.3] — 2026-07-01

**OpenAPI from service registries** — `/v1/openapi.json` and `/v1/docs` document the full `/v1/api/…` surface.

Migration: [MIGRATION-0.17.md](MIGRATION-0.17.md) · Plan: [docs/superpowers/plans/2026-07-01-0.17-service-completion.md](docs/superpowers/plans/2026-07-01-0.17-service-completion.md)

### Added

- **`openapi_registry.py`** — aggregates per-service `ROUTES` into `RouteDefinition` metadata
- **`tests/test_openapi_registry.py`**

### Changed

- **`openapi.py`**, **`docs.py`**, **`doc_examples.py`** — full service-domain route catalog
- **`routes.py`** — registers meta routes only; service routes remain on `service_routes.py`
- **`ARCHITECTURE.md`** — REST/OpenAPI layout note

### Fixed

- OpenAPI/HTML docs no longer meta-only after 0.17 monolith route removal

## [0.17.2] — 2026-07-01

**Palm provider remote alignment** — compositional remote client uses `/v1/api/…` only.

Migration: [MIGRATION-0.17.md](MIGRATION-0.17.md)

### Changed

- **`submit_flow_remote`** → `POST /v1/api/flows/{flow_id}/create`
- **`get_job_remote`** → `GET /v1/api/system/jobs/{job_id}`
- **`submit_process_remote`** → `/v1/api/processes/{process_id}/prepare` + `/submit`
- **`remote_job_payload`** — maps `session_id` to `instance_id`

### Documentation

- **`docs/PROVIDER-APPS.md`** — remote binding path table

## [0.17.1] — 2026-07-01

**Process execution service** — multi-flow runs under `/v1/api/processes/…`; legacy `/v1/plans` removed.

Migration: [MIGRATION-0.17.md](MIGRATION-0.17.md)

### Added

- **`ProcessExecutionService`** — `prepare`, `submit`, `run`, `dispatch` with command-path grammar
- **REST** — `POST /v1/api/processes/{process_id}/prepare`, `/submit`, `/run`
- **Registry** — `process_commands()` in `execution/processes/registry.py`

### Changed

- **`PalmRestClient`** / in-process MCP — plan staging via `/v1/api/processes/…`
- **`ServerContext`** — wires `ProcessExecutionService` with runtime for submit idle sync

### Removed (breaking)

- **`POST /v1/plans/prepare`**, **`POST /v1/plans/submit`** monolith routes

## [0.17.0] — 2026-07-01

**System REST parity** — observe/lifecycle HTTP under `/v1/api/system/…`; legacy monolith job/instance/snapshot routes removed.

Migration: [MIGRATION-0.17.md](MIGRATION-0.17.md) · Plan: [docs/superpowers/plans/2026-07-01-0.17-service-completion.md](docs/superpowers/plans/2026-07-01-0.17-service-completion.md)

### Added

- **System REST** — `inspect_job`, `cancel_job`, `list_instances`, `inspect_instance`, `instance_tree`, snapshots, `resume_instance` on `/v1/api/system/…`
- **`tests/test_system_service_routes.py`**, **`tests/test_rest_system_routes.py`**

### Changed

- **`PalmRestClient`** — waiting jobs, job context, cancel, tree, snapshots → `/v1/api/system/…`; `provide_job_input` delegates to flows session input
- **`job_context.next_actions`** — flows session input + system instance/job paths
- Wizard read model and invoke tree links → system service paths
- Explorer SSR copy and doc examples updated

### Removed (breaking)

- **`GET/POST /v1/jobs`** monolith routes (submit → `/v1/api/flows/{flow_id}/create`; input → flows session)
- **`/v1/instances`**, **`/v1/snapshots`** monolith routes

## [0.16.5] — 2026-07-01

**Services are the API** — domain services in `palm/services/`, per-service REST under `/v1/api/…`, MCP remounted by service domain. Breaking release for integrators on legacy `/v1/wizards` and monolithic MCP tool names.

Vision: [docs/VISION-0.16.md](docs/VISION-0.16.md) · ADR: [docs/adr/005-service-domain-api.md](docs/adr/005-service-domain-api.md) · Migration: [MIGRATION-0.16.md](MIGRATION-0.16.md) · MCP: [docs/MCP.md](docs/MCP.md)

### Added

- **`palm/services/`** — `definitions`, `execution/flows`, `execution/providers`, `system` with per-domain `registry.py` and `dispatch()` command-path grammar
- **REST `/v1/api/…`** — definitions catalog + CRUD, flow session REPL, provider invoke, system doctor/jobs
- **MCP per-domain tools** — `palm_flows_*`, `palm_system_*`, `palm_definitions_*`, `palm_providers_invoke` (26 tools total with pattern contributors)
- **`ProviderExecutionService`** — `host.execution.providers.invoke()` with provider validation
- **Definitions CRUD** — `POST/PUT/DELETE` on `/v1/api/definitions/{flows,processes,resources}/…`
- **`FlowSession` / `SessionContext`** — service-layer session handles; `session_id` terminology at API boundary

### Changed

- **`host.internal`** → **`host.system`** (`SystemService`)
- **`host.execution.on(id)`** → **`host.execution.flows`** session API (`dispatch`, `FlowSession`)
- Explorer SSR and operator hints updated to `/v1/api/flows/…` and `palm_flows_*` tool names
- MCP prompts and `docs/llms.txt` agent guide rewritten for 0.16 conventions

### Removed (breaking — no deprecation window)

- **`/v1/wizards`** REST surface and `handlers/wizard.py`
- Legacy catalog routes (`/v1/flows`, `/v1/processes`, `/v1/resources`, `/v1/doctor`, `/v1/flows/validate`)
- **`POST /v1/resources/invoke`** — replaced by `/v1/api/providers/{provider}/{resource_ref}/invoke`
- Orphaned monolith handlers `handlers/catalog.py`, `handlers/resources.py`
- Monolithic MCP tools (`palm_submit_wizard`, `palm_inspect_instance`, `palm_wizard_input`, `palm_doctor`, …)

### Transitional (at 0.16.5 ship; removed in 0.17.0)

- `/v1/jobs`, `/v1/instances`, `/v1/snapshots` — migrated to `/v1/api/system` in **0.17.0**
- `/v1/plans` — remains until **0.17.1**

## [0.15.4] — 2026-06-30

**Service layer release** — CQRS schemas, `palm.common.services`, in-process MCP, REST schema dedupe, and legacy cleanup. PyPI packages the full 0.15 track (internal milestones 0.15.1–0.15.3 on master).

Vision: [docs/VISION-0.15.md](docs/VISION-0.15.md) · ADR: [docs/adr/004-cqrs-schemas-service-layer.md](docs/adr/004-cqrs-schemas-service-layer.md) · MCP: [docs/MCP.md](docs/MCP.md)

### Added

- **`CqrsSchemaRegistry`** — `DictStateSchema` per command/query; patterns contribute via `CqrsContributor.command_schemas` / `query_schemas`
- **Service layer** (`palm/common/services/`) — `InternalService`, `DefinitionService`, `ExecutionService`, `InstanceSession`, `ReplSession`, `BaseService` with schema-validated dispatch
- **Instance-centric API** — `host.execution.on(instance_id).input("yes")`; `ReplSession` for CLI REPL
- **`PalmInProcessBackend`** — MCP tools call services on `ServerContext` when `PALM_MCP_IN_PROCESS=1` (default in `.grok/config.toml`)
- **`rest/schema_bridge.py`** — REST input bodies projected from `CqrsSchemaRegistry`
- **`ServerContext.schemas`** — registry exposed for REST handlers
- **Docs** — `docs/VISION-0.15.md`, ADR 004, cleanup track specs/plans under `docs/superpowers/`

### Changed

- REST inspect/catalog/wizard writes delegate to services (thin handlers)
- MCP local mode avoids HTTP round-trip when in-process
- REST `provide_input` / wizard input validation uses registry (single source of truth)
- Definition views imported from `palm.common.services.views` (serializer shim trimmed)
- Ruff import hygiene across `src/` and `tests/`; wizard packages exempt from isort (`I001`) for circular-import safety

### Removed (experimental — no deprecation window)

- `create_cli_app()` — use `create_cli_host()`
- `interactive_runtime` wizard aliases (`resolve_wizard_job`, `provide_wizard_input_for_instance`, …)
- `ChildWizardCompletionHook` — use `ChildCompletionHook`
- `serializers.py` re-exports of `views.py` helpers (snapshot serializers remain)
- `ssr/explorer/collection_input.py` shim

## [0.14.9] — 2026-06-26

**MCP Operator release** — `palm-mcp` adapter for coding agents: 26 tools, 4 prompts, 10 resources; stdio + native HTTP transports; agent-oriented docs.

Guide: [docs/MCP.md](docs/MCP.md) · Agent context: [docs/llms.txt](docs/llms.txt) (`palm://agent/guide`)

### Added

- **`palm-mcp` stdio server** — FastMCP adapter proxying to Palm REST (`PALM_BASE_URL`); install via `pip install "palmengine[mcp]"` or `uv sync --extra mcp`
- **26 MCP tools** — operator loop (`palm_inspect_instance`, `palm_wizard_input`, `palm_resume_child_wait`, …), lifecycle (`palm_submit_wizard`, `palm_cancel_job`, `palm_invoke_resource`, …), debug (`palm_doctor`, `palm_trace_events`, `palm_validate_flow`, …)
- **10 MCP resources** — `palm://agent/guide`, `palm://definitions/*`, `palm://instances/{id}/tree`, `palm://openapi`, `palm://server/health`
- **4 MCP prompts** — `debug-wizard-block`, `drive-wizard-to-step`, `explain-compositional-stack`, `operator-handoff`
- **Pattern MCP contributors** — `register_mcp_contributor()` in `palm/patterns/_registry.py`; wizard (`palm_wizard_collection_action`, `palm_wizard_commit_preview`), parallel (`palm_parallel_branch_status`), pipeline (`palm_pipeline_step_trace`)
- **App MCP contributors** — `register_app_mcp_contributor()` in `palm/app/mcp_registry.py` for downstream apps
- **Native HTTP MCP** — streamable HTTP at `POST /mcp` and SSE at `/mcp/sse` + `/mcp/messages` when `mcp` extra installed; discovery via `GET /v1/surfaces/mcp`
- **REST endpoints for MCP** — `POST /v1/wizards/{id}/resume-child-wait`, `resume-wizard-tick`; `GET /v1/instances/{id}/tree`; `POST /v1/jobs/{id}/cancel`; `POST /v1/flows/validate`; `GET /v1/doctor`; resource catalog `GET /v1/resources`, `GET /v1/resources/{ref}`
- **`palm/common/operator/`** — `compact_wizard_inspect()`, `compact_job_inspect()`, `build_invoke_tree()`, `resolve_mcp_wizard_input()` (plain-string coercion), `enrich_job_list_rows()`, `slim_waiting_job_row()`, `build_doctor_report()`, snapshot diff helpers
- **`palm_invoke_resource`, `palm_compose_status`** — resource invoke and compositional session summary tools
- **Grok project config** — [`.grok/config.toml`](.grok/config.toml) registers `palm-mcp` stdio for this repo
- **Just recipes** — `just mcp-sync`, `just mcp-inspector`
- **Tests** — `tests/test_mcp_tools.py`, `test_mcp_phase3.py`, `test_mcp_phase4.py`, `test_mcp_phase5.py`, `test_mcp_http_surface.py`, `test_mcp_registry.py`, `test_operator_waiting_jobs.py`, `test_server_list_jobs_enrichment.py`
- **Documentation** — [docs/MCP.md](docs/MCP.md) agent development guide; MCP sections in README, DEVELOPMENT, AGENTS, STATUS, `docs/llms.txt`

### Changed

- **MCP module split** — `src/palm/runtimes/mcp/tools.py`, `resources.py` extracted from monolithic `server.py`
- **Plain-string wizard input** — `palm_wizard_input` and `palm_provide_job_input` prefer `input="yes"` over JSON `value`; coercion matches Explorer forms
- **`GET /v1/flows`** — list includes `step_slugs` for wizard flows; `GET /v1/flows/{id}?verbose=0` returns slim summary
- **`GET /v1/jobs`** — enriches rows with `instance_id`, `pattern`, `flow`, `step` from metadata and instance manager
- **`palm_list_waiting`** — never aliases `job_id` as `instance_id`; omits `instance_id` when unknown

### Developer notes

- **Agent conventions:** instance-first (`instance_id`); plain `input` strings; resources = read, tools = write; `palm_resume_child_wait` when `waiting_for_child`
- **Operator loop:** definitions → submit → inspect → input → wait on children → resume
- **Prerequisite:** `palm server` on `:8080` before connecting MCP stdio
- **MCP Inspector:** `just mcp-inspector` for interactive tool testing

## [0.13.13] — 2026-06-25

**Provider apps + compositional follow-ups** — PatternApp alignment, ProviderApp framework, remote resource invoke, REST HTTP bindings.

### Added

- **[docs/PATTERN-APPS.md](docs/PATTERN-APPS.md)** — canonical guide for PatternApp manifests, `bindings/`/`flow/` layout, and `palm.common` boundaries
- **[docs/PROVIDER-APPS.md](docs/PROVIDER-APPS.md)** — canonical guide for ProviderApp manifests and provider `bindings/`/`flow/` layout
- **ADR-002** — [docs/adr/002-pattern-apps-and-common-boundaries.md](docs/adr/002-pattern-apps-and-common-boundaries.md)
- **ADR-003** — [docs/adr/003-provider-apps.md](docs/adr/003-provider-apps.md)
- **`ProviderApp`** — Django-style manifest base in `palm/common/providers/app.py`; `providers/_registry.py` for app lifecycle, runtime binding, and runtime accessor hooks
- **`POST /v1/resources/invoke`** — REST endpoint for remote resource invocation (compositional palm provider remote mode)
- **`register_runtime_accessor`** — decouples `child_wait` and wizard bridges from palm-specific wiring imports
- **`tests/test_provider_boundary.py`** — AST enforcement for provider imports in `palm.common` and `palm.patterns`
- **`just guard-common`** — runs `test_common_boundary.py`, `test_provider_boundary.py`, and `test_modular_apps.py` (wired into `just check`)

### Changed

- **parallel** — reorganized into `bindings/` (definitions, instances, context, behavior_tree) and `flow/` (branch, scope, merge); `ParallelApp` manifest documents `palm_layers`
- **pipeline** — `bindings/definitions` + `bindings/behavior_tree`; enhanced `PipelineApp` manifest
- **dag, etl** — `bindings/definitions/builder.py` + `flow/` scaffold; honest `PatternApp` manifests
- **palm provider** — reorganized into `bindings/` (resource, orchestration, runtimes, recursion) and `flow/` (coordinator, params, target, remote); `PalmProviderApp` manifest; remote `invoke_resource` via `/v1/resources/invoke`
- **rest provider** — `bindings/resource` + `bindings/transport` with real HTTP fetch (stub fallback when `base_url` absent)
- **graphql, postgres** — minimal `ProviderApp` manifests
- **Documentation** — AGENTS, ARCHITECTURE, STATUS, `docs/index.html`, `docs/llms.txt` updated for PatternApp and ProviderApp models; stale path bans in `scripts/docs_check.py`

## [0.13.0] — 2026-06-18

**Wizard Experience release** — first-class `/v1/wizards` REST surface, HTMX-powered Explorer workspace, and rich collection-step UI.

Vision: [docs/VISION-0.13.md](docs/VISION-0.13.md) · Guide: [EXPLORER-WIZARD.md](EXPLORER-WIZARD.md) · Phases: [src/palm/patterns/wizard/MIGRATION-WIZARD-PHASES.md](src/palm/patterns/wizard/MIGRATION-WIZARD-PHASES.md)

### Added

- **`/v1/wizards` REST API** — `POST` submit, `GET` rich status, `POST` input, `POST` backtrack keyed by durable `instance_id`
- **`build_wizard_view()`** — instance-centric read model combining projections, job inspection, prompt, answers, and `next_actions`
- **CQRS** — `SubmitWizardCommand`, `ProvideWizardInputCommand`, `RequestWizardBacktrackCommand`, `GetWizardStatusQuery`
- **Palm Explorer wizard workspace** — HTMX partial updates at `/explorer/instances/{id}` with progress bar, prompt card, answers panel, step timeline, and backtrack controls
- **Collection step UI** — overview card, numbered item cards, add/edit/remove flows, field-phase draft panel, remove confirmation dialog
- **`collection_input.py`** — maps Explorer form actions to wizard `provide_input` values (including compound edit/remove)
- **Extended job inspection** — collection phase metadata (`collection_draft`, `collection_progress`, `item_fields`, …) flows into wizard `prompt`
- **Guide** — [EXPLORER-WIZARD.md](EXPLORER-WIZARD.md) for operators and integrators
- **Tests** — `tests/test_server_wizards.py`, Explorer wizard + collection HTMX coverage in `tests/test_server_ssr.py`

### Changed

- **Wizard phase modularization** — collection, input, summary, commit, resource, and transform phases live under `palm/patterns/wizard/phases/` with BT routing (`PhaseKeyedSelectorNode`, `PhaseTransitionLoopNode`)
- **`WizardPattern`** — slim orchestration surface; step logic owned by phase nodes
- **OpenAPI / `/v1/docs`** — wizard request examples for collection menu, field input, and continue actions
- **Documentation** — README “Try in Explorer”, ARCHITECTURE wizard Explorer section, `docs/index.html` and `docs/llms.txt` refreshed for 0.13

### Developer notes

- Explorer collection UI posts `collection_action` (+ optional `item_index`) to `/explorer/instances/{id}/input`; REST clients use `/v1/wizards/{id}/input` with wizard menu strings (`"Add a new item"`, etc.)
- HTMX targets `#wizard-workspace` with `outerHTML` swap; forms disable controls during flight via `hx-disabled-elt`

## [0.12.9] — 2026-06-17

**Compositional Power release** — Resources as first-class, declarative citizens; Palm calling Palm via the `palm` provider; Explorer resource hub.

Vision: [docs/VISION-0.12.md](docs/VISION-0.12.md) · Migration: [MIGRATION-0.12.md](MIGRATION-0.12.md) · ADR: [docs/adr/001-compositional-power-resources.md](docs/adr/001-compositional-power-resources.md)

### Added (Phase 1)

- **`ResourceDefinition`** — declarative resource contracts in `palm/definitions/resource.py`
- **`DefinitionRepository` resource CRUD** — register, save, get, list, delete with storage roundtrip
- **Bootstrap hydration** — resources loaded from storage alongside flows and processes
- **CLI** — `resource list`, `resource describe <ref>`; `palm doctor` and `process list` catalog show resources
- **Example** — `examples/definitions/fetch_customer.py`

### Added (Phase 2)

- **`ProviderResult`** — structured invoke outcomes (`success`, `data`, `error`, `metadata`)
- **`BaseProvider.invoke()`** — action-based contract; `describe()` and `health()` metadata
- **`ResourceEngine.invoke()`** — definition ref or direct provider; `{{ state.* }}` and `{param}` binding
- **Events** — `resource.invoked`, `resource.completed`, `resource.failed` via injected `EventEngine`
- **`palm/common/resource/`** — `resource_definition_resolver()` bridge (core purity preserved)
- **`PalmApp.invoke_resource()`** / **`ApplicationHost.invoke_resource()`**
- **CLI** — `resource invoke <ref> key=value ...` and direct `--provider` mode
- **Integration** — `WizardActionLeaf`, `enrich_resource` transform use engine invoke path

### Added (Phase 3)

- **`ResourceLeaf`** — core BT leaf invoking `ResourceEngine` with trace + output keys
- **`WizardResourceLeaf`** — wizard `step_kind: resource` with answer promotion for state binding
- **Wizard config** — `resource_ref`, `params`, `output_key`, `action` on resource steps
- **Example flow** — `resource-customer-wizard` (input + `fetch-customer` resource step)
- **Events** — `wizard.resource.invoked`

### Added (Phase 4)

- **`palm` provider** — built-in compositional orchestration at `palm/providers/palm/`
- **Local mode** — `submit_flow`, `submit_process`, `invoke_resource`, `fetch` via bound runtime
- **Remote mode** — HTTP delegation to `ServerRuntime` (`POST /v1/jobs`, plans API for processes)
- **Recursion guardrails** — configurable depth limit and cycle detection via `contextvars`
- **Correlation metadata** — child jobs carry `__palm:parent_job_id`, `__palm:invoke_depth`, `__palm:invoke_chain`
- **Runtime wiring** — `BaseRuntime.start()` binds local runtime for in-process `palm` calls
- **Example** — `compositional-parent` wizard calling `ingest-etl` via `submit-ingest-etl` resource

### Changed (Phase B — resource cleanup)

- **Breaking:** removed wizard `step_kind: action` and `WizardActionLeaf`
- **Breaking:** resource steps require `resource_ref` (`resource_provider` / `resource_id` removed)
- Removed `resource_leaf_from_legacy_action()` compatibility helper
- **`ResourceLeaf`** — richer failure messages and trace (`resource_ref`, `action`, correlation fields)
- **`promote_binding_keys()`** — shared wizard answer promotion for param binding
- **Events** — `resource.completed` / `resource.failed` include correlation payload; dropped `wizard.resource.invoked`

See [MIGRATION-0.12.md](MIGRATION-0.12.md).

### Added (Phase C — future-proofing)

- **`palm/core/utils/recursion.py`** — reusable `recursion_frame()` depth/cycle guard
- **`ResourceCatalog`** — rich discovery (`describe`, provider actions, schemas)
- **Explorer** — `/explorer/resources` catalog and detail pages
- **`ResourceEngine` caching** — optional definition + read-result TTL caches (`PALM_RESOURCE_CACHE_*`)
- **`DefinitionRepository.find_resources()`** / `list_resources_by_provider()`
- **Examples** — expanded compositional demo (nesting + remote URL pattern)

### Added (Phase 5 — cross-cutting integration)

- **Compensation** — `register_for_resource()` undo handlers; `CompensationCoordinator` triggers on `resource.failed` and commit failure with tracked mutating invokes
- **`resource.compensated`** observability event when resource undo succeeds
- **`ResourceInvocationProjection`** — per-instance/job resource call timeline (`GetResourceInvocationsQuery`)
- **Explorer** — resource step timeline on instance detail pages
- **Wizard** — mutating invoke tracking (`RESOURCE_INVOCATIONS`); enriched `RESOURCE_FEEDBACK`
- **`enrich_resource`** — full `resource_ref` support with custom `action`, `params`, and state binding
- **Observability** — `JobExecutionContextHook` stamps execution correlation; `resource.*` events include job/instance/wizard/step metadata
- **`palm/core/resource/observability.py`** — core-safe correlation helpers

### Added (Phase 6 — release polish)

- **Explorer resources hub** — `/explorer/resources` catalog (filters, usage counts, invoke shortcuts); detail pages with action catalog, flow cross-refs, invocation timeline; **Try Invoke** form at `/explorer/resources/{id}/invoke`
- **Explorer integration** — resource steps on flow detail; resource invocations on job detail; overview stat + link card
- **Documentation** — `MIGRATION-0.12.md`, Resource Best Practices in README and ARCHITECTURE; `RELEASE-0.12.9.md` checklist
- **Quality** — `just docs-check` version surfaces; full test suite green at 0.12.9

## [0.11.8] — 2026-06-17

**Explorer polish release** — Palm Explorer becomes the living server hub; legacy wiki/docs paths redirect; flow submission UX refined.

### Added

- **Palm Explorer** — schema-driven SSR hub at `/explorer` for flows, jobs, instances, schemas, patterns, and processes
- **Explorer surface** — `ExplorerSurface` (`explorer`); `/v1/surfaces/explorer` and `/v1/surfaces/ssr` surface info endpoints
- **Flow submission UX** — registered-flow primary form, advanced test-wizard panel, **Start this flow** buttons, `?flow=` pre-fill on submit page
- **Instance browser** — browse and inspect durable process instances and snapshots from the hub
- **Root redirect** — `GET /` → `/explorer` (302); health payload includes `home`

### Changed

- **SSR layering** — `palm/common/runtimes/server/ssr/` stays thin (render + layout shell); Explorer implementation lives in `palm/runtimes/server/surfaces/ssr/explorer/`
- **Legacy paths** — `/wiki/*` and `/docs` redirect to `/explorer`; health keeps `wiki: "/explorer"` as deprecated alias
- **REST docs hub** — links to Palm Explorer alongside `/v1/docs` and OpenAPI

### Fixed

- **Explorer forms** — choice fields tolerate `choices: null` without crashing (`_normalize_choices`)

## [0.10.9] — 2026-06-16

**Architecture evolution release** — ApplicationHost becomes the primary orchestrator, CQRS read models power the CLI, and reliability primitives (outbox, compensation) ship for production-style deployments.

### Added

- **ApplicationHost** — top-level orchestrator with composable role profiles (`all_in_one`, `master`, `worker`, `server`), startup recovery, and coordinated shutdown
- **CQRS layer** (`palm.common.cqrs`) — `CommandBus` / `QueryBus`, handlers for submit/resume/input, and three projections:
  - `InstanceIndexProjection` — instance catalog read model
  - `WizardProgressProjection` — wizard step, backtrack trace, commit status
  - `JobStatusBoardProjection` — live job board for dashboards
- **Reliability** — transactional event outbox (`OutboxStore`, background drain), `CompensationCoordinator` for commit-failure undo, optional `WebhookDispatcher`
- **Projection rebuild safeguards** — configurable batch size, max instances, `skip_if_fresh` policy on startup
- **Status dashboard** — projection-backed Rich overview (`palm status` default):
  - Host health (roles, runtimes, outbox, recovery)
  - Instance counts, active wizards, job board, recent host events
  - `--full` detailed view, `-r` / `--refresh` live refresh in REPL/TTY
- **`palm host`** subcommand — blocking deployment roles via `run_host()` (`all-in-one`, `master`, `worker`, `server`)
- **`HostEventRecorder`** — ring buffer of recent host bus events for dashboards
- **CLI consolidation** — unified diagnostics routing (`status` / `doctor`), shared `instance resume`, backward-compatible aliases documented in help
- **Test performance** — `PalmSettings.for_tests()`, shared fixtures, `--fast` pytest mode, collapsed-runtime worker-ready fix (~33× faster suite)
- **Migration guide** — [MIGRATION-0.10.md](MIGRATION-0.10.md)

### Changed

- **CLI bootstrap** — `create_cli_host()` + `ApplicationHost` replace direct `PalmApp` wiring; collapsed profile runtime name `main`
- **`palm status`** — live dashboard by default; `status --full` is detailed dashboard; use `palm doctor` for full health report
- **`palm doctor`** — supports `--dashboard` (and `--full` / `-r` when combined with dashboard flags in REPL)
- **Worker coordination** — collapsed `all_in_one` hosts register embedded runtime as worker (no 5s startup timeout)
- **`examples/full_demo.py`** — rewritten for `ApplicationHost` + CQRS + resume across restart
- **Documentation** — README, ARCHITECTURE, DEVELOPMENT, examples README refreshed for 0.10 primary paths

### Removed

- **`PalmApp.bootstrap_cli()`** — use `ApplicationHost` / `create_cli_host()`
- **`CLI_RUNTIME_NAME`** constant
- **`palm/runtimes/cli/pkg/`** re-export shim

### Deprecated

- **`create_cli_app()`** — use `create_cli_host()`; returns `host.app` for legacy callers
- **Wizard-only CLI shortcuts** — `wizard start` / `wizard status` remain but `flow start` / `status` are preferred

### Fixed

- **Collapsed host startup** — `WorkerCoordinator` counts embedded runtime in `all_in_one` profile (eliminates spurious worker-ready timeout)
- **`palm host all-in-one`** — `HostProfile` import available at module level (fixes `NameError` on one-shot host command)

### Upgrade notes (0.9.x → 0.10.9)

| Before (0.9) | After (0.10.9) |
|--------------|----------------|
| `PalmApp.bootstrap_cli()` | `create_cli_host()` or `ApplicationHost(...).start()` |
| `app.submit_flow(...)` in services | `host.submit_flow(...)` or `host.execute(SubmitFlowCommand(...))` |
| `app.list_instances()` in CLI | `host.list_instance_views()` / query bus |
| `status --full` = doctor | `status --full` = detailed dashboard; `doctor` = health report |

See [MIGRATION-0.10.md](MIGRATION-0.10.md) for full migration steps.

## [0.9.7] — 2026-06-15

**Transform release** — declarative data shaping from core engine to wizard steps, plus security and reliability polish to close the 0.9 line.

### Added

- **TransformEngine** (`palm.core.transform`) — pure core engine with `TransformContext`, batch/chained pipelines, and scoped `BaseState` reads/writes with optional schema validation
- **Built-in transform rules** (`palm.common.transforms`) — **22 registered rules** with catalog descriptions for docs and `palm doctor`:
  - Field shaping: `rename_field`, `map_fields`, `filter_items`, `lookup`, `conditional`, `jsonpath_extract`, `jsonpath_set`, `calculate`, `string_format`
  - Dates: `date_format`, `date_parse`
  - Integration: `enrich_resource`, `callable`
  - Serialization: `json_load`/`json_dump`, `csv_load`/`csv_dump`, `yaml_load`/`yaml_dump`, `toml_load`, `xml_load`, `parquet_load` (stub for custom pyarrow rules)
- **Registration helpers** — `register_transform()`, `@transform_rule`, `TransformExecutor`, `apply_transform_to_state()`, autoload at bootstrap
- **Wizard `step_kind: transform`** — declarative transform steps between interactive prompts; promotes output to answers for summary and flow-schema validation; CLI shows `Applied transform: …`
- **TransformLeaf** — behavior-tree leaf for programmatic transform chains inside wizard trees
- **Examples** — `transform-example` (wizard transform steps), `transform-shaping` (calculate / lookup / conditional pipeline), `transform-formats` (json → csv ETL-style demo)
- **`palm doctor`** — transform registry table with per-rule catalog descriptions

### Changed

- **Documentation** — README, ARCHITECTURE, examples, and website refreshed for transforms and 0.9.7 capabilities
- **Dev dependencies** — pytest bumped to 9.x (addresses CVE-2025-71176) with compatible pytest-asyncio
- **Version** — release line advances to **0.9.7**

### Fixed

- **Filesystem storage path traversal** — `FilesystemStorageBackend` rejects `..` segments, path separators, and any resolved path outside `data_dir`; prevents writes outside the storage root (e.g. keys like `palm:..:outside`)
- **InstanceManager active slot leak** — `acquire()` marks an instance active only after a successful load; failed lookups no longer consume active slots
- **DictStateSchema length constraints** — validates `minLength`/`maxLength` on strings and `minItems`/`maxItems` on arrays
- **`guard_core.py` Windows console** — success message uses plain `[OK]` instead of a Unicode checkmark

## [0.8.15] — 2026-06-12

Polished release — dynamic list wizards, parallel branches, and friendlier CLI choice UX on top of the state schema foundation.

### Added

- **Collection step kind** (`step_kind: collection`) — repeatable structured items with add, edit, remove, and done; per-item scopes (`item-N:field`), draft state, and resume-friendly session keys
- **Collection item selection** — compact edit/remove flow: pick by number, partial label search, or `cancel`; configurable `label_field` for any collection flow
- **Choice input resolution** — wizard and collection choice fields accept 1-based index, exact value, case-insensitive match, and unique partial match; canonical values stored in answers
- **Parallel pattern** (`parallel-demo`) — concurrent wizard branches with isolated scopes, per-branch snapshots, merge strategies, and CLI branch progress (`@parallel:<branch>`)
- **Examples** — `todo-builder` (collection + schemas), `parallel-demo`; `flow start` as the recommended entry point
- **Tests** — collection steps, item selection, choice resolution, parallel branch resume, CLI E2E for `todo-builder` and `schema-onboard`

### Changed

- **CLI display** — numbered option lists for choices and collection menus; compact item previews during edit/remove selection
- **Collection menu** — main menu stays small (add / edit / remove / continue) even with many items; current list shown as a numbered summary
- **Documentation** — README, ARCHITECTURE, DEVELOPMENT, examples guide, and website refreshed for 0.8.15
- **Version** — release line advances to **0.8.15**

### Fixed

- **Union-type schemas** — `DictStateSchema` validates `type: ["string", "null"]` and similar unions without crashing
- **Optional collection fields** — empty CLI input skips optional fields; regex rules treat `None` as empty
- **Scope stack** — collection field editing avoids duplicate scope frames on resume

## [0.8.8] — 2026-06-12

State schema and scoping release — layered validation, durable scope resume, and CLI polish.

### Added

- **State schemas** (`palm.core.context.state_schema`) — lightweight JSON Schema-inspired validation (`DictStateSchema`) with no external dependencies; supports `type`, `enum`, `minimum`/`maximum`, nested `object`/`array`, and `default`
- **Scoped state** (`BaseState`) — `enter_scope` / `exit_scope`, per-scope values (`set_scoped` / `get_scoped`), per-scope schemas (`bind_scope_schema`), and `effective_schema()` (innermost wins)
- **Flow-level schemas** — `state_schema` / `state_schema_ref` on `FlowDefinition`; materialized at submission via `palm.common.state.schema_binding`
- **Wizard layered validation** — built-in field rules → declarative rules → per-step schema → flow schema; `coerce_step_input` converts CLI string input to schema types (e.g. `"27"` → `27`)
- **Wizard step scopes** — each input step enters a named scope; prompt bundles expose `scope_stack`, `current_scope`, `scope_depth`
- **Schema-aware snapshots** — `__palm:meta` in `snapshot_state()` preserves `scope_stack`, `scope_schemas`, and `effective_schema`; `state_from_snapshot()` restores full scope context for resume
- **State observability** (`palm.common.state`) — opt-in `EventEngineStateObserver` for scope and schema events; value events off by default to avoid tick noise
- **`schema-onboard` example** — flow + per-step schemas demonstrating layered validation and resume
- **CLI context display** — wizard panels, `status`, and REPL prompt show scope and validation feedback when present
- **`palm doctor`** — flow catalog indicates which definitions declare state schemas

### Changed

- **Wizard validation** — failed schema checks keep the user on the current step with formatted, actionable messages
- **Documentation** — `ARCHITECTURE.md`, `DEVELOPMENT.md`, and `examples/README.md` updated for schema/scoping workflows
- **Version** — release line advances to **0.8.8**

### Tests

- `tests/core/test_state_scoping.py`, `tests/test_state_phase3.py`, `tests/test_state_snapshots.py`, `tests/test_state_observability.py`
- `tests/test_wizard_schema.py`, `tests/test_wizard_schemas_layered.py`

## [0.7.4] — 2026-06-10

Distribution and adoption improvements — no breaking API changes.

### Changed

- **PyPI package renamed to `palmengine`** — install with `pip install palmengine[cli]`; Python import remains `import palm`; CLI command remains `palm`
- **Packaging** — `just build`, `just publish-test`, `just publish`, `just install-local`, `just release-prep`; GitHub Actions publish workflow
- **Documentation** — README installation section, DEVELOPMENT release guide, install commands updated across docs

## [0.7.0] — 2026-06-10

Production-ready persistence foundation, storage factory, and instance lifecycle coordination.

### Changed (architectural boundaries)

- **Wizard logic removed from `palm.common`** — instance field extraction, resume restoration, and submission metadata now live in `palm.patterns.wizard.persistence` and `palm.patterns.wizard.submission`, registered via `palm.patterns._registry`
- **`PatternBuildContext` slimmed** — no wizard metadata or default commit/validation registry resolution; wizard builder owns its defaults
- **Generic persistence preserved** — `snapshot_state`, `state_from_snapshot`, `build_instance_from_job`, `update_instance_from_job`, `prepare_resume_state` remain in `palm.common.persistence.instance_sync` and delegate to pattern hooks

### Added (CLI usability)

- **Global CLI flags** — `-b`/`-d`, `--config`, `-S`/`--enable-state-snapshot`, `--max-loaded-instances`, `--max-concurrent-active`, `--scheduler`, `--format` (`table`|`json`); merged via `settings_from_invocation()` with documented env precedence
- **REPL auto-completion** — context-aware suggestions for commands, wizard/process names, and instance ids (active by default; `--all` for terminal); snapshot command scoped to instances with snapshots
- **Instance workflows** — `instance list` filters (`--all`, `--status`, `--flow`, `--limit`), `instance prune [--dry-run]`, richer tables (status emoji, short + full ids), JSON output for scripting
- **`palm doctor`** — persistence mode panel and active (non-terminal) instance summary

### Added (continued)

- **`InstanceManager`** (`palm.common.managers`) — LRU cache, active-instance tracking, lightweight summaries, startup reconciliation, and thread-safe coordination over `InstanceRepository`
- **`BaseManager`** — minimal `initialize` / `shutdown` lifecycle contract for managers
- **`InstanceSummary`** — fast listing view for CLI `instance list` without full payload loads
- **Instance settings** — `max_loaded_instances`, `max_concurrent_active`, `reconcile_instances_on_startup` on `PalmSettings`
- **Manager tests** — `tests/test_instance_manager.py`

### Changed (continued)

- **CLI bootstrap** — thin `PalmApp` client; `resolve_cli_settings()` respects `PALM_*` env unless flags are explicit; persistence banner in REPL/doctor
- **CLI instance resolution** — `instance list` shows full ids; prefix/name resolution shared across `status`, `snapshots`, and `resume`; all commands use `instance_manager`
- **`PalmApp`** — shared `instance_manager` property; instance APIs route through the manager
- **`BaseRuntime`** — wires hooks and executor through `InstanceManager`; shared manager across app runtimes
- **CLI** — `instance list`, `doctor`, and snapshot commands use the manager layer

### Added

- **`FilesystemStorageBackend`** — production filesystem persistence with atomic writes (temp file + rename), JSON serialization, namespace key paths (`palm:instances:*` → nested `.json` files), thread-safe operations, and v0.6 flat-file read compatibility
- **`StorageFactory`** (`palm.common.storage`) — lazy backend registration, `PalmSettings`-driven `backend_options`, and `initialize_engine()` / `select()` helpers
- **Storage exceptions** — `StoragePermissionError`, `StorageCorruptionError` in `palm.core.exceptions`
- **Optional storage extras** — `postgres` and `mongodb` uv extras for lazy-loaded backends
- **Filesystem tests** — `tests/test_filesystem_storage.py` (unit + repository + `PalmApp` integration)

### Changed

- **`BaseRuntime.start()`** — initializes shared `StorageEngine` via `StorageFactory` (respects `backend_options` from `PalmSettings.data_dir`)
- **`runtime_start_options()`** — forwards filesystem `data_dir` through `backend_options`
- **Repository list methods** — skip missing or corrupted index entries instead of failing entire listings
- **Storage autoload** — core backends (`memory`, `filesystem`) register at import; `postgres` / `mongodb` load lazily on first use
- **`FilesystemBackend`** — alias retained; canonical class is `FilesystemStorageBackend`

### Configuration

```bash
export PALM_STORAGE_BACKEND=filesystem
export PALM_DATA_DIR=./data   # optional; defaults to ./data
```

## [0.6.0] — 2026-06-07

Major orchestration maturation release: authoritative lifecycle, layered runtimes, execution plans, and production-oriented server/daemon surfaces.

### Added

- **`palm.app` layer** — `PalmApp`, `PalmSettings`, multi-runtime registry, shared storage, definition bootstrap
- **`palm.common` package** — shared coordination split into `executions/`, `plans/`, `hooks/`, `persistence/`, `patterns/`
- **Django-style extensible apps** — `patterns/`, `providers/`, `storages/` restructured as self-contained subpackages with per-app `registry.py` and `INSTALLED_*` autoload lists
- **Pattern builder registry** — each pattern app registers its own `builder.py`; `common/patterns/builder.py` dispatches generically
- **Lifecycle authority** — `RunResult` + `OrchestrationEngine.apply_result()` as sole job transition path
- **Scheduling model** — `JobScheduler` (inline/queued) composes with `JobRunner`; shared `drive_job` primitive
- **Middleware** — `JobHook` protocol with drive-phase hooks (`on_before_drive`, `on_after_drive`); `AuthMiddleware`, `DriveObservabilityHook`, `InstancePersistenceHook`
- **State snapshots** — optional `StateSnapshotHook` captures `BlackboardState` at configurable job status transitions; stored as bounded `state_snapshots[]` ring buffer on `ProcessInstance`; configured via `PalmSettings` (`enable_state_snapshot`, `snapshot_on_status`, `max_snapshots_per_instance`); CLI `palm instance snapshots <id>`; `PalmApp.list_instance_snapshots()`
- **Thread-safe registries** — `Registry`, pattern builder map, `CommitRegistry`, `PlanRegistry`, and `RuntimeRegistry` use `threading.RLock`; idempotent re-registration; concurrency tests in `tests/test_core_registry.py`
- **Executions handoff** — `ExecutionPlan`, `ProcessPlan`, `prepare_*_plan`, `submit_plan(s)`, `PlanRegistry` for deferred submission
- **Runtimes** — `RuntimeHost` protocol, `BaseRuntime` shared wiring, `DaemonRuntime`, `ServerRuntime` (stdlib HTTP API)
- **Auth** — `AuthEngine` wired on runtimes; `auth_enforce`, per-request `X-Palm-Subject` on server
- **Server API** — `POST /v1/plans/prepare`, `POST /v1/plans/submit`, job input/status endpoints
- **Migration guide** — [MIGRATION-0.6.md](MIGRATION-0.6.md)

### Changed

- **Package layout** — coordination logic moved from monolithic `palm.executions` to structured `palm.common`
- **EmbeddedRuntime** slimmed to policy wrapper over `BaseRuntime`
- **DefinitionExecutor** uses plan-based submission internally
- CLI storage flag renamed to `--storage-backend`
- Test double renamed: `TestBackend` → `TestRunner`
- Orchestration initialization uses `scheduler=` (not `mode=`)

### Removed

- **`palm.executions` package** — use `palm.common` and subpackages (`common.plans`, `common.hooks`, etc.)
- **`palm.patterns.wizard.commit`** — use `palm.patterns.wizard.handler`
- `ExecutionBackend` alias (use `JobRunner`)
- `BehaviorTreeBackend` alias (use `BehaviorTreeRunner`)
- `EmbeddedMode` (use `InlineScheduler`)
- `wire_instance_persistence()` (automatic hook registration)
- `ProcessExecutor` alias (use `DefinitionExecutor`)
- Deprecated `backend=` parameters on schedulers and runtime runner resolution

## [0.5.0-dev] — 2026-06-05

Milestone toward **0.5.0**: a production-oriented developer experience on top of the 0.4.0 architecture rebuild.

### Added

- **Executions layer** (`palm.executions`) — `DefinitionExecutor`, `DefinitionRepository`, pattern builder, and instance sync outside core
- **Persistent process instances** (`palm.instances`) — durable snapshots with status history; resume across runtime restarts when storage is shared
- **Pluggable state** — `BlackboardState` and orchestration job state decoupled from engine internals
- **Transactional wizards** — declarative validation, summary/commit steps, named commit handlers, resource action steps, backtracking
- **Modern CLI** (`palm.runtimes.cli_pkg`) — Rich output, REPL, `process` / `instance` / `wizard` commands, `input` / `back` / `status`
- **`palm doctor`** and **`palm status --full`** — engine health, registries, definition catalog, recent instances
- **`palm version --full`** — build and plugin matrix without starting a job
- **Example definitions** — onboarding, data ingestion, approval workflow, quick wizard under `examples/definitions/`
- **`examples/full_demo.py`** — end-to-end script: register → submit → input → commit → simulated restart → resume
- **Documentation** — README quick start, ARCHITECTURE.md, DEVELOPMENT.md, examples guide
- **`just` recipes** — `palm-doctor`, `palm-repl`, demos, `demo-full`, release-oriented `prepr`

### Changed

- **EmbeddedRuntime** high-level API — `submit_flow`, `submit_process`, `provide_input`, `resume_process`, `get_instance`
- CLI entry point rebuilt; legacy REPL command aliases retained during transition
- Version series opens at **0.5.0-dev** (supersedes 0.4.0-dev tracking)

### Architecture (carried from 0.4.0)

- Pure **core** layer with registry-based extension
- Patterns: wizard, DAG, ETL; providers: REST, GraphQL, Postgres; storages: memory, filesystem, MongoDB, Postgres
- Legacy code quarantined under `archive/` (not imported by new code)

## [0.4.0] — 2026

### Added

- Full package restructure: `palm.core`, `palm.patterns`, `palm.providers`, `palm.storages`, `palm.definitions`
- Registry-based pattern, provider, and storage registration
- Wizard, DAG, and ETL pattern skeletons
- Embedded runtime wiring and orchestration job lifecycle
- Core purity guard and AGENTS.md constitution

### Removed

- Monolithic pre-0.4.0 layout (preserved in `archive/` for reference)

## [0.3.x and earlier]

See `archive/` for legacy CLI, wizards, and behavior-tree implementations.