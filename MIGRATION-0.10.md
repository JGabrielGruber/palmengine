# Migration guide — 0.9.x → 0.10.9

Palm **0.10.9** introduces `ApplicationHost` as the recommended top-level orchestrator. The underlying engines, patterns, and definitions are unchanged — this is primarily a **bootstrap and API layering** shift.

---

## What changed

| Before (0.9) | After (0.10) |
|--------------|--------------|
| `PalmApp.bootstrap_cli()` | `create_cli_host()` → `ApplicationHost` |
| `create_cli_app()` | **Deprecated** — use `create_cli_host()` |
| CLI writes via `ctx.app.submit_*` | CLI writes via host **command bus** (`host.submit_flow`, …) |
| CLI reads via `InstanceManager` | CLI reads via **query bus** / projections |
| Single embedded runtime `"cli"` | Collapsed `all_in_one` profile → runtime `"main"` |
| `palm/runtimes/cli/pkg/` shim | **Removed** — import from `palm.runtimes.cli.shared` |

`PalmApp` remains the **infrastructure layer** (storage, runtime registry, definitions). You do not need to rewrite pattern or definition code.

---

## CLI and terminal apps

**Old (deprecated):**

```python
from palm.app import create_cli_app

app = create_cli_app()
app.submit_flow("onboard")
app.shutdown()
```

**New (recommended):**

```python
from palm.app import ApplicationHost, HostProfile
from palm.app.session import create_cli_host

host = create_cli_host()
try:
    job = host.submit_flow("onboard")
    rows = host.list_instance_views(include_terminal=False)
finally:
    host.shutdown()
```

The `palm` CLI already uses `create_cli_host()` internally. No operator workflow changes for `palm flow start`, `palm instance list`, etc.

---

## Library / service embedding

**Old pattern (still valid for low-level tests):**

```python
from palm.app import PalmApp, PalmSettings

app = PalmApp(PalmSettings()).bootstrap()
app.create_runtime("embedded", autostart=True)
app.load_definitions()
job = app.submit_flow("onboard")
```

**New pattern (recommended for services):**

```python
from palm.app import ApplicationHost, HostProfile, PalmSettings

with ApplicationHost(profile=HostProfile.all_in_one()) as host:
    job = host.submit_flow("onboard")
    status = host.get_instance_view(job.metadata["instance_id"])
```

### Multi-role deployment

```bash
palm host master    # command runtime + outbox drain
palm host worker    # daemon workers
palm host server    # HTTP API
palm host all-in-one  # collapsed dev profile (same as CLI)
```

```python
from palm.app import ApplicationHost, HostProfile, run_host

# Blocking process helper
run_host("master")

# Or explicit lifecycle
host = ApplicationHost(profile=HostProfile.master_only())
host.start()
# host.execute(SubmitFlowCommand(...))
host.shutdown()
```

---

## CQRS commands and queries

Host convenience methods wrap the buses:

| Write | Read |
|-------|------|
| `host.submit_flow(ref)` | `host.list_instance_views()` |
| `host.submit_process(ref)` | `host.get_instance_view(id)` |
| `host.provide_input(job_id, value)` | `host.list_instance_snapshots(id)` |
| `host.resume_process(instance_id)` | `host.get_wizard_progress(instance_id=…)` |
| `host.execute(SubmitFlowCommand(...))` | `host.ask(ListInstancesQuery(...))` |

Extend by adding command/query dataclasses in `palm/common/cqrs/` and wiring in `palm/app/host/cqrs_wiring.py`.

---

## Compensation handlers

Register undo hooks for failed wizard commits (optional):

```python
from palm.common.compensation import (
    CompensationContext,
    CompensationResult,
    default_compensation_registry,
)

def undo_save(ctx: CompensationContext) -> CompensationResult:
    return CompensationResult.success({"undone": True})

default_compensation_registry().register_for_commit_hook("save_profile", undo_save)
```

The host wires `CompensationCoordinator` on start when `enable_compensation=True` (default).

---

## Settings additions (0.10)

| Setting | Default | Purpose |
|---------|---------|---------|
| `rebuild_projections_on_startup` | `True` | Rebuild CQRS read models on host start |
| `projection_rebuild_batch_size` | `100` | Batch size for large instance rebuilds |
| `enable_compensation` | `True` | Event-driven commit-failure undo |
| `enable_webhook_dispatcher` | `False` | POST outbox events to external URLs |
| `webhook_urls` | `[]` | Webhook destinations |
| `host_profile` | — | `all_in_one`, `master`, `worker`, `server` |

---

## Import changes

| Removed | Replacement |
|---------|-------------|
| `PalmApp.bootstrap_cli()` | `ApplicationHost` + `HostProfile.all_in_one()` |
| `CLI_RUNTIME_NAME` | Use `host.running_runtimes()` (CLI → `["main"]`) |
| `palm.runtimes.cli.pkg.*` | `palm.runtimes.cli.shared.*` |
| `create_cli_app()` | `create_cli_host()` (deprecated wrapper still returns `.app`) |

---

## What you do **not** need to change

- Flow/process definitions in `examples/definitions/`
- Wizard commit handlers on `default_commit_registry()`
- Pattern, provider, and storage plugin structure
- `BaseRuntime` hook wiring (`InstancePersistenceHook`, outbox, snapshots)
- Core engine APIs

---

## Further reading

- [ARCHITECTURE.md](ARCHITECTURE.md) — ApplicationHost, CQRS, outbox, compensation
- [DEVELOPMENT.md](DEVELOPMENT.md) — contributor bootstrap patterns
- [README.md](README.md) — quick start and CLI reference