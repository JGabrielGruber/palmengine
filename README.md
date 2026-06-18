# Palm Engine 🌴

**Palm** is a lightweight, Python-first orchestration engine built on a clean **Behavior Tree** foundation. It coordinates interactive wizards, data pipelines, and—over time—compute-heavy workloads with explicit contracts, durable state, and human-first tooling.

**Current release:** `0.13.0` — Wizard Experience: `/v1/wizards` REST, Explorer wizard workspace, collection UI · See [CHANGELOG.md](CHANGELOG.md) · [EXPLORER-WIZARD.md](EXPLORER-WIZARD.md) · [VISION-0.13](docs/VISION-0.13.md) · [SCOPE.md](SCOPE.md)

---

## Installation

Palm is published on PyPI as **`palmengine`**. After install, you **import** `palm` and run the **`palm`** CLI — same names as in source development.

| What | Name |
|------|------|
| PyPI package | `palmengine` |
| `pip install` | `pip install palmengine[cli]` |
| Python import | `import palm` |
| CLI command | `palm` |

```bash
# End users — CLI + REPL
pip install palmengine[cli]
palm version --full
palm doctor

# Library only (no Rich / REPL)
pip install palmengine

# From source (contributors)
git clone https://github.com/JGabrielGruber/palmengine.git && cd palmengine
uv sync --group dev --extra cli
uv pip install -e ".[cli]"
```

Optional extras: `[cli]`, `[test]`, `[dev]`, `[all]`, `[postgres]`, `[mongodb]`.

---

## Vision

Palm aims to be **simple at the core and powerful at the edges**:

- **Human-first** — interactive wizards, Rich CLI feedback, backtracking, resume after interruption
- **Truth-seeking** — pluggable state, persistent process instances, transactional commits
- **Extensible** — patterns, providers, and storages register at the edge; core stays pure
- **Ambitious but honest** — from onboarding wizards to multi-flow data pipelines and planned GPU kernel nodes

Behavior Trees are the control-flow foundation. Steps are nodes. Cross-cutting concerns (auth, guards, observability) belong in **runtimes** and optional **BT guard nodes**—not buried in step definitions.

---

## What works today (0.12 architecture)

| Area | Capabilities |
|------|----------------|
| **Resources** | `ResourceDefinition`, `ResourceEngine.invoke()`, `ResourceLeaf`, `ResourceCatalog`; wizard `step_kind: resource` |
| **`palm` provider** | Palm calling Palm — local `submit_flow` / `invoke_resource` or remote HTTP; recursion guardrails |
| **ApplicationHost** | Top-level orchestrator — role profiles (`all_in_one`, `master`, `worker`, `server`), startup recovery |
| **CQRS** | Command/query buses, projections (`instance_index`, `wizard_progress`, `job_status_board`, `resource_invocations`) |
| **Reliability** | Transactional outbox, compensation handlers (including resource undo), optional webhook dispatch |
| **Core** | Behavior tree, orchestration, context, storage, resource, event, auth, **TransformEngine** |
| **State** | `DictStateSchema`, scoped state, schema-aware snapshots (`__palm:meta`) |
| **Transforms** | **22 built-in rules** — field shaping, JSONPath, dates, conditionals, serialization, `enrich_resource` |
| **Patterns** | **Wizard** (collection, transform, resource steps, summary/commit); **parallel** branches; DAG and ETL stubs |
| **Persistence** | Filesystem backend, `InstanceManager`, durable resume across restarts |
| **Runtimes** | `EmbeddedRuntime`, `DaemonRuntime`, `ServerRuntime` (HTTP), **CLI + REPL** (host-backed) |
| **Palm Explorer** | SSR hub at `/explorer` — flows, jobs, instances, **wizard workspace** (HTMX + collection editor), **resources**; `/` redirects here |
| **Wizard REST** | `/v1/wizards` — submit, status, input, backtrack keyed by `instance_id` |
| **Dashboard** | `palm status` — projection-backed Rich overview; `--full`, `-r` live refresh |
| **DX** | Rich examples, `palm doctor`, `palm resource *`, `just` quality recipes |

