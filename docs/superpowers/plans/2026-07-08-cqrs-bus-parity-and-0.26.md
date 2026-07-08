# CQRS Bus Parity + 0.25.8+ Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the host vs standalone CQRS wiring gap (MCP in-process impact/commit), unify service-domain transport via a `ServiceCqrsContributor` registry, and ship PyPI **0.26.0** with full design + revisioning operator parity.

**Architecture:** Business rules stay in `DesignService` / `DefinitionService` (ADR-008). CQRS remains transport-only. Pattern contributors (`patterns/_registry.CqrsContributor`) stay for pattern verbs; a parallel **service contributor registry** owns definitions/design revisioning transport. A single `collect_cqrs_catalog()` feeds both `ApplicationHost` and `wire_standalone_buses()`. Host-only projection queries remain explicitly gated.

**Tech Stack:** Python 3.12+, Palm CQRS buses, `ApplicationHost`, `ServerContext`, MCP in-process (`palm-mcp`), pytest, `just guard-common`

**ADR:** New [docs/adr/009-service-cqrs-contributors.md](../../adr/009-service-cqrs-contributors.md) (Task 1)

**Depends on:** 0.25.8 design dispatch (shipped locally — `feat(0.25.8): registry-driven design command dispatch`)

---

## Locked decisions

| # | Decision |
|---|----------|
| 1 | **No business logic in CQRS handlers** — handlers delegate to service methods or `common/persistence/*` primitives |
| 2 | **Service contributors, not pattern contributors** — `AnalyzeDefinitionImpactQuery` belongs to `definitions`, not wizard |
| 3 | **Host/standalone parity for service-required types** — every type `DefinitionService.ask/dispatch` emits must register in standalone mode |
| 4 | **Host-only projection types stay host-only** — `GetResourceInvocationsQuery`, `ListResourceInvocationsQuery`, projection-backed `ListInstancesQuery` paths documented in catalog |
| 5 | **MCP verification gate** — in-process `palm_design_impact` + `palm_design_commit` must pass before 0.26.0 cut |
| 6 | **0.26.0 bundles** 0.25.8–0.25.13 + parity work (single PyPI descriptive release per ADR-008) |

---

## File map (new / modified)

| Path | Responsibility |
|------|----------------|
| `docs/adr/009-service-cqrs-contributors.md` | ADR for service CQRS contributor model |
| `src/palm/services/_cqrs_registry.py` | `ServiceCqrsContributor`, `register_service_cqrs_contributor`, `iter_service_cqrs_contributors` |
| `src/palm/common/cqrs/catalog.py` | `collect_cqrs_command_types`, `collect_cqrs_query_types` with `mode="host"\|"standalone"` |
| `src/palm/services/definitions/bindings/cqrs/` | Impact query + migrate command handlers |
| `src/palm/services/design/bindings/cqrs/contributor.py` | Registers design contributor at import |
| `src/palm/common/runtimes/server/cqrs.py` | Standalone uses catalog + service wire hooks |
| `src/palm/app/host/cqrs_wiring.py` | Host uses catalog; remove duplicated definitions handlers |
| `src/palm/common/runtimes/server/context.py` | `wire_service_cqrs_contributors()` after services constructed |
| `src/palm/app/host/application_host.py` | Same service wire sequence |
| `tests/test_cqrs_bus_catalog_parity.py` | Catalog parity contract tests |
| `tests/test_definitions_cqrs_standalone.py` | Impact/migrate via standalone bootstrap |
| `tests/test_mcp_design_in_process.py` | MCP backend design flow without HTTP |

---

## Phase 0.25.8 — Design dispatch registry ✅ SHIPPED

**Status:** Complete locally (`1c8c01c`)

- `src/palm/common/operator/path_match.py`
- `src/palm/services/design/grammar.py`
- `src/palm/services/design/dispatch.py`
- `tests/test_design_dispatch.py`

**Verification:** `uv run pytest tests/test_design_dispatch.py -q`

---

## Phase 0.25.9 — Definitions CQRS bindings (standalone gap fix)

> **Unblocks MCP immediately.** Minimal slice before full registry refactor.

### Task 1: ADR-009 draft

**Files:**
- Create: `docs/adr/009-service-cqrs-contributors.md`

- [ ] **Step 1: Write ADR-009**

