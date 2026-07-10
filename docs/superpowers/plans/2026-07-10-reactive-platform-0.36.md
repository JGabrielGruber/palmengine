# Reactive Platform 0.36–0.37 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the first two trains of [VISION-0.36](../../VISION-0.36.md): (A) virtual analytics views + schema/doctor/assist discovery (0.36), then (B) WorkIntent enqueue + definition triggers + `resource.changed` drain-when-able (0.37 foundation).

**Architecture:** Analytics remains a thin read path. Virtual views are declared on `metadata.analytics` and evaluated at query time via existing transforms (`count_by`). Deferred reactions use pure `WorkIntent` data (core), durable enqueue via extended outbox (common), and host drain when able—never a fat WorkEngine that runs flows inside core. Triggers are definition metadata → enqueue only.

**Tech Stack:** Python 3.12, existing `AnalyticsService`, `count_by` transform, `OutboxStore` / `OutboxBackgroundService`, `ApplicationHost`, `DefinitionService`, pytest, `examples/definitions/todos/`.

**Spec:** [docs/VISION-0.36.md](../../VISION-0.36.md) · baseline code: `src/palm/services/analytics/`, `src/palm/common/events/outbox.py`, `src/palm/app/host/outbox_service.py`

**Out of scope for this plan:** 0.38 journal offsets, 0.39 DashboardDefinition, Bot, analytics joins, OLAP.

---

## File map (decomposition)

### Train A — 0.36 virtual data plane

| Path | Responsibility |
|------|----------------|
| `src/palm/services/analytics/exposure.py` | Parse `source`, `transform`, `materialize`; keep unknown-key ignore |
| `src/palm/services/analytics/virtual.py` | Apply view transform ops on row lists (compose transform registry) |
| `src/palm/services/analytics/schema_roles.py` | Extract field roles from `output_schema` / analytics.fields |
| `src/palm/services/analytics/service.py` | describe enrichment; query virtual path before/instead of own invoke |
| `src/palm/services/analytics/datasets.py` | list/resolve unchanged gates; optional view flag on list rows |
| `src/palm/services/system/service.py` (or doctor contributor) | Published-dataset preflight checks |
| `src/palm/services/assist/catalog/menu.py` | `section=datasets` menu page |
| `examples/definitions/todos/resources.py` | Virtual priority view (no second put required for query) |
| `tests/test_analytics_exposure.py` | Extended parse tests |
| `tests/test_analytics_virtual.py` | Virtual query tests |
| `tests/test_analytics_schema_roles.py` | Field catalog tests |
| `tests/test_analytics_doctor.py` | Doctor preflight tests |
| `tests/test_assist_menu_datasets.py` | Menu section tests |

### Train B — 0.37 work intents + triggers (foundation)

| Path | Responsibility |
|------|----------------|
| `src/palm/core/work/intent.py` | Pure `WorkIntent` dataclass |
| `src/palm/core/work/__init__.py` | Export |
| `src/palm/common/work/store.py` | Durable store (outbox-backed or parallel keys under `palm:work:`) |
| `src/palm/common/work/coalesce.py` | REPLACE semantics by `coalesce_key` |
| `src/palm/common/triggers/parse.py` | Parse `metadata.triggers` / `analytics.refresh` |
| `src/palm/common/triggers/registry.py` | Match events → WorkIntents |
| `src/palm/common/resource/change_emit.py` | After mutating invoke → Event + optional enqueue |
| `src/palm/app/host/work_drain_service.py` | Drain when able → execution submit |
| `src/palm/app/host/application_host.py` | Wire drain + trigger attach |
| `tests/test_work_intent.py` | Pure type + coalesce |
| `tests/test_work_store.py` | Enqueue/claim/ack |
| `tests/test_triggers_parse.py` | Trigger parse |
| `tests/test_resource_changed_work.py` | put → intent → drain (integration) |

---

# Train A — 0.36 Contracts & virtual views

### Task 1: Extend analytics exposure parse

**Files:**
- Modify: `src/palm/services/analytics/exposure.py`
- Modify: `tests/test_analytics_exposure.py`