```mermaid
flowchart LR
    User[Developer / operator] --> CLI[CLI / REPL]
    CLI --> Host[ApplicationHost]
    Host --> CQRS[Command + Query buses]
    Host --> RT[Runtime main]
    CQRS --> Proj[Projections]
    RT --> CM[common + patterns]
    CM --> BT[Behavior Tree]
```

**Recommended entrypoint:** `ApplicationHost` wraps `PalmApp` (infrastructure) and wires CQRS, projections, outbox, and compensation. The CLI uses it automatically via `create_cli_host()`.

---

## Quick start

```bash
pip install palmengine[cli]

palm status              # live projection dashboard (default)
palm doctor              # full health report
palm version --full      # version + registered plugins
palm repl                # interactive shell (default: `palm`)
palm flow start onboard          # recommended — works for all patterns
# shortcut: palm start onboard
```

**From source:** `uv sync --group dev --extra cli && uv pip install -e ".[cli]"` then the same `palm` commands.

**Library quick start (ApplicationHost):**

```python
from palm.app import ApplicationHost, HostProfile

with ApplicationHost(profile=HostProfile.all_in_one()) as host:
    job = host.submit_flow("onboard")
    rows = host.list_instance_views(include_terminal=False)
    print(job.status.value, len(rows))
```

Demo script: `uv run python examples/full_demo.py` (host + resume across restart).

**Server + Palm Explorer:**

```bash
# Start HTTP server (default port 8080)
python -c "from palm.runtimes.server import ServerRuntime, run_server; run_server(ServerRuntime())"

# Open the living hub — flows, jobs, instances, schemas
open http://localhost:8080/explorer   # or just http://localhost:8080/ (redirects)
```

REST reference: `GET /v1/docs` · OpenAPI: `GET /v1/openapi.json` · Health: `GET /health`

### Try in Explorer

The instance detail page is a **live wizard workspace** — progress bar, prompt card, answers, timeline, and backtrack. Collection steps get a rich multi-item editor (add / edit / remove) with HTMX partial updates.

```bash
# 1. Start server
python -c "from palm.runtimes.server import ServerRuntime, run_server; run_server(ServerRuntime())"

# 2. Submit todo-builder (collection demo)
curl -s -X POST http://localhost:8080/v1/wizards \
  -H 'Content-Type: application/json' \
  -d '{"flow_name": "todo-builder"}'
# → copy instance_id from JSON

# 3. Open workspace
open http://localhost:8080/explorer/instances/<instance_id>
```

Use **Add New** on the collection overview, fill fields, edit or remove items, then **Continue to summary**. Full guide: [EXPLORER-WIZARD.md](EXPLORER-WIZARD.md).

**Try the new examples:**

```bash
palm flow start schema-onboard   # layered state schemas + scopes
palm flow start todo-builder     # dynamic todo list (collection step)
palm flow start parallel-demo    # parallel wizard branches
palm flow start transform-example  # wizard transform steps
palm flow start transform-shaping  # pipeline calculate / lookup / conditional
palm flow start transform-formats  # json_load → csv_dump ETL-style pipeline
```

### Transforms

Declarative data shaping via registered rules — usable in **pipelines**, **wizard** steps (`step_kind: transform`), or `TransformLeaf` nodes.

```python
from palm.common.transforms import TransformExecutor, autoload

autoload()
executor = TransformExecutor()
result = executor.apply(
    "string_format",
    "ada",
    template="Hello, {value}!",
    case="title",
)
# → "Hello, Ada!"
```

```yaml
# Wizard step (in flow options.steps)
step_kind: transform
source_key: name
target_key: greeting
rule: string_format
options:
  template: "Hello, {value}!"
  case: title
```

Run `palm doctor` for the full rule catalog with descriptions. Extend with `register_transform("my_rule", MyRule)` at bootstrap.