Document: service vs pattern contributors, `wire_*_service_cqrs` contract, parity requirement, relationship to ADR-004/008.

- [ ] **Step 2: Commit**

```bash
git add docs/adr/009-service-cqrs-contributors.md
git commit -m "docs(adr): 009 service CQRS contributors"
```

---

### Task 2: Definitions CQRS handlers

**Files:**
- Create: `src/palm/services/definitions/bindings/cqrs/__init__.py`
- Create: `src/palm/services/definitions/bindings/cqrs/handlers.py`
- Create: `src/palm/services/definitions/bindings/cqrs/registry.py`
- Create: `src/palm/services/definitions/bindings/cqrs/wiring.py`
- Test: `tests/test_definitions_cqrs_standalone.py`

- [ ] **Step 1: Write failing standalone impact test**

```python
# tests/test_definitions_cqrs_standalone.py
"""Definitions CQRS transport on standalone ServerContext (MCP bootstrap path)."""

from __future__ import annotations

from palm.definitions import FlowDefinition
from palm.runtimes.mcp.in_process import _bootstrap_server_context


def _wizard_body(name: str) -> dict:
    return FlowDefinition(
        name=name,
        pattern="wizard",
        options={"steps": [{"slug": "n", "title": "N", "prompt": "?"}]},
    ).to_dict()


def test_analyze_impact_via_standalone_context() -> None:
    ctx = _bootstrap_server_context()
    body = _wizard_body("standalone-impact-flow")
    ctx.definitions.create_flow(body)
    impact = ctx.definitions.analyze_impact("standalone-impact-flow", target_revision=2)
    assert impact["flow_id"] == "standalone-impact-flow"
    assert impact["target_revision"] == 2
    assert "summary" in impact


def test_migrate_instance_dry_run_via_standalone_context() -> None:
    ctx = _bootstrap_server_context()
    body = _wizard_body("standalone-migrate-flow")
    ctx.definitions.create_flow(body)
    # No instances — dry_run should succeed with zero rows or explicit empty result
    result = ctx.definitions.migrate_instance(
        "nonexistent-instance",
        target_revision=1,
        dry_run=True,
    )
    assert isinstance(result, dict)
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
uv run pytest tests/test_definitions_cqrs_standalone.py -v
```

Expected: `TypeError: No handler registered for AnalyzeDefinitionImpactQuery`

- [ ] **Step 3: Implement handlers**

`src/palm/services/definitions/bindings/cqrs/registry.py`:

```python
from palm.common.cqrs.command import MigrateInstanceCommand
from palm.common.cqrs.query import AnalyzeDefinitionImpactQuery

DEFINITIONS_COMMAND_TYPES: tuple[type, ...] = (MigrateInstanceCommand,)
DEFINITIONS_QUERY_TYPES: tuple[type, ...] = (AnalyzeDefinitionImpactQuery,)
```

`src/palm/services/definitions/bindings/cqrs/handlers.py`:

```python
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.command import Command, MigrateInstanceCommand
from palm.common.cqrs.query import AnalyzeDefinitionImpactQuery, Query
from palm.common.persistence.definition_impact import analyze_definition_impact_or_raise
from palm.common.persistence.instance_migration import migrate_instance

if TYPE_CHECKING:
    from palm.common.runtimes.base import BaseRuntime


class DefinitionsCommandHandler:
    def __init__(self, runtime: BaseRuntime) -> None:
        self._runtime = runtime

    def handle(self, command: Command) -> Any:
        if isinstance(command, MigrateInstanceCommand):
            return migrate_instance(
                self._runtime.repository,
                self._runtime.instance_manager,
                instance_id=command.instance_id,
                target_revision=command.target_revision,
                dry_run=command.dry_run,
            )
        raise TypeError(f"Unsupported definitions command: {type(command).__name__}")


class DefinitionsQueryHandler:
    def __init__(self, runtime: BaseRuntime) -> None:
        self._runtime = runtime

    def ask(self, query: Query) -> Any:
        if isinstance(query, AnalyzeDefinitionImpactQuery):
            return analyze_definition_impact_or_raise(
                self._runtime.repository,
                self._runtime.instance_manager.list_instances(),
                flow_id=query.flow_id,
                target_revision=query.target_revision,
            )
        raise TypeError(f"Unsupported definitions query: {type(query).__name__}")
```

