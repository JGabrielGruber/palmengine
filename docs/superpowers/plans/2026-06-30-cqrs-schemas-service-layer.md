# 0.15 CQRS Schemas + Service Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unify Palm's user-facing API behind a service layer that consumes schema-described CQRS, with instance-centric execution as the primary metaphor.

**Architecture:** Extend `CqrsContributor` with `DictStateSchema` maps; add `CqrsSchemaRegistry` for validation and introspection. Build `BaseService` + `InternalService` in `palm/common/services/` that compose CQRS (many-to-one). Runtimes become thin adapters. Later extract `DefinitionService` and `ExecutionService` with `InstanceSession` / `ReplSession`.

**Tech Stack:** Python 3.12, dataclasses, `DictStateSchema` (`palm/core/context/state_schema.py`), existing `CommandBus`/`QueryBus`, pytest, `uv run pytest`, `just check`.

**Design spec:** [docs/superpowers/specs/2026-06-30-cqrs-schemas-service-layer-design.md](../specs/2026-06-30-cqrs-schemas-service-layer-design.md)

---

## File map

| File | Responsibility |
|------|----------------|
| `src/palm/common/cqrs/schemas.py` | `ValidationResult`, `CqrsSchemaRegistry` |
| `src/palm/common/cqrs/schema_bootstrap.py` | Core command/query schema registration |
| `src/palm/patterns/_registry.py` | Extend `CqrsContributor` with schema dicts |
| `src/palm/patterns/wizard/bindings/cqrs/schemas.py` | Wizard CQRS schemas |
| `src/palm/common/services/base.py` | `BaseService` — validate + dispatch/ask |
| `src/palm/common/services/errors.py` | `ServiceValidationError` |
| `src/palm/common/services/views.py` | `InspectView`, `DoctorReport`, etc. |
| `src/palm/common/services/internal.py` | `InternalService` — operational API |
| `src/palm/common/services/definition.py` | `DefinitionService` (phase 0.15d) |
| `src/palm/common/services/execution.py` | `ExecutionService` (phase 0.15e) |
| `src/palm/common/services/session.py` | `InstanceSession`, `ReplSession` (phase 0.15e) |
| `src/palm/app/host/cqrs_wiring.py` | Wire schema registry at bootstrap |
| `src/palm/app/host/application_host.py` | Expose `.services` / `.internal` |
| `src/palm/common/runtimes/server/context.py` | Expose services on `ServerContext` |
| `src/palm/runtimes/server/surfaces/rest/handlers/*.py` | Thin handlers → InternalService |
| `src/palm/runtimes/mcp/tools.py` | In-process service calls |
| `tests/test_cqrs_schemas.py` | Schema registry unit tests |
| `tests/test_services_internal.py` | InternalService unit tests |

---

## Phase 0.15a — CQRS Schemas

### Task 1: ValidationResult and CqrsSchemaRegistry skeleton

**Files:**
- Create: `src/palm/common/cqrs/schemas.py`
- Create: `tests/test_cqrs_schemas.py`
- Modify: `src/palm/common/cqrs/__init__.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_cqrs_schemas.py
from __future__ import annotations

from dataclasses import dataclass

from palm.common.cqrs.command import Command
from palm.common.cqrs.schemas import CqrsSchemaRegistry, ValidationResult
from palm.core.context.state_schema import DictStateSchema


@dataclass(frozen=True)
class _SampleCommand(Command):
    name: str
    count: int = 1


_SAMPLE_SCHEMA = DictStateSchema(
    {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "count": {"type": "integer"},
        },
        "required": ["name"],
    }
)


def test_registry_register_and_lookup() -> None:
    registry = CqrsSchemaRegistry()
    registry.register_command(_SampleCommand, _SAMPLE_SCHEMA)
    assert registry.schema_for(_SampleCommand) is _SAMPLE_SCHEMA
    assert registry.schema_for(str) is None


def test_registry_validate_dataclass_as_dict() -> None:
    registry = CqrsSchemaRegistry()
    registry.register_command(_SampleCommand, _SAMPLE_SCHEMA)
    result = registry.validate(_SampleCommand(name="demo"))
    assert result.ok is True
    assert result.errors == []


def test_registry_validate_rejects_invalid() -> None:
    registry = CqrsSchemaRegistry()
    registry.register_command(_SampleCommand, _SAMPLE_SCHEMA)
    result = registry.validate(_SampleCommand(name=""))
    assert result.ok is False
    assert len(result.errors) >= 1
    assert result.details[0]["field"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cqrs_schemas.py -v`  