**CLI persistence:** the CLI bootstraps `ApplicationHost` (`all_in_one` profile). By default it uses **in-memory** storage (fast, non-durable). Set durable storage via flags or environment:

```bash
# Recommended for local work — persists instances under ./data/
export PALM_STORAGE_BACKEND=filesystem
export PALM_DATA_DIR=./data

# Or per invocation:
palm --storage-backend filesystem --data-dir ./data wizard start onboard
```

`palm doctor` and REPL startup show whether state will survive restarts.

**Instance commands** (`list`, `status`, `snapshots`) read through the host **query bus** and projections. Writes (`flow start`, `input`, `resume`) go through the **command bus**. Short ids from `instance list` work with prefix matching.

**Global CLI flags** (override env only when explicitly passed):

| Flag | Env | Purpose |
|------|-----|---------|
| `-b` / `--storage-backend` | `PALM_STORAGE_BACKEND` | Storage backend (`memory`, `filesystem`, …) |
| `-d` / `--data-dir` | `PALM_DATA_DIR` | Data directory for durable backends |
| `--config` | — | Optional `.env`-style config file |
| `-S` / `--enable-state-snapshot` | `PALM_ENABLE_STATE_SNAPSHOT` | Capture state snapshot history |
| `--max-loaded-instances` | `PALM_MAX_LOADED_INSTANCES` | InstanceManager LRU size |
| `--max-concurrent-active` | `PALM_MAX_CONCURRENT_ACTIVE` | Active instance cap |
| `--scheduler` | `PALM_DEFAULT_SCHEDULER` | `inline` or `queued` |
| `--format` | — | `table` (default) or `json` for scripting |

Settings precedence: `PALM_*` environment → `--config` file → CLI flags.

```bash
palm instance list                          # active (non-terminal) instances
palm instance list --all --format json      # all instances, JSON for scripts
palm instance list --status WAITING_FOR_INPUT --flow quick
palm instance prune --dry-run               # preview terminal instance cleanup
palm --format json instance status <id>     # machine-readable status
```

The REPL uses smart tab-completion for commands, flow/process names, and instance ids
(active by default; `--all` includes terminal instances).

---

## Persistent wizard resume

Process instances snapshot orchestrated work—wizard answers, step, status—and persist through storage so sessions survive restarts.

```bash
palm wizard start onboard
palm input Ada
palm instance list                    # note instance id

# Later, or in a new terminal:
palm process resume <instance_id>
palm input ada@example.com
# … continue through summary and commit
```

Shared `StorageEngine` across runtime lifetimes is required for cross-process resume (see [DEVELOPMENT.md](DEVELOPMENT.md)).

**Durable filesystem storage (recommended for local dev and single-node deploys):**

```bash
export PALM_STORAGE_BACKEND=filesystem
export PALM_DATA_DIR=./data   # optional; defaults to ./data

palm wizard start onboard
palm input Ada
# Restart the CLI — instances and definitions persist under ./data/
palm process resume <instance_id>
```

---

## State snapshots (optional)

Palm can record **point-in-time blackboard captures** at selected job status transitions—useful for audit trails, debugging wizard flows, and future time-travel replay. Snapshots are stored on each `ProcessInstance` as a bounded ring buffer (`state_snapshots[]`). The feature is **off by default**.

**Enable via environment:**

```bash
export PALM_ENABLE_STATE_SNAPSHOT=true
export PALM_SNAPSHOT_ON_STATUS='["WAITING_FOR_INPUT","SUCCEEDED","FAILED"]'
export PALM_MAX_SNAPSHOTS_PER_INSTANCE=10

palm wizard start onboard
palm input Ada
palm instance snapshots <instance_id>   # inspect captured history
```

**Enable in code:**

```python
from palm.app import ApplicationHost, HostProfile, PalmSettings

settings = PalmSettings(
    enable_state_snapshot=True,
    snapshot_on_status=["WAITING_FOR_INPUT", "SUCCEEDED"],
    max_snapshots_per_instance=5,
)
with ApplicationHost(settings, profile=HostProfile.all_in_one()) as host:
    job = host.submit_flow("onboard")
    snapshots = host.list_instance_snapshots(job.metadata["instance_id"])
```