- [ ] **Step 1: Write failing tests for source/transform/materialize**

```python
def test_parse_virtual_view_source_and_transform() -> None:
    exp = parse_analytics_exposure(
        {
            "analytics": {
                "published": True,
                "kind": "view",
                "source": "palm-todos",
                "materialize": False,
                "transform": {"op": "count_by", "field": "priority"},
            }
        }
    )
    assert exp.published is True
    assert exp.kind == "view"
    assert exp.source == "palm-todos"
    assert exp.materialize is False
    assert exp.transform == {"op": "count_by", "field": "priority"}


def test_materialize_defaults_true_when_absent_for_backward_compat() -> None:
    """Existing views without source stay materialize-style (invoke own resource)."""
    exp = parse_analytics_exposure(
        {"analytics": {"published": True, "kind": "view", "derived_from": ["palm-todos"]}}
    )
    assert exp.source is None
    assert exp.materialize is True  # no virtual path
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
uv run pytest tests/test_analytics_exposure.py::test_parse_virtual_view_source_and_transform -v
```

Expected: FAIL (`AnalyticsExposure` has no `source`)

- [ ] **Step 3: Implement parse fields**

In `exposure.py`:

- Add to `_KNOWN_KEYS`: `"source"`, `"transform"`, `"materialize"`, `"fields"`
- Add on `AnalyticsExposure`:
  - `source: str | None = None`
  - `transform: dict[str, Any] = field(default_factory=dict)`
  - `materialize: bool = True`  # default True when no source; if source set and materialize omitted → False
  - `fields: tuple[dict[str, Any], ...] = ()`  # raw field role entries for Task 4
- Parse rules:
  - `source`: optional non-empty str
  - `transform`: optional dict (known keys later validated in virtual.py)
  - `materialize`: if key absent and `source` set → `False`; if key absent and no source → `True`; if bool present use it
- Include new fields in `to_dict()` when non-default

- [ ] **Step 4: Run tests — expect PASS**

```bash
uv run pytest tests/test_analytics_exposure.py -q
```

- [ ] **Step 5: Commit**

```bash
git add src/palm/services/analytics/exposure.py tests/test_analytics_exposure.py
git commit -m "feat(analytics): 0.36.1 exposure source/transform/materialize"
```

---

### Task 2: Virtual view evaluation helper

**Files:**
- Create: `src/palm/services/analytics/virtual.py`
- Create: `tests/test_analytics_virtual.py`

- [ ] **Step 1: Write failing tests**

```python
from palm.services.analytics.virtual import apply_view_transform

def test_apply_count_by() -> None:
    rows = [
        {"title": "a", "priority": "high"},
        {"title": "b", "priority": "low"},
        {"title": "c", "priority": "high"},
    ]
    out = apply_view_transform(rows, {"op": "count_by", "field": "priority"})
    assert out == [
        {"priority": "high", "count": 2},
        {"priority": "low", "count": 1},
    ]


def test_unknown_op_raises() -> None:
    import pytest
    with pytest.raises(ValueError, match="op"):
        apply_view_transform([], {"op": "nope"})
```

- [ ] **Step 2: Run — expect FAIL (module missing)**

```bash
uv run pytest tests/test_analytics_virtual.py -v
```

- [ ] **Step 3: Implement `virtual.py`**

```python
"""Virtual analytics views — apply declared transform ops to row lists."""

from __future__ import annotations

from typing import Any

from palm.common.transforms.rules.count_by import CountByRule
from palm.core.transform.base import TransformContext


def apply_view_transform(
    rows: list[dict[str, Any]],
    transform: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not transform:
        return list(rows)
    op = str(transform.get("op") or "").strip()
    if op == "count_by":
        field = transform.get("field")
        if not field:
            raise ValueError("count_by requires field")
        ctx = TransformContext(original=list(rows))
        result = CountByRule.from_options(field=str(field)).apply(ctx)
        value = result.value
        if not isinstance(value, list):
            return []
        return [r for r in value if isinstance(r, dict)]
    raise ValueError(f"Unsupported analytics transform op: {op!r}")
```