`src/palm/services/definitions/bindings/cqrs/wiring.py`:

```python
from __future__ import annotations

from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.common.runtimes.base import BaseRuntime
from palm.services.definitions.bindings.cqrs.handlers import (
    DefinitionsCommandHandler,
    DefinitionsQueryHandler,
)
from palm.services.definitions.bindings.cqrs.registry import (
    DEFINITIONS_COMMAND_TYPES,
    DEFINITIONS_QUERY_TYPES,
)


def wire_definitions_service_cqrs(
    command_bus: CommandBus,
    query_bus: QueryBus,
    runtime: BaseRuntime,
) -> None:
    commands = DefinitionsCommandHandler(runtime)
    queries = DefinitionsQueryHandler(runtime)
    for command_type in DEFINITIONS_COMMAND_TYPES:
        command_bus.register(command_type, commands)
    for query_type in DEFINITIONS_QUERY_TYPES:
        query_bus.register(query_type, queries)
```

- [ ] **Step 4: Wire in ServerContext**

Modify `src/palm/common/runtimes/server/context.py` after `wire_design_service_cqrs`:

```python
from palm.services.definitions.bindings.cqrs.wiring import wire_definitions_service_cqrs

wire_definitions_service_cqrs(self._command_bus, self._query_bus, runtime)
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
uv run pytest tests/test_definitions_cqrs_standalone.py -v
```

- [ ] **Step 6: Run design tests (commit path uses definitions impact)**

```bash
uv run pytest tests/test_design_service.py tests/test_design_cqrs.py tests/test_design_dispatch.py -q
```

- [ ] **Step 7: Commit**

```bash
git add src/palm/services/definitions/bindings/cqrs/ \
  src/palm/common/runtimes/server/context.py \
  tests/test_definitions_cqrs_standalone.py
git commit -m "feat(0.25.9): definitions CQRS bindings for standalone bus"
```

---

### Task 3: MCP manual verification script

**Files:**
- Create: `tests/test_mcp_design_in_process.py`

- [ ] **Step 1: Write integration test (no FastMCP — backend duck-type)**

```python
# tests/test_mcp_design_in_process.py
"""Design propose → impact → commit via PalmInProcessBackend (MCP path)."""

from __future__ import annotations

from palm.definitions import FlowDefinition
from palm.runtimes.mcp.in_process import create_in_process_backend


def test_design_full_flow_in_process_backend() -> None:
    backend = create_in_process_backend()
    body = FlowDefinition(
        name="mcp-integration-flow",
        pattern="wizard",
        options={"steps": [{"slug": "n", "title": "N", "prompt": "?"}]},
    ).to_dict()
    proposed = backend.design_propose_flow(body=body)
    proposal_id = proposed["proposal"]["proposal_id"]
    assert proposed["validation"]["valid"] is True

    impact = backend.design_analyze_proposal_impact(proposal_id)
    assert impact["target_revision"] == 1

    committed = backend.design_commit_proposal(proposal_id)
    assert committed["revision"] == 1
    assert committed["flow_id"] == "mcp-integration-flow"
```

- [ ] **Step 2: Run test**

```bash
uv run pytest tests/test_mcp_design_in_process.py -v
```

Expected: PASS after Task 2

- [ ] **Step 3: Commit**

```bash
git add tests/test_mcp_design_in_process.py
git commit -m "test(0.25.9): MCP in-process design impact/commit integration"
```

---

## Phase 0.25.10 — Service CQRS contributor registry

### Task 4: Service contributor registry

**Files:**
- Create: `src/palm/services/_cqrs_registry.py`
- Test: `tests/test_service_cqrs_registry.py`

- [ ] **Step 1: Write registry test**

```python
# tests/test_service_cqrs_registry.py
from palm.services._cqrs_registry import (
    ServiceCqrsContributor,
    clear_service_cqrs_contributors,
    iter_service_cqrs_contributors,
    register_service_cqrs_contributors,
)


def test_register_and_iterate_service_contributors() -> None:
    clear_service_cqrs_contributors()

    def wire(_cmd, _qry, _ctx) -> None:
        pass

    register_service_cqrs_contributor(
        ServiceCqrsContributor(
            service_name="demo",
            command_types=(str,),
            query_types=(int,),
            wire=wire,
        )
    )
    contributors = iter_service_cqrs_contributors()
    assert len(contributors) == 1
    assert contributors[0].service_name == "demo"
```