Expected: FAIL — `ModuleNotFoundError: palm.common.cqrs.schemas`

- [ ] **Step 3: Implement minimal registry**

```python
# src/palm/common/cqrs/schemas.py
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any

from palm.core.context.state_schema import DictStateSchema


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[str]
    details: list[dict[str, str]]


class CqrsSchemaRegistry:
    def __init__(self) -> None:
        self._commands: dict[type, DictStateSchema] = {}
        self._queries: dict[type, DictStateSchema] = {}

    def register_command(self, command_type: type, schema: DictStateSchema) -> None:
        self._commands[command_type] = schema

    def register_query(self, query_type: type, schema: DictStateSchema) -> None:
        self._queries[query_type] = schema

    def schema_for(self, cqrs_type: type) -> DictStateSchema | None:
        return self._commands.get(cqrs_type) or self._queries.get(cqrs_type)

    def validate(self, instance: Any) -> ValidationResult:
        schema = self.schema_for(type(instance))
        if schema is None:
            return ValidationResult(ok=True, errors=[], details=[])
        payload = asdict(instance) if is_dataclass(instance) else dict(instance)
        errors = list(schema.validate_state(payload))
        details = [{"field": _field_from_error(e), "message": e} for e in errors]
        return ValidationResult(ok=not errors, errors=errors, details=details)


def _field_from_error(message: str) -> str:
    if message.startswith("missing required key: "):
        return message.removeprefix("missing required key: ")
    if ": " in message:
        return message.split(": ", 1)[0]
    return "body"
```

Export from `src/palm/common/cqrs/__init__.py`: `CqrsSchemaRegistry`, `ValidationResult`.

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_cqrs_schemas.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/palm/common/cqrs/schemas.py src/palm/common/cqrs/__init__.py tests/test_cqrs_schemas.py
git commit -m "feat(cqrs): add CqrsSchemaRegistry and ValidationResult"
```

---

### Task 2: Extend CqrsContributor with schema maps

**Files:**
- Modify: `src/palm/patterns/_registry.py`
- Modify: `tests/test_cqrs_schemas.py`

- [ ] **Step 1: Write failing test for contributor schema collection**

```python
# append to tests/test_cqrs_schemas.py
from palm.patterns._registry import CqrsContributor, register_cqrs_contributor, iter_cqrs_contributors


def test_registry_collects_contributor_schemas() -> None:
    from palm.common.cqrs.schemas import build_schema_registry

    @dataclass(frozen=True)
    class _PatCmd(Command):
        slug: str

    schema = DictStateSchema({"type": "object", "properties": {"slug": {"type": "string"}}, "required": ["slug"]})
    register_cqrs_contributor(
        CqrsContributor(
            pattern_name="_test_pattern",
            command_types=(_PatCmd,),
            command_schemas={_PatCmd: schema},
        )
    )
    registry = build_schema_registry()
    assert registry.schema_for(_PatCmd) is schema