- [ ] **Step 4: Run — expect PASS**

```bash
uv run pytest tests/test_analytics_virtual.py -q
```

- [ ] **Step 5: Commit**

```bash
git add src/palm/services/analytics/virtual.py tests/test_analytics_virtual.py
git commit -m "feat(analytics): 0.36.2 virtual view transform helper"
```

---

### Task 3: Query path for virtual views

**Files:**
- Modify: `src/palm/services/analytics/service.py`
- Modify: `tests/test_analytics_dogfood.py` (or new `tests/test_analytics_virtual_query.py`)

- [ ] **Step 1: Write failing integration test**

Use fakes from `tests/test_analytics_service.py` pattern:

```python
def test_query_virtual_view_loads_source_not_self() -> None:
    """View with source+transform must not invoke the view resource."""
    resources = {
        "palm-todos": {
            "name": "palm-todos",
            "provider": "kv",
            "action": "get",
            "metadata": {
                "analytics": {
                    "published": True,
                    "kind": "fact",
                    "row_path": "value",
                }
            },
        },
        "palm-todos-by-priority": {
            "name": "palm-todos-by-priority",
            "provider": "kv",
            "action": "get",
            "metadata": {
                "analytics": {
                    "published": True,
                    "kind": "view",
                    "source": "palm-todos",
                    "materialize": False,
                    "transform": {"op": "count_by", "field": "priority"},
                    "default_profile": "series",
                }
            },
        },
    }
    envelopes = {
        "palm-todos": {
            "success": True,
            "data": {
                "value": [
                    {"title": "a", "priority": "high"},
                    {"title": "b", "priority": "high"},
                ]
            },
            "error": None,
        },
        # If view resource is invoked, fail the test via missing envelope
    }
    svc = _svc(resources, envelopes)  # reuse helper from test_analytics_service
    out = svc.query("palm-todos-by-priority", profile="table")
    assert out["status"] == "ok"
    assert out["data"]["columns"] == ["priority", "count"]
    assert ["high", 2] in out["data"]["rows"] or out["data"]["rows"] == [["high", 2]]
    assert "palm-todos-by-priority" not in [
        c[0] for c in svc._providers.calls  # type: ignore[attr-defined]
    ]
```

Adapt fake providers to record `calls` (already does in `test_analytics_service.py`).

- [ ] **Step 2: Run — expect FAIL**

```bash
uv run pytest tests/test_analytics_virtual_query.py -v
```

- [ ] **Step 3: Wire `AnalyticsService.query`**

After `resolve_dataset` for the requested dataset:

```python
# Pseudocode inside query(), after resolve_dataset(detail, exposure):
if (
    exposure.source
    and not exposure.materialize
    and exposure.transform
):
    source_detail, source_exp = resolve_dataset(
        self._definitions,
        exposure.source,
        allow_unpublished=self._allow_unpublished,
    )
    source_name = str(source_detail.get("name") or exposure.source)
    envelope = self._providers.invoke(source_name, params=dict(params or {}), ...)
    # normalize envelope → rows using source_exp.row_path
    # rows = apply_view_transform(rows, exposure.transform)
    # then select/limit/present as today
    # lineage: kind=view, derived_from=[source], resource_ref=view name
```

If virtual path fails (source missing), return error envelope with code `dataset_not_found` or `virtual_source_failed`.

- [ ] **Step 4: Run all analytics unit tests**

```bash
uv run pytest tests/test_analytics_*.py -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/palm/services/analytics/service.py tests/test_analytics_virtual_query.py
git commit -m "feat(analytics): 0.36.2 query virtual views from source+transform"
```

---

### Task 4: Field roles + describe enrichment

**Files:**
- Create: `src/palm/services/analytics/schema_roles.py`
- Modify: `src/palm/services/analytics/service.py` (`describe`)
- Create: `tests/test_analytics_schema_roles.py`

- [ ] **Step 1: Failing tests**