- [ ] **Step 2: Run — expect FAIL**

```bash
uv run pytest tests/test_service_cqrs_registry.py -v
```

- [ ] **Step 3: Implement registry**

```python
# src/palm/services/_cqrs_registry.py
"""Service-domain CQRS contributor registry — transport wiring at bootstrap."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

WireFn = Callable[[Any, Any, Any], None]


@dataclass(frozen=True)
class ServiceCqrsContributor:
    service_name: str
    command_types: tuple[type, ...] = ()
    query_types: tuple[type, ...] = ()
    command_schemas: dict[type, Any] = field(default_factory=dict, compare=False, hash=False)
    query_schemas: dict[type, Any] = field(default_factory=dict, compare=False, hash=False)
    wire: WireFn | None = None


_lock = threading.RLock()
_contributors: dict[str, ServiceCqrsContributor] = {}


def register_service_cqrs_contributor(contributor: ServiceCqrsContributor) -> None:
    with _lock:
        existing = _contributors.get(contributor.service_name)
        if existing is contributor:
            return
        _contributors[contributor.service_name] = contributor


def iter_service_cqrs_contributors() -> tuple[ServiceCqrsContributor, ...]:
    with _lock:
        return tuple(_contributors.values())


def clear_service_cqrs_contributors() -> None:
    with _lock:
        _contributors.clear()


def wire_service_cqrs_contributors(command_bus: Any, query_bus: Any, wire_context: Any) -> None:
    """Drain registered contributors and invoke each ``wire`` hook."""
    for contributor in iter_service_cqrs_contributors():
        if contributor.wire is not None:
            contributor.wire(command_bus, query_bus, wire_context)
```

- [ ] **Step 4: Run test — PASS**

- [ ] **Step 5: Commit**

```bash
git add src/palm/services/_cqrs_registry.py tests/test_service_cqrs_registry.py
git commit -m "feat(0.25.10): ServiceCqrsContributor registry"
```

---

### Task 5: Definitions registers as service contributor

**Files:**
- Create: `src/palm/services/definitions/bindings/cqrs/contributor.py`
- Modify: `src/palm/services/definitions/__init__.py` (import contributor module at package load)
- Modify: `src/palm/common/runtimes/server/context.py`

- [ ] **Step 1: Add contributor module**

```python
# src/palm/services/definitions/bindings/cqrs/contributor.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from palm.services._cqrs_registry import ServiceCqrsContributor, register_service_cqrs_contributor
from palm.services.definitions.bindings.cqrs.registry import (
    DEFINITIONS_COMMAND_TYPES,
    DEFINITIONS_QUERY_TYPES,
)
from palm.services.definitions.bindings.cqrs.wiring import wire_definitions_service_cqrs


@dataclass(frozen=True)
class DefinitionsWireContext:
    runtime: Any


def _wire(command_bus: Any, query_bus: Any, ctx: DefinitionsWireContext) -> None:
    wire_definitions_service_cqrs(command_bus, query_bus, ctx.runtime)


def register_definitions_cqrs_contributor() -> None:
    register_service_cqrs_contributor(
        ServiceCqrsContributor(
            service_name="definitions",
            command_types=DEFINITIONS_COMMAND_TYPES,
            query_types=DEFINITIONS_QUERY_TYPES,
            wire=lambda bus, qbus, ctx: _wire(bus, qbus, ctx),
        )
    )


register_definitions_cqrs_contributor()
```

- [ ] **Step 2: Replace direct wire in ServerContext**

```python
import palm.services.definitions  # noqa: F401 — register definitions CQRS contributor
from palm.services._cqrs_registry import wire_service_cqrs_contributors
from palm.services.definitions.bindings.cqrs.contributor import DefinitionsWireContext

# After services constructed:
wire_service_cqrs_contributors(
    self._command_bus,
    self._query_bus,
    DefinitionsWireContext(runtime=runtime),
)
# Keep wire_design_service_cqrs until Task 6 migrates design
```

- [ ] **Step 3: Run standalone + design tests**