Resume still uses the latest `state_snapshot` field (maintained by `InstancePersistenceHook`). Historical entries are for inspection—not replay yet. See [ARCHITECTURE.md](ARCHITECTURE.md) for middleware design and trade-offs.

---

## Example flows

Definitions under [`examples/definitions/`](examples/definitions/) auto-register at CLI startup.

| Example | Command | Highlights |
|---------|---------|------------|
| **Onboarding** | `flow start onboard` | Validation, summary + commit |
| **Schema wizard** | `flow start schema-onboard` | Flow + per-step schemas, scoped resume |
| **Todo builder** | `flow start todo-builder` | Collection step, dynamic lists, schemas |
| **Parallel demo** | `flow start parallel-demo` | Concurrent branches, merge, branch scopes |
| **Data ingestion** | `flow start ingest-wizard` | Resource action step, ETL companion flow |
| **Approval** | `flow start approval` | Multi-field validation, commit handler |
| **Quick demo** | `flow start quick` | Minimal wizard for resume experiments |

```bash
palm process list
palm process submit data-ingestion
palm doctor    # shows flows with state schemas
```

Details: [examples/README.md](examples/README.md)

---

## Living Explorer Hub

When `ServerRuntime` is running, **Palm Explorer** is the browser-first control surface for operators and integrators:

| Path | Purpose |
|------|---------|
| `/explorer` | Overview — registered flows, active jobs, instance counts |
| `/explorer/flows` | Flow catalog with **Start this flow** actions |
| `/explorer/flows/submit` | Schema-driven flow submission (registered or test wizard) |
| `/explorer/jobs` | Job board with wizard input forms |
| `/explorer/instances` | Durable process instance browser |
| `/explorer/schemas` | State schema introspection |

Legacy `/wiki/*` and `/docs` redirect to `/explorer`. Implementation: `palm/runtimes/server/surfaces/ssr/explorer/`.

---

## CLI overview

| Command | Description |
|---------|-------------|
| `palm` / `palm repl` | Interactive REPL (host-backed) |
| `palm status` | Live dashboard — instances, wizards, jobs, host events |
| `palm status --full` | Detailed dashboard (active rows, traces) |
| `palm status -r` | Live refresh every 2s (Ctrl+C to stop) |
| `palm doctor` | Full health report: plugins, persistence, definitions |
| `palm version --full` | Version, Python, registered patterns/providers/storages |
| `palm process list` \| `submit` \| `resume` | Definition catalog and lifecycle |
| `palm instance list` | Instances via CQRS projection |
| `palm instance snapshots <id>` | State snapshot history (when enabled) |
| `palm flow start <flow>` | Start any flow — **recommended** |
| `palm start <flow>` | Shortcut for `flow start` |
| `palm wizard start <flow>` | Wizard-only shortcut (legacy alias) |
| `palm input` / `palm back` | Drive or rewind an active flow |
| `palm host all-in-one` | Run ApplicationHost (blocking, signals) |
| `palm host master` \| `worker` \| `server` | Role-based deployment |

Run `palm --help` for the full list.

---

## Project structure

```
src/palm/
├── app/            # ApplicationHost, PalmApp (infra), settings, host roles
├── core/           # Pure engines (BT, orchestration, context, storage, …)
├── common/         # CQRS, outbox, compensation, hooks, persistence, managers
├── instances/      # ProcessInstance + StateSnapshot models
├── definitions/    # FlowDefinition, ProcessDefinition
├── patterns/       # wizard, dag, etl (extensible)
├── providers/      # rest, graphql, postgres (extensible)
├── storages/       # memory, filesystem, postgres, mongodb (extensible)
└── runtimes/       # Embedded/Daemon/Server, CLI (host-backed)

examples/           # definitions/ + full_demo.py (ApplicationHost)
SCOPE.md            # vision, scope, roadmap
ARCHITECTURE.md     # layers, ApplicationHost, CQRS, reliability
MIGRATION-0.10.md   # upgrade guide from 0.9.x bootstrap paths
archive/            # legacy + experimental (not imported)
```