```python
from palm.services.analytics.schema_roles import fields_from_schemas

def test_json_schema_properties_become_fields() -> None:
    fields = fields_from_schemas(
        output_schema={
            "type": "object",
            "properties": {
                "day": {"type": "string", "x-palm-role": "dimension"},
                "revenue": {"type": "number", "x-palm-role": "measure"},
            },
        },
        analytics_fields=None,
    )
    by_name = {f["name"]: f for f in fields}
    assert by_name["day"]["role"] == "dimension"
    assert by_name["revenue"]["role"] == "measure"


def test_analytics_fields_override() -> None:
    fields = fields_from_schemas(
        output_schema=None,
        analytics_fields=[{"name": "priority", "role": "dimension"}],
    )
    assert fields == [{"name": "priority", "role": "dimension", "type": None}]
```

- [ ] **Step 2: Implement `schema_roles.py`**

- Walk `output_schema.properties` if mapping
- Role from `x-palm-role` or property `role`; default `None`
- Type from `type` string
- If `analytics_fields` list present, use as authoritative (merge types from schema when possible)

- [ ] **Step 3: `describe()` includes `fields` list**

```python
"fields": fields_from_schemas(
    output_schema=detail.get("output_schema"),
    analytics_fields=list(exposure.fields) if exposure.fields else None,
)
```

- [ ] **Step 4: Tests pass + commit**

```bash
uv run pytest tests/test_analytics_schema_roles.py tests/test_analytics_service.py -q
git add src/palm/services/analytics/schema_roles.py src/palm/services/analytics/service.py tests/test_analytics_schema_roles.py
git commit -m "feat(analytics): 0.36.3 describe field roles from schema"
```

---

### Task 5: Doctor preflight for published datasets

**Files:**
- Locate doctor assembly: `src/palm/services/system/` (search `resource_preflight` / `doctor`)
- Modify doctor payload builder
- Create: `tests/test_analytics_doctor.py`

- [ ] **Step 1: Find existing doctor shape**

```bash
rg -n "resource_preflight|def doctor" src/palm/services/system src/palm/common -g'*.py' | head -30
```

- [ ] **Step 2: Write test asserting doctor includes analytics section**

```python
def test_doctor_lists_published_and_flags_missing_schema(host_with_published_resource):
    report = host.system.doctor()  # exact method name from Step 1
    analytics = report["resource_preflight"]["analytics"]  # or top-level analytics
    assert "published_count" in analytics
    assert isinstance(analytics.get("issues"), list)
```

Adjust keys to match existing doctor style once found.

- [ ] **Step 3: Implement checks**

For each resource with `parse_analytics_exposure(...).published`:

- Issue if `action` not in read allowlist  
- Issue if virtual view (`source` and not materialize) but source name empty  
- Issue if no `output_schema` and no `analytics.fields` (warning severity)

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(system): 0.36.4 doctor analytics published preflight"
```

---

### Task 6: Assist menu section `datasets`

**Files:**
- Modify: `src/palm/services/assist/catalog/menu.py`
- Modify: menu tests if present; else `tests/test_assist_menu_datasets.py`

- [ ] **Step 1: Failing test**

```python
def test_menu_datasets_section_lists_published(host):
    # register palm-todos style published resource
    turn = host.assist.catalog.menu(section="datasets")  # exact API: inspect menu.py
    # assert choices contain open: or dataset ids
    assert any("palm-todos" in str(c) for c in turn.get("choices", []))