```bash
uv run pytest tests/test_definitions_cqrs_standalone.py tests/test_mcp_design_in_process.py -v
```

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(0.25.10): register definitions as ServiceCqrsContributor"
```

---

## Phase 0.25.11 — Unified CQRS catalog

### Task 6: `collect_cqrs_catalog()` single source of truth

**Files:**
- Create: `src/palm/common/cqrs/catalog.py`
- Modify: `src/palm/app/host/cqrs_wiring.py`
- Modify: `src/palm/common/runtimes/server/cqrs.py`
- Test: `tests/test_cqrs_bus_catalog_parity.py`

- [ ] **Step 1: Write parity test**

```python
# tests/test_cqrs_bus_catalog_parity.py
"""CQRS type catalog parity — service-required types must exist in standalone mode."""

from __future__ import annotations

import palm.services.definitions  # noqa: F401
import palm.services.design.bindings.cqrs.contributor  # noqa: F401 — after Task 7

from palm.common.cqrs.catalog import collect_cqrs_command_types, collect_cqrs_query_types
from palm.services.definitions.bindings.cqrs.registry import (
    DEFINITIONS_COMMAND_TYPES,
    DEFINITIONS_QUERY_TYPES,
)
from palm.services.design.bindings.cqrs.registry import DESIGN_COMMAND_TYPES, DESIGN_QUERY_TYPES

SERVICE_COMMAND_TYPES = DEFINITIONS_COMMAND_TYPES + DESIGN_COMMAND_TYPES
SERVICE_QUERY_TYPES = DEFINITIONS_QUERY_TYPES + DESIGN_QUERY_TYPES


def test_standalone_catalog_includes_service_command_types() -> None:
    standalone = set(collect_cqrs_command_types(mode="standalone"))
    for command_type in SERVICE_COMMAND_TYPES:
        assert command_type in standalone, f"{command_type.__name__} missing from standalone"


def test_standalone_catalog_includes_service_query_types() -> None:
    standalone = set(collect_cqrs_query_types(mode="standalone"))
    for query_type in SERVICE_QUERY_TYPES:
        assert query_type in standalone, f"{query_type.__name__} missing from standalone"


def test_host_catalog_is_superset_of_standalone_commands() -> None:
    host = set(collect_cqrs_command_types(mode="host"))
    standalone = set(collect_cqrs_command_types(mode="standalone"))
    assert standalone <= host
```

- [ ] **Step 2: Implement catalog**

```python
# src/palm/common/cqrs/catalog.py
from __future__ import annotations

from typing import Literal

import palm.patterns  # noqa: F401
import palm.services.definitions  # noqa: F401

from palm.common.cqrs.command import (
    CancelJobCommand,
    MigrateInstanceCommand,
    PreparePlansCommand,
    ProvideInputCommand,
    ResumeProcessCommand,
    SubmitFlowCommand,
    SubmitPlansCommand,
    SubmitProcessCommand,
)
from palm.common.cqrs.query import (
    AnalyzeDefinitionImpactQuery,
    GetFlowQuery,
    GetInstanceSnapshotQuery,
    GetInstanceStatusQuery,
    GetJobContextQuery,
    GetJobStatusQuery,
    GetProcessQuery,
    GetResourceInvocationsQuery,
    InspectInstanceQuery,
    ListFlowsQuery,
    ListInstanceSnapshotsQuery,
    ListInstancesQuery,
    ListJobStatusQuery,
    ListProcessesQuery,
    ListResourceInvocationsQuery,
)
from palm.patterns._registry import iter_cqrs_contributors
from palm.services._cqrs_registry import iter_service_cqrs_contributors

CatalogMode = Literal["host", "standalone"]

_HOST_ONLY_COMMAND_TYPES: tuple[type, ...] = ()
_HOST_ONLY_QUERY_TYPES: tuple[type, ...] = (
    GetResourceInvocationsQuery,
    ListResourceInvocationsQuery,
)


def _core_command_types() -> list[type]:
    return [
        SubmitFlowCommand,
        SubmitProcessCommand,
        ProvideInputCommand,
        ResumeProcessCommand,
        PreparePlansCommand,
        SubmitPlansCommand,
        CancelJobCommand,
        MigrateInstanceCommand,
    ]


def _core_query_types(*, mode: CatalogMode) -> list[type]:
    types: list[type] = [
        GetJobStatusQuery,
        GetJobContextQuery,
        InspectInstanceQuery,
        ListJobStatusQuery,
        ListInstancesQuery,
        GetInstanceStatusQuery,
        ListInstanceSnapshotsQuery,
        GetInstanceSnapshotQuery,
        ListFlowsQuery,
        AnalyzeDefinitionImpactQuery,
        GetFlowQuery,
        ListProcessesQuery,
        GetProcessQuery,
    ]
    if mode == "host":
        types.extend(_HOST_ONLY_QUERY_TYPES)
    return types