```

- [ ] **Step 2: Run test — expect FAIL** (`build_schema_registry` missing, `CqrsContributor` has no `command_schemas`)

- [ ] **Step 3: Extend CqrsContributor**

In `src/palm/patterns/_registry.py`, add to `CqrsContributor`:

```python
command_schemas: dict[type, Any] = field(default_factory=dict)  # DictStateSchema
query_schemas: dict[type, Any] = field(default_factory=dict)
```

Import `field` from dataclasses if not already.

- [ ] **Step 4: Add build_schema_registry**

In `src/palm/common/cqrs/schemas.py`:

```python
import palm.patterns  # noqa: F401
from palm.common.cqrs.command import CancelJobCommand, ProvideInputCommand, ...
from palm.common.cqrs.query import ListInstancesQuery, ...
from palm.patterns._registry import iter_cqrs_contributors
from palm.common.cqrs.schema_bootstrap import register_core_schemas


def build_schema_registry() -> CqrsSchemaRegistry:
    registry = CqrsSchemaRegistry()
    register_core_schemas(registry)
    for contributor in iter_cqrs_contributors():
        for cmd_type, schema in contributor.command_schemas.items():
            registry.register_command(cmd_type, schema)
        for qry_type, schema in contributor.query_schemas.items():
            registry.register_query(qry_type, schema)
    return registry
```

- [ ] **Step 5: Run tests — PASS (use test isolation: clear contributor in teardown if needed)**

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(cqrs): extend CqrsContributor with schema maps and build_schema_registry"
```

---

### Task 3: Core command/query schemas

**Files:**
- Create: `src/palm/common/cqrs/schema_bootstrap.py`
- Modify: `src/palm/runtimes/server/surfaces/rest/schemas.py` (read for shapes)
- Modify: `tests/test_cqrs_schemas.py`

- [ ] **Step 1: Write test that core commands have schemas**

```python
def test_core_submit_flow_command_has_schema() -> None:
    from palm.common.cqrs.command import SubmitFlowCommand
    from palm.common.cqrs.schemas import build_schema_registry

    registry = build_schema_registry()
    schema = registry.schema_for(SubmitFlowCommand)
    assert schema is not None
    result = registry.validate(SubmitFlowCommand(flow="demo"))
    assert result.ok is True
```

- [ ] **Step 2: Implement register_core_schemas**

Mirror shapes from `rest/schemas.py` — at minimum:

- `SubmitFlowCommand`, `SubmitProcessCommand`, `ProvideInputCommand`, `ResumeProcessCommand`
- `PreparePlansCommand`, `SubmitPlansCommand`, `CancelJobCommand`
- `ListInstancesQuery`, `GetInstanceStatusQuery`, `ListJobStatusQuery`, `GetJobStatusQuery`
- `GetJobContextQuery`, `ListFlowsQuery`, `GetFlowQuery`, `ListProcessesQuery`, `GetProcessQuery`

Use `DictStateSchema` with `type: object` and appropriate properties. Dataclass fields map 1:1 to schema keys via `asdict`.

- [ ] **Step 3: Run tests — PASS**

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(cqrs): register core command and query schemas"
```

---

### Task 4: Wizard pattern CQRS schemas

**Files:**
- Create: `src/palm/patterns/wizard/bindings/cqrs/schemas.py`
- Modify: `src/palm/patterns/wizard/app.py`
- Modify: `tests/test_cqrs_schemas.py`

- [ ] **Step 1: Write test**

```python
def test_wizard_commands_have_schemas() -> None:
    from palm.common.cqrs.schemas import build_schema_registry
    from palm.patterns.wizard.bindings.cqrs.commands import (
        ProvideWizardInputCommand,
        SubmitWizardCommand,
    )

    registry = build_schema_registry()
    assert registry.schema_for(SubmitWizardCommand) is not None
    assert registry.schema_for(ProvideWizardInputCommand) is not None
```

- [ ] **Step 2: Create wizard schemas** — copy shapes from `SUBMIT_WIZARD_BODY`, `WIZARD_INPUT_BODY`, `WIZARD_BACKTRACK_BODY` in `rest/schemas.py`

- [ ] **Step 3: Wire in wizard `app.py` ready()**

```python
from palm.patterns.wizard.bindings.cqrs.schemas import WIZARD_COMMAND_SCHEMAS, WIZARD_QUERY_SCHEMAS