```

- [ ] **Step 2: Implement section**

Reuse `AnalyticsService.list_datasets` if host has analytics; else definitions N+1 + `is_analytics_published`.  
Choice values: `open:dataset:palm-todos` or path alias to analytics describe—prefer documenting `params={dataset}` for assist later; for menu, value `dataset:palm-todos` and action open via assist grammar if easy; else chips with label only + alias `assist/menu` params.

Minimal viable: section lists items with `open` kind `dataset` and id name; Portal already uses `open:kind:id` for flows—add `dataset` kind that dispatches analytics describe/query summary.

If open-kind extension is large, **YAGNI for 0.36.6:** menu returns choices with `value` = dataset name and `actions` with label "Describe" alias params. Prefer matching existing `assist/open` pattern:

```python
# open.py — add kind dataset → analytics.describe
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(assist): 0.36.5 menu section datasets"
```

---

### Task 7: Todos pack — virtual priority view

**Files:**
- Modify: `examples/definitions/todos/resources.py`
- Modify: `examples/definitions/todos/builder.py` (optional: drop priority put if virtual)
- Modify: `examples/definitions/todos/analytics.py` (optional flow becomes “optional materialize” or simplified)
- Modify: `tests/test_analytics_dogfood.py`

- [ ] **Step 1: Change `palm-todos-by-priority` to virtual**

```python
PALM_TODOS_BY_PRIORITY = ResourceDefinition(
    ...
    # provider/action still required by ResourceDefinition — keep get + default []
    # but analytics:
    metadata={
        "analytics": {
            "published": True,
            "kind": "view",
            "source": "palm-todos",
            "materialize": False,
            "transform": {"op": "count_by", "field": "priority"},
            "default_profile": "series",
            "derived_from": ["palm-todos"],
        }
    },
)
```

Note: virtual query never invokes this resource; definition exists for catalog/describe.

- [ ] **Step 2: Simplify builder** — remove `rollup_priority` + `save_priority_view` steps if virtual covers series; keep only put fact. Update intro copy.

- [ ] **Step 3: Simplify or keep analytics flow** as optional “force rematerialize” for future; or delete materialize puts and leave flow as “inspect load only”. Prefer **delete priority put steps** from analytics flow; flow can remain load+summary for operator inspect, or remove pack module if redundant.

YAGNI: keep `todo-analytics` as load+summary only (no rebuild) for human inspection.

- [ ] **Step 4: Tests**

```python
def test_priority_view_is_virtual_no_second_put():
    # materialize only palm-todos
    # query palm-todos-by-priority → ok series/table without put-palm-todos-by-priority
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(todos): 0.36.6 virtual palm-todos-by-priority view"
```

---

### Task 8: Docs for 0.36 train complete

**Files:**
- Modify: `docs/VISION-0.36.md` (mark 0.36.x steps shipped when done)
- Modify: `STATUS.md`, `CHANGELOG.md`
- Modify: `docs/VISION-0.35.md` status note if needed

- [ ] **Step 1: Update STATUS ladder checkboxes for 0.36.1–0.36.6**
- [ ] **Step 2: CHANGELOG Unreleased bullets**
- [ ] **Step 3: Commit**

```bash
git commit -m "docs: mark 0.36 virtual analytics train shipped"
```

---

# Train B — 0.37 WorkIntent + triggers (foundation)

Start only after Train A green on `master`.

### Task 9: Pure WorkIntent in core

**Files:**
- Create: `src/palm/core/work/__init__.py`
- Create: `src/palm/core/work/intent.py`
- Create: `tests/test_work_intent.py`
- Modify: `scripts/guard_core.py` only if new package needs allowlisting (usually fine)

- [ ] **Step 1: Failing test**

```python
from palm.core.work import WorkIntent

def test_work_intent_roundtrip_dict():
    w = WorkIntent(
        id="w1",
        kind="run_flow",
        target="todo-analytics",
        payload={"reason": "test"},
        coalesce_key="todo-analytics:global",
        not_before=None,
        attempt=0,
        depth=0,
    )
    d = w.to_dict()
    w2 = WorkIntent.from_dict(d)
    assert w2.target == "todo-analytics"
    assert w2.coalesce_key == "todo-analytics:global"
```

- [ ] **Step 2: Implement frozen dataclass + to_dict/from_dict** (no I/O, no imports outside core)

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(core): 0.37.0 pure WorkIntent type"
```

---

### Task 10: Durable work store (outbox-adjacent)

**Files:**
- Create: `src/palm/common/work/store.py`
- Create: `src/palm/common/work/coalesce.py`
- Create: `tests/test_work_store.py`

- [ ] **Step 1: API design (implement exactly)**

