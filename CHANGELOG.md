# Changelog

All notable changes to Palm are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.7.0] — 2026-06-10

Production-ready persistence foundation, storage factory, and instance lifecycle coordination.

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