register_cqrs_contributor(
    CqrsContributor(
        ...
        command_schemas=WIZARD_COMMAND_SCHEMAS,
        query_schemas=WIZARD_QUERY_SCHEMAS,
    )
)
```

- [ ] **Step 4: Run tests — PASS**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(wizard): register CQRS schemas for wizard commands and queries"
```

---

## Phase 0.15b — BaseService + InternalService

### Task 5: Service errors and BaseService

**Files:**
- Create: `src/palm/common/services/errors.py`
- Create: `src/palm/common/services/base.py`
- Create: `tests/test_services_base.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_services_base.py
from dataclasses import dataclass

from palm.common.cqrs import CommandBus
from palm.common.cqrs.command import Command
from palm.common.cqrs.schemas import CqrsSchemaRegistry, ValidationResult
from palm.common.services.base import BaseService
from palm.common.services.errors import ServiceValidationError
from palm.core.context.state_schema import DictStateSchema


@dataclass(frozen=True)
class _Cmd(Command):
    name: str


def test_base_service_rejects_invalid_command() -> None:
    bus = CommandBus()
    registry = CqrsSchemaRegistry()
    registry.register_command(
        _Cmd,
        DictStateSchema({"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}),
    )
    svc = BaseService(commands=bus, queries=QueryBus(), schemas=registry)

    class _Handler:
        def handle(self, command: Command) -> str:
            return "ok"

    bus.register(_Cmd, _Handler())

    try:
        svc.dispatch(_Cmd(name=""))
        assert False, "expected ServiceValidationError"
    except ServiceValidationError as exc:
        assert exc.result.ok is False
```

- [ ] **Step 2: Implement**

```python
# src/palm/common/services/errors.py
@dataclass(frozen=True)
class ServiceValidationError(ValueError):
    result: ValidationResult
    cqrs_type: type

# src/palm/common/services/base.py
class BaseService:
    def __init__(self, *, commands: CommandBus, queries: QueryBus, schemas: CqrsSchemaRegistry) -> None:
        self._commands = commands
        self._queries = queries
        self._schemas = schemas

    def dispatch(self, command: Command) -> Any:
        result = self._schemas.validate(command)
        if not result.ok:
            raise ServiceValidationError(result, type(command))
        return self._commands.dispatch(command)

    def ask(self, query: Query) -> Any:
        result = self._schemas.validate(query)
        if not result.ok:
            raise ServiceValidationError(result, type(query))
        return self._queries.ask(query)
```