---

## Resource best practices (0.12)

1. **Define once, reference everywhere** — register `ResourceDefinition` in the repository; use `resource_ref` in wizards, `ResourceLeaf` in behavior trees, and `enrich_resource` in transforms.
2. **Prefer declarative params** — bind with `{{ state.key }}`; promote wizard answers before resource steps (`promote_binding_keys()`).
3. **Compose with the `palm` provider** — delegate sub-flows locally or via `remote_url`; rely on built-in depth/cycle guardrails.
4. **Observe `resource.*` events** — completed/failed payloads include correlation (`invoke_depth`, `invoke_chain`, `parent_job_id`).
5. **Cache reads, not writes** — keep `resource_cache_definitions` on; enable `resource_cache_results` only for idempotent `fetch` actions.
6. **Discover before invoke** — `palm doctor`, `palm resource list/describe`, and Explorer `/explorer/resources` show actions and schemas.

```bash
palm resource list
palm resource describe fetch-customer
palm resource invoke fetch-customer customer_id=42
```

Full guide: [docs/VISION-0.12.md](docs/VISION-0.12.md) · [MIGRATION-0.12.md](MIGRATION-0.12.md)

---

## Where Palm is headed

High-level direction (not all shipped yet). Full detail in [SCOPE.md](SCOPE.md).

| Theme | Direction |
|-------|-----------|
| **Runtimes** | WebSocket surface, persistent plan registry, richer server auth |
| **Middleware** | Runtime-level auth/observability; optional BT guard nodes for step policy |
| **Compute** | `KernelLeaf` GPU nodes, resident kernels, dataset staging (Parquet → context → kernel → artifact) |
| **Observability** | Structured events, long-running job management |

GPU batch prototypes live in `archive/experimental/gpubatches/` as early R&D—not part of the supported API until promoted.

```mermaid
---
title: CPU vs GPU Execution Time
---
xychart
    title "CPU vs GPU Batch Processing Time"
    x-axis "Batch Size" ["32K", "65K", "131K", "262K"]
    y-axis "Time (seconds)" 0 --> 60
    line "CPU" [8.28, 14.37, 28.64, 57.14]
    line "GPU" [0.026, 0.051, 0.100, 0.200]
```

---

## Architecture & contribution

| Document | Contents |
|----------|----------|
| [SCOPE.md](SCOPE.md) | Vision, in/out of scope, roadmap, experimental areas |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Layers, BT control flow, middleware model, engines |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Setup, tests, adding patterns/backends |
| [AGENTS.md](AGENTS.md) | Rules for contributors and AI agents |

```bash
just dev          # setup
just check        # lint + types + tests
just palm-doctor  # CLI health
just demo-full    # end-to-end script
```

---

## Philosophy

**🌴 Palm grows where the sun meets the sea.**

Orchestration should balance structure with flexibility—automation with mindful human participation. Palm keeps the core small and truthful, puts people first in interactive flows, and grows capability through registries and nodes rather than monolithic middleware.

---

## Migration

- **0.11.x → 0.12 Compositional Power** — see [MIGRATION-0.12.md](MIGRATION-0.12.md) for wizard `step_kind: resource` and removed `action` steps
- **0.9.x → 0.10 architecture** — see [MIGRATION-0.10.md](MIGRATION-0.10.md) for `ApplicationHost`, CQRS, and removed `bootstrap_cli` / `cli/pkg` paths
- **0.5.x → 0.6.0** — see [MIGRATION-0.6.md](MIGRATION-0.6.md) for removed aliases (`ExecutionBackend`, `EmbeddedMode`, etc.)
- **0.3.x legacy** — code under **`archive/`** is reference-only; never import from `archive/` in new work

---

## License

MIT