```python
class WorkIntentStore:
    def enqueue(self, intent: WorkIntent) -> str: ...
    def claim_due(self, *, limit: int = 10, now: datetime | None = None) -> list[WorkIntent]: ...
    def ack(self, intent_id: str) -> None: ...
    def fail(self, intent_id: str, error: str) -> None: ...
```

Storage keys: `palm:work:entry:{id}`, `palm:work:pending_index` (mirror outbox patterns in `src/palm/common/events/outbox.py`).

Coalesce: if `coalesce_key` set, replace any pending entry with same key (delete old index entry).

- [ ] **Step 2: Tests with memory StorageEngine** (see outbox tests)

```bash
rg -n "OutboxStore" tests -g'*.py' | head -15
```

Copy fixture pattern.

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(work): 0.37.1 durable WorkIntentStore with coalesce"
```

---

### Task 11: Parse definition triggers

**Files:**
- Create: `src/palm/common/triggers/parse.py`
- Create: `src/palm/common/triggers/__init__.py`
- Create: `tests/test_triggers_parse.py`

- [ ] **Step 1: Support shapes**

```python
def parse_triggers(metadata: dict | None) -> list[TriggerSpec]:
    """
    triggers: [
      {kind: schedule, cron|interval, work: {flow_id, coalesce_key?}},
      {kind: on_flow, flow, when: succeeded, work: {...}},
      {kind: on_resource, resource, actions: [put], work: {...}, debounce?},
    ]
    Also map analytics.refresh.flow_id → schedule/on_resource stub if present.
    """
```

`TriggerSpec` frozen dataclass in same module.

- [ ] **Step 2: Tests for each kind + invalid ignored/strict**

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(triggers): 0.37.2 parse definition trigger metadata"
```

---

### Task 12: Trigger match → enqueue

**Files:**
- Create: `src/palm/common/triggers/registry.py`
- Create: `tests/test_triggers_registry.py`

- [ ] **Step 1: Registry loads triggers from DefinitionService list of flows (N+1 get full def or metadata)**

```python
class TriggerRegistry:
    def reload(self, definitions: DefinitionService) -> None: ...
    def on_event(self, event_type: str, payload: dict) -> list[WorkIntent]: ...
```

Matching rules:

- `on_resource`: `event_type == "resource.changed"` and payload.resource_ref in trigger.resource and action in actions  
- `on_flow`: `event_type == "flow.session.succeeded"` and payload.flow_id == trigger.flow  
- `schedule`: not via on_event (host tick separately)

- [ ] **Step 2: Unit tests with fake definitions returning metadata**

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(triggers): 0.37.2 registry event match to WorkIntent"
```

---

### Task 13: Emit `resource.changed` (mutating only)

**Files:**
- Prefer common wrapper used by ProviderExecutionService after invoke  
- Modify: `src/palm/services/execution/providers/service.py`  
- Or: `src/palm/common/resource/` helper called from enrich path  
- Create: `tests/test_resource_changed_event.py`

- [ ] **Step 1: After successful invoke, if action in {put, delete, write, …}:**

```python
event_engine.publish(Event(
    type="resource.changed",
    payload={
        "resource_ref": resource_ref,
        "action": action,
        "resource_id": result.metadata.get("resource_id"),
        "provider": result.metadata.get("provider"),
        # optional content_hash if cheap
    },
))
```

ProviderExecutionService may not have EventEngine today—inject optional `event_engine` or publish via host interceptor on a known bus.

**YAGNI path:** Host registers a wrapper around providers.invoke that publishes + enqueues. Avoid core ResourceEngine dependency on EventEngine if not already present.

Check:

```bash
rg -n "EventEngine|event_engine" src/palm/services/execution src/palm/core/resource -g'*.py' | head -20
```

- [ ] **Step 2: Test put publishes event (mock subscribe)**

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(resource): 0.37.3 emit resource.changed on mutating invoke"
```

---

### Task 14: Host work drain when able

**Files:**
- Create: `src/palm/app/host/work_drain_service.py`
- Modify: `src/palm/app/host/application_host.py` (start/stop wire)
- Create: `tests/test_work_drain_integration.py`