- [ ] **Step 3: Run tests — PASS**

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(services): add BaseService with schema validation"
```

---

### Task 6: InternalService — inspect_instance and list_jobs

**Files:**
- Create: `src/palm/common/services/views.py`
- Create: `src/palm/common/services/internal.py`
- Create: `tests/test_services_internal.py`

- [ ] **Step 1: Write failing test with mocked buses**

Test `InternalService.inspect_instance` dispatches `GetWizardStatusQuery` when instance pattern is wizard (mock query bus returns row with pattern metadata).

Test `InternalService.list_jobs` calls `ListJobStatusQuery`.

- [ ] **Step 2: Implement InternalService subset**

```python
class InternalService(BaseService):
    def list_jobs(self, *, status: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        return self.ask(ListJobStatusQuery(status=status, limit=limit))

    def inspect_instance(self, instance_id: str) -> dict[str, Any]:
        from palm.patterns.wizard.bindings.cqrs.queries import GetWizardStatusQuery
        row = self.ask(GetWizardStatusQuery(instance_id=instance_id))
        if row is not None:
            return row if isinstance(row, dict) else row.to_dict()
        inst = self.ask(GetInstanceStatusQuery(instance_id=instance_id))
        if inst is None:
            raise InstanceNotFoundServiceError(instance_id)
        ctx = self.ask(GetJobContextQuery(job_id=str(inst.get("job_id", instance_id))))
        return ctx
```

Add `InstanceNotFoundServiceError` to `errors.py`.

- [ ] **Step 3: Run tests — PASS**

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(services): add InternalService with list_jobs and inspect_instance"
```

---

### Task 7: Wire services on ApplicationHost and ServerContext

**Files:**
- Modify: `src/palm/app/host/application_host.py`
- Modify: `src/palm/common/runtimes/server/context.py`
- Modify: `tests/test_application_host_cqrs.py`

- [ ] **Step 1: Write test that host exposes internal service**

```python
def test_application_host_exposes_internal_service(cli_host) -> None:
    assert hasattr(cli_host, "internal")
    rows = cli_host.internal.list_jobs(limit=5)
    assert isinstance(rows, list)
```

- [ ] **Step 2: Wire in ApplicationHost._wire_cqrs**

```python
from palm.common.cqrs.schemas import build_schema_registry
from palm.common.services.internal import InternalService

self._schema_registry = build_schema_registry()
self._internal = InternalService(
    commands=self._command_bus,
    queries=self._query_bus,
    schemas=self._schema_registry,
)

@property
def internal(self) -> InternalService:
    return self._internal
```

- [ ] **Step 3: Wire ServerContext similarly** (standalone mode builds own registry)

- [ ] **Step 4: Run `uv run pytest tests/test_application_host_cqrs.py -v` — PASS**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(host): wire InternalService on ApplicationHost and ServerContext"
```

---

### Task 8: REST handlers delegate to InternalService

**Files:**
- Modify: `src/palm/runtimes/server/surfaces/rest/handlers/wizard.py`
- Modify: `src/palm/runtimes/server/surfaces/rest/handlers/jobs.py`
- Modify: `src/palm/runtimes/server/surfaces/rest/handlers/instances.py`
- Test: existing REST integration tests

- [ ] **Step 1: Refactor get_wizard handler**

```python
def get_wizard(ctx: ServerContext, request: ServerRequest, *, instance_id: str) -> ServerResponse:
    try:
        row = ctx.internal.inspect_instance(instance_id)
    except InstanceNotFoundServiceError:
        return errors.wizard_not_found(instance_id)
    return ok(read_model_body(row))
```

- [ ] **Step 2: Refactor list_jobs, get_job_context similarly**

- [ ] **Step 3: Run REST tests**

Run: `uv run pytest tests/ -k "rest or wizard" -v --tb=short` (or project equivalent)

- [ ] **Step 4: Commit**

```bash
git commit -m "refactor(rest): delegate inspect routes to InternalService"
```

---

## Phase 0.15c — MCP in-process

### Task 9: MCP tools call InternalService directly

**Files:**
- Modify: `src/palm/runtimes/mcp/server.py`
- Modify: `src/palm/runtimes/mcp/tools.py`
- Modify: `src/palm/runtimes/mcp/config.py`

- [ ] **Step 1: Add optional in-process backend to PalmMcpConfig**

When `PALM_MCP_IN_PROCESS=1` or host attached, tools receive `InternalService` instead of `PalmRestClient`.

- [ ] **Step 2: Refactor palm_inspect_instance**

```python
def palm_inspect_instance(instance_id: str, ...) -> dict[str, Any]:
    view = internal.inspect_instance(instance_id)
    return compact_wizard_inspect(view, ...)
```

- [ ] **Step 3: Keep PalmRestClient for remote mode** (document in config)

- [ ] **Step 4: Run MCP-related tests**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(mcp): in-process InternalService path for operator tools"
```

---

## Phase 0.15d — DefinitionService

### Task 10: Extract catalog methods

**Files:**
- Create: `src/palm/common/services/definition.py`
- Modify: `src/palm/runtimes/server/surfaces/rest/handlers/catalog.py`
- Create: `tests/test_services_definition.py`

- [ ] **Step 1: Implement DefinitionService** — `list_flows`, `get_flow`, `validate_flow`, `list_processes`, `get_process`, `list_resources`, `get_resource`

- [ ] **Step 2: Move methods from InternalService if duplicated**

- [ ] **Step 3: Wire on host/context as `.definition`**

- [ ] **Step 4: Update catalog REST handlers**

- [ ] **Step 5: Tests + commit**

```bash
git commit -m "feat(services): add DefinitionService and wire catalog routes"
```

---

## Phase 0.15e — ExecutionService + Sessions

### Task 11: InstanceSession

**Files:**
- Create: `src/palm/common/services/session.py`
- Create: `src/palm/common/services/execution.py`
- Create: `tests/test_services_execution.py`

- [ ] **Step 1: Write tests for instance-centric API**

```python
def test_execution_on_returns_session(mock_host) -> None:
    session = mock_host.execution.on("inst_1")
    assert session.instance_id == "inst_1"

def test_session_input_dispatches_wizard_command(mock_host, wizard_instance) -> None:
    view = mock_host.execution.on(wizard_instance).input("yes")
    assert view["status"] in ("WAITING_FOR_INPUT", "RUNNING", "SUCCEEDED")
```

- [ ] **Step 2: Implement ExecutionService.on() and InstanceSession**

Pattern branching: read instance metadata → `ProvideWizardInputCommand` vs `ProvideInputCommand`.

- [ ] **Step 3: Convenience methods run_flow / run_wizard**

- [ ] **Step 4: ReplSession for CLI**

Modify CLI REPL to hold `ReplSession` tracking active instance.

- [ ] **Step 5: Move submit/input/resume from InternalService to ExecutionService**

- [ ] **Step 6: Update REST wizard write routes to `ctx.execution.on(id).input(...)`**

- [ ] **Step 7: Tests + commit**

```bash
git commit -m "feat(services): add ExecutionService, InstanceSession, and ReplSession"
```

---

## Phase 0.15f — Documentation

### Task 12: Docs and ADR

**Files:**
- Create: `docs/VISION-0.15.md`
- Create: `docs/adr/004-cqrs-schemas-service-layer.md`
- Modify: `ARCHITECTURE.md`, `AGENTS.md`, `STATUS.md`, `docs/MCP.md`, `docs/llms.txt`

- [ ] **Step 1: Write VISION-0.15.md** following `docs/VISION-0.13.md` structure

- [ ] **Step 2: Write ADR 004** — decision, consequences, alternatives (Pydantic, 1:1 CQRS routes)

- [ ] **Step 3: Add ARCHITECTURE section** — service layer diagram, runtime adapter rule

- [ ] **Step 4: Update AGENTS.md** — extension table row for `register_cqrs_contributor` schemas + services

- [ ] **Step 5: Run `just docs-check` and `just check`**

- [ ] **Step 6: Commit**

```bash
git commit -m "docs: add 0.15 vision, ADR 004, and architecture updates"
```

---

## Final verification

- [ ] Run: `just check`
- [ ] Run: `uv run pytest tests/test_cqrs_schemas.py tests/test_services_base.py tests/test_services_internal.py -v`
- [ ] Confirm `rest/schemas.py` duplicates removed or marked deprecated where registry replaces them
- [ ] Confirm MCP local mode avoids HTTP round-trip

---

## Plan self-review (completed)

| Spec section | Task coverage |
|--------------|---------------|
| CQRS Schemas | Tasks 1–4 |
| BaseService | Task 5 |
| InternalService | Tasks 6–8 |
| Runtimes thin adapters | Tasks 8–9 |
| DefinitionService | Task 10 |
| ExecutionService + Sessions | Task 11 |
| Extension (CqrsContributor) | Tasks 2, 4 |
| Documentation | Task 12 |

No TBD placeholders. Type names consistent: `CqrsSchemaRegistry`, `InternalService`, `InstanceSession`, `ServiceValidationError`.