def collect_cqrs_command_types(*, mode: CatalogMode = "host") -> tuple[type, ...]:
    types = _core_command_types()
    for contributor in iter_cqrs_contributors():
        types.extend(contributor.command_types)
    for contributor in iter_service_cqrs_contributors():
        types.extend(contributor.command_types)
    return tuple(types)


def collect_cqrs_query_types(*, mode: CatalogMode = "host") -> tuple[type, ...]:
    types = _core_query_types(mode=mode)
    for contributor in iter_cqrs_contributors():
        types.extend(contributor.query_types)
    for contributor in iter_service_cqrs_contributors():
        types.extend(contributor.query_types)
    return tuple(types)
```

- [ ] **Step 3: Refactor host wiring to use catalog**

In `cqrs_wiring.py`, replace `collect_cqrs_command_types` / `collect_cqrs_query_types` bodies with imports from `palm.common.cqrs.catalog`.

Remove `_analyze_definition_impact` and `_migrate_instance` from `HostQueryHandlers` / `PalmCommandHandlers` — service contributor handlers own those types now (registered after generic host handler overwrites per-type).

**Important:** Host currently registers ONE handler object per type. Service wiring must `command_bus.register(MigrateInstanceCommand, definitions_handler)` **after** `wire_command_bus`, overwriting the host handler for that type. Same pattern as design 0.25.7.

- [ ] **Step 4: Refactor standalone wiring to use catalog**

In `cqrs.py` `wire_standalone_buses`, replace manual type lists with:

```python
from palm.common.cqrs.catalog import collect_cqrs_command_types, collect_cqrs_query_types

command_types = list(collect_cqrs_command_types(mode="standalone"))
query_types = list(collect_cqrs_query_types(mode="standalone"))
```

- [ ] **Step 5: Run parity + full CQRS tests**

```bash
uv run pytest tests/test_cqrs_bus_catalog_parity.py tests/test_definitions_cqrs_standalone.py \
  tests/test_design_cqrs.py tests/test_mcp_design_in_process.py -v
just guard-common
```

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(0.25.11): unified CQRS catalog for host and standalone"
```

---

## Phase 0.25.12 — Design migrates to service contributor

### Task 7: Design `ServiceCqrsContributor` + host wire cleanup

**Files:**
- Create: `src/palm/services/design/bindings/cqrs/contributor.py`
- Modify: `src/palm/app/host/cqrs_wiring.py` — remove hardcoded `DESIGN_*` imports
- Modify: `src/palm/common/cqrs/schemas.py` — drain service contributor schemas
- Modify: `src/palm/common/runtimes/server/context.py` — remove direct `wire_design_service_cqrs`

- [ ] **Step 1: Design contributor module**

```python
# src/palm/services/design/bindings/cqrs/contributor.py
from dataclasses import dataclass
from typing import Any

from palm.services._cqrs_registry import ServiceCqrsContributor, register_service_cqrs_contributor
from palm.services.design.bindings.cqrs.registry import DESIGN_COMMAND_TYPES, DESIGN_QUERY_TYPES
from palm.services.design.bindings.cqrs.schemas import (
    DESIGN_COMMAND_SCHEMAS,
    DESIGN_QUERY_SCHEMAS,
)
from palm.services.design.bindings.cqrs.wiring import wire_design_service_cqrs


@dataclass(frozen=True)
class DesignWireContext:
    design: Any


def register_design_cqrs_contributor() -> None:
    register_service_cqrs_contributor(
        ServiceCqrsContributor(
            service_name="design",
            command_types=DESIGN_COMMAND_TYPES,
            query_types=DESIGN_QUERY_TYPES,
            command_schemas=DESIGN_COMMAND_SCHEMAS,
            query_schemas=DESIGN_QUERY_SCHEMAS,
            wire=lambda bus, qbus, ctx: wire_design_service_cqrs(bus, qbus, ctx.design),
        )
    )
```

Call `register_design_cqrs_contributor()` at module bottom; import from `palm.services.design` package.