- [ ] **Step 1: Drainer loop (mirror OutboxBackgroundService)**

```python
class WorkDrainService:
    """Claim due WorkIntents and submit flows via ExecutionService when able."""

    def tick(self) -> int:
        if not self._able():
            return 0
        claimed = self._store.claim_due(limit=10)
        for intent in claimed:
            try:
                if intent.kind == "run_flow":
                    self._execution.flows.create(...)  # use real API from codebase
                self._store.ack(intent.id)
            except Exception as exc:
                self._store.fail(intent.id, str(exc))
        return len(claimed)
```

Discover real submit API:

```bash
rg -n "def create|def submit|def start_flow" src/palm/services/execution/flows/service.py | head -20
```

- [ ] **Step 2: Integration test**

Enqueue intent → tick → flow session exists or provider put from flow side-effect.

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(host): 0.37.4 WorkDrainService run-when-able"
```

---

### Task 15: Wire resource.changed → triggers → store

**Files:**
- Modify: host wiring after analytics/execution ready
- Modify: `tests/test_resource_changed_work.py`

- [ ] **Step 1: On `resource.changed`, `intents = registry.on_event(...); store.enqueue each`**

- [ ] **Step 2: Dogfood**

```python
# put palm-todos via providers
# assert pending work for todo-analytics or virtual no-op
# if virtual-only views, trigger may no-op; use materialize flow target for test
```

Register a test flow metadata trigger on a tiny pipeline if todos analytics is virtual-only.

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(host): 0.37.5 resource.changed enqueues WorkIntents"
```

---

### Task 16: Schedule tick → enqueue

**Files:**
- Modify: host background tick or new `ScheduleTickService`
- Create: `tests/test_schedule_trigger_enqueue.py`

- [ ] **Step 1: Each tick, for triggers kind=schedule due, enqueue WorkIntent with coalesce_key**

Parse `cron` only if dependency exists; **YAGNI:** support `interval_seconds: int` first in parse.py.

- [ ] **Step 2: Test interval_seconds=0 or past not_before enqueues once (coalesce)**

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(host): 0.37.6 schedule triggers enqueue work intents"
```

---

### Task 17: Docs for 0.37 foundation

**Files:**
- `docs/VISION-0.36.md` — mark 0.37.x foundation steps
- `STATUS.md`, `CHANGELOG.md`
- Optional ADR: `docs/adr/013-work-intents-and-triggers.md` (recommended)

- [ ] **Step 1: Write ADR-013** summarizing WorkIntent vs EventEngine vs no fat WorkEngine  
- [ ] **Step 2: Update STATUS trains**  
- [ ] **Step 3: Commit**

```bash
git commit -m "docs: ADR-013 work intents; mark 0.37 foundation"
```

---

# Later trains (not detailed here)

| Train | Plan when starting |
|-------|-------------------|
| **0.38** | Journal offsets, named consumers, redrive — new plan file |
| **0.39** | DashboardDefinition — new plan file |

Do **not** implement 0.38–0.39 in the same agent session as 0.36 without a fresh plan.

---

## Self-review (writing-plans checklist)

| Spec area (VISION-0.36) | Tasks |
|-------------------------|-------|
| Virtual views | 1–3, 7 |
| Schema roles | 4 |
| Doctor | 5 |
| Assist datasets | 6 |
| WorkIntent pure | 9 |
| Durable queue + coalesce | 10 |
| Triggers parse/match | 11–12 |
| resource.changed | 13, 15 |
| Drain when able | 14 |
| Schedule | 16 |
| No fat WorkEngine | 9–14 design |
| Journal 0.38 | deferred |
| Dashboard 0.39 | deferred |
| Definition-only examples | 7 |

**Placeholder scan:** none intentional.  
**Type names:** `WorkIntent`, `AnalyticsExposure.source/transform/materialize`, `apply_view_transform`, `TriggerRegistry`, `WorkIntentStore` — consistent across tasks.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-10-reactive-platform-0.36.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — this session, executing-plans with checkpoints  

**Which approach?**
