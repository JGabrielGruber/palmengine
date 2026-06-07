# Migrating to Palm 0.6

This guide covers breaking changes and recommended patterns when upgrading from **0.5.x** to **0.6.0**.

---

## Summary

Palm 0.6 finalizes the orchestration maturation work started in 0.5.x:

- **Lifecycle authority** — `JobRunner` → `RunResult` → `apply_result`
- **Scheduling** — `JobScheduler` (inline / queued) replaces ad-hoc modes
- **Executions handoff** — `ExecutionPlan` / `ProcessPlan` with prepare → stage → submit
- **Runtimes** — `BaseRuntime` foundation with `EmbeddedRuntime`, `DaemonRuntime`, `ServerRuntime`
- **Middleware** — `JobHook` drive-phase hooks, `AuthMiddleware`, `InstancePersistenceHook`

Deprecated aliases and transitional APIs from the 0.5 maturation period have been **removed**.

Shared coordination logic lives in **`palm.common`**. The `palm.executions` package has been **removed**.

---

## Package layout (`palm.common`)

| 0.6 import | Was (0.5) | Notes |
|------------|-----------|-------|
| `palm.common` | `palm.executions` | `DefinitionExecutor`, repos, `build_pattern`, plans |
| `palm.common.plans` | `palm.executions.plan` | `ExecutionPlan`, `ProcessPlan`, `PlanRegistry` |
| `palm.common.hooks` | `palm.executions.hooks` | `InstancePersistenceHook` |
| `palm.common.persistence` | `palm.executions.repository`, `instance_*` | Repos and sync helpers |
| `palm.common.patterns` | `palm.executions.builder`, `build_context` | Generic `build_pattern` dispatcher |

### Extensible modules (Django-style apps)

Patterns, providers, and storages are self-contained subpackages:

| App type | Layout | Registration |
|----------|--------|--------------|
| Pattern | `patterns/<name>/pattern.py`, `builder.py`, `registry.py` | `INSTALLED_PATTERNS` + `pattern_registry` |
| Provider | `providers/<name>/provider.py`, `registry.py` | `INSTALLED_PROVIDERS` + `provider_registry` |
| Storage | `storages/<name>/backend.py`, `registry.py` | `INSTALLED_STORAGES` + `storage_registry` |

Wizard-specific APIs live under `palm.patterns.wizard` (e.g. `handler`, `options`, `builder`).

```python
from palm.common import DefinitionExecutor, ExecutionPlan
from palm.common.hooks import InstancePersistenceHook
from palm.common.plans import PlanRegistry
from palm.patterns.wizard.handler import CommitResult, default_commit_registry
```

---

## Removed APIs

| Removed (0.5) | Replacement (0.6) |
|---------------|-------------------|
| `ExecutionBackend` | `JobRunner` |
| `BehaviorTreeBackend` | `BehaviorTreeRunner` |
| `EmbeddedMode` | `InlineScheduler` from `palm.runtimes.schedulers` |
| `wire_instance_persistence()` | Automatic `InstancePersistenceHook` at `BaseRuntime.start()` |
| `ProcessExecutor` | `DefinitionExecutor` |
| `OrchestrationEngine.initialize(mode=...)` | `initialize(scheduler=...)` |
| `InlineScheduler(backend=...)` | `InlineScheduler(runner=...)` |
| `runtime.start(backend="memory")` | `runtime.start(storage_backend="memory")` |
| CLI `--backend` | CLI `--storage-backend` |

---

## Orchestration

### JobRunner (was ExecutionBackend)

```python
# Before
from palm.core import ExecutionBackend

# After
from palm.core import JobRunner
from palm.backends import BehaviorTreeRunner

scheduler = InlineScheduler(runner=BehaviorTreeRunner())
engine.initialize(scheduler=scheduler)
```

### JobScheduler (was OrchestrationMode / EmbeddedMode)

```python
# Before
from palm.runtimes.embedded_mode import EmbeddedMode
from palm.backends import BehaviorTreeBackend

engine.initialize(mode=EmbeddedMode(backend=BehaviorTreeBackend()))

# After
from palm.runtimes.schedulers import InlineScheduler
from palm.backends import BehaviorTreeRunner

engine.initialize(scheduler=InlineScheduler(runner=BehaviorTreeRunner()))
```

### Test doubles

```python
# Before
from tests.core.fakes.backend import TestBackend

# After
from tests.core.fakes.runner import TestRunner
```

---

## Runtimes

### Storage backend option

```python
# Before
runtime.start(backend="memory")

# After
runtime.start(storage_backend="memory")
```

### Instance persistence

No manual wiring required. `BaseRuntime.start()` registers `InstancePersistenceHook` automatically.

```python
# Before — removed
from palm.executions.instance_events import wire_instance_persistence
wire_instance_persistence(runtime, runtime.instances)

# After — nothing to do
runtime.start()
```

### Runtime variants (0.6)

| Runtime | Default scheduler | Use case |
|---------|-------------------|----------|
| `EmbeddedRuntime` | inline | Libraries, tests, CLI |
| `DaemonRuntime` | queued | Long-lived background process |
| `ServerRuntime` | queued + HTTP | Network API |

```python
from palm.runtimes import DaemonRuntime, ServerRuntime

daemon = DaemonRuntime()
daemon.start(credentials={"subject": "ops"}, auth_enforce=True)

server = ServerRuntime()
server.start(port=8080, auth_enforce=True)
# POST /v1/plans/prepare, POST /v1/plans/submit
# Header: X-Palm-Subject: ops
```

---

## Executions

### DefinitionExecutor (was ProcessExecutor)

```python
from palm.executions import DefinitionExecutor  # not ProcessExecutor
```

### ExecutionPlan / ProcessPlan

Prepare without submitting (deferred submission, batching, server staging):

```python
plan = runtime.executor.prepare_flow_plan(flow)
job = runtime.executor.submit_plan(plan)

bundle = runtime.executor.prepare_process_plan(process)
jobs = runtime.executor.submit_plans(bundle.plans)
```

Server HTTP two-phase flow:

```http
POST /v1/plans/prepare
POST /v1/plans/submit  {"plan_ids": ["plan-abc", ...]}
```

---

## Auth middleware

Enable per-runtime drive authorization:

```python
runtime.start(
    credentials={"subject": "ada"},
    auth_enforce=True,
    auth_roles=("user",),  # optional
)
```

HTTP clients send `X-Palm-Subject` when `auth_enforce=True`.

---

## CLI

```bash
# Before
palm --backend memory repl

# After
palm --storage-backend memory repl
```

---

## Verification after upgrade

```bash
just check        # lint + types + tests + guard-core
just palm-doctor  # runtime health
```

If you imported any symbol listed in **Removed APIs**, search your codebase and apply the replacements above.