- [ ] **Step 2: Extend `build_schema_registry()`**

```python
from palm.services._cqrs_registry import iter_service_cqrs_contributors

for contributor in iter_service_cqrs_contributors():
    for command_type, schema in contributor.command_schemas.items():
        registry.register_command(command_type, schema)
    for query_type, schema in contributor.query_schemas.items():
        registry.register_query(query_type, schema)
```

Remove direct `register_design_cqrs_schemas(registry)` call.

- [ ] **Step 3: Unified wire in host + standalone**

Create `src/palm/services/_cqrs_wiring.py`:

```python
def wire_all_service_cqrs(command_bus, query_bus, *, runtime, design) -> None:
    from palm.services.definitions.bindings.cqrs.contributor import DefinitionsWireContext
    from palm.services.design.bindings.cqrs.contributor import DesignWireContext
    from palm.services._cqrs_registry import wire_service_cqrs_contributors

    wire_service_cqrs_contributors(
        command_bus,
        query_bus,
        {
            "definitions": DefinitionsWireContext(runtime=runtime),
            "design": DesignWireContext(design=design),
        },
    )
```

Update `wire_service_cqrs_contributors` to accept `dict[str, Any]` keyed by `service_name`.

- [ ] **Step 4: Run full test suite**

```bash
uv run pytest tests/test_cqrs_bus_catalog_parity.py tests/test_design_cqrs.py \
  tests/test_design_dispatch.py tests/test_mcp_design_in_process.py -v
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(0.25.12): design ServiceCqrsContributor; drain schema registry"
```

---

## Phase 0.25.13 — Documentation + AGENTS sync

### Task 8: Docs and constitution

**Files:**
- Modify: `AGENTS.md` — service CQRS contributor row in extension table
- Modify: `docs/MCP.md` — note in-process requires service CQRS parity
- Modify: `docs/superpowers/plans/2026-07-07-design-service-plus.md` — mark 0.25.8–0.25.13 complete
- Modify: `docs/STATUS.md` — phase table

- [ ] **Step 1: Update AGENTS.md extension table**

Add row:

| Service CQRS transport | `palm/services/<domain>/bindings/cqrs/` | `ServiceCqrsContributor` in `palm/services/_cqrs_registry.py`; wire via `wire_all_service_cqrs()` |

- [ ] **Step 2: Commit docs**

```bash
git commit -m "docs(0.25.13): service CQRS contributor guide and status sync"
```

---

## Phase 0.26.0 — PyPI release cut

### Task 9: Release gate

- [ ] **Step 1: Full verification**

```bash
uv run pytest tests/test_design_service.py tests/test_design_cqrs.py \
  tests/test_design_dispatch.py tests/test_definitions_cqrs_standalone.py \
  tests/test_cqrs_bus_catalog_parity.py tests/test_mcp_design_in_process.py \
  tests/test_rest_design_routes.py tests/test_instance_migration.py -v
just guard-common
just docs-check
```

- [ ] **Step 2: MCP live verification (restart palm-mcp after code changes)**

1. `palm_system_doctor` — version 0.26.0
2. `palm_design_propose_flow` → `palm_design_impact` → `palm_design_commit`
3. `palm_assist(alias="design/impact", params={proposal_id})` — assistant shape

- [ ] **Step 3: CHANGELOG + RELEASE-0.26.0.md**

- [ ] **Step 4: Version bump in `pyproject.toml`**

- [ ] **Step 5: Commit + tag**

```bash
git commit -m "chore(0.26.0): release notes and version bump"
git tag v0.26.0
```

---

## Self-review (plan author)

| Spec requirement | Task |
|------------------|------|
| Standalone impact/migrate | Task 2, 5 |
| Service contributor registry | Task 4–7 |
| Single catalog | Task 6 |
| Design dispatch (0.25.8) | Phase header ✅ |
| MCP verification gate | Task 3, 9 |
| ADR | Task 1 |
| No business logic in handlers | Locked decision #1 |
| Host-only projections documented | `catalog.py` `_HOST_ONLY_QUERY_TYPES` |

**Placeholder scan:** None.

---

## Execution handoff

**Plan saved to** `docs/superpowers/plans/2026-07-08-cqrs-bus-parity-and-0.26.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks
2. **Inline Execution** — implement in this session with checkpoints after each phase

**Which approach?**