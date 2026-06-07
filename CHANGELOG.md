# Changelog

All notable changes to Palm are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.6.0] — 2026-06-07

Major orchestration maturation release: authoritative lifecycle, layered runtimes, execution plans, and production-oriented server/daemon surfaces.

### Added

- **`palm.common` package** — shared coordination split into `executions/`, `plans/`, `hooks/`, `persistence/`, `patterns/`; `palm.executions` retained as compat alias
- **Lifecycle authority** — `RunResult` + `OrchestrationEngine.apply_result()` as sole job transition path
- **Scheduling model** — `JobScheduler` (inline/queued) composes with `JobRunner`; shared `drive_job` primitive
- **Middleware** — `JobHook` protocol with drive-phase hooks (`on_before_drive`, `on_after_drive`); `AuthMiddleware`, `DriveObservabilityHook`, `InstancePersistenceHook`
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