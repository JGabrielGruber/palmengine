# Assist Domain Design

**Status:** Approved (July 1, 2026)  
**Version target:** 0.18.0 (MVP) · 0.19.0 (stable MCP proxy)  
**Builds on:** [0.16.5 shipped](../../VISION-0.16.md) · [0.17 service completion](2026-07-01-0.17-service-completion-design.md)  
**Vision:** [docs/VISION-0.18-ASSIST.md](../../VISION-0.18-ASSIST.md)

---

## Problem

Integrators and coding agents must internalize a **tier table** of MCP tools, flow ids, process entry rules, and compositional navigation before they can operate Palm safely. That knowledge lives in `docs/MCP.md` and prompts — not in a durable, testable service domain.

0.16 correctly split **catalog**, **execution**, and **observe**. It did not add a layer for **meta-orchestration**: greeting, triage, doctor, catalog discovery, compose navigation, and handoff into business flows.

Meanwhile, MCP tool proliferation forces agent hosts to **restart or reconfigure** when Palm adds domain verbs — even when the underlying service dispatch model is already path-shaped (`FlowExecutionService.dispatch`).

---

## Goal

Introduce **`palm/services/assist/`** as the fifth user-facing service:

1. **Conversational operator shell** — wizard-driven assist flows (input, collection, transform)
2. **Declarative routes** — transport-agnostic command paths for reads, scenario start, handoff
3. **Composable side effects** — `step_kind: resource` inside assist wizards (Palm provider, REST, etc.)
4. **Extension registry** — `register_assist_contributor()` for scenarios without core edits
5. **Stable MCP surface (0.19)** — one `palm_assist` tool mapping to assist + delegated service paths

Assist **composes** existing services; it does not duplicate CQRS, job state, or resource engines.

---

## Principle

```
Agent / Human
    ↓
assist (meta: what next?, handoff, stable proxy)
    ↓
definitions | execution/* | system  (business + observe)
    ↓
patterns / providers / core
```

**Core purity unchanged.** Assist lives in `palm/services/` and imports from `palm/common/` and other service domains — never from `palm/core/` extensions.

**No `palm/services/palm/`.** Remote/local palm behavior remains the provider plugin consuming `definitions`, `execution/flows`, `execution/providers`, `execution/processes`, and `system`.

---

## Policy

| Rule | Assist |
|------|--------|
| Breaking changes | 0.18 adds surface; 0.19 may deprecate direct MCP tier-1 duplication in docs (not remove `palm_flows_*` immediately) |
| Session identity | Assist sessions use `session_id` (= durable `instance_id`) same as flows |
| Plain-string input | Assist session input follows flows coercion (`yes`, choice slugs) |
| Handoff | Explicit typed payload; no hidden magic routing to arbitrary flows |
| Job-level input | **Never** on assist — interactive input is session verbs only (same as 0.17 flows policy) |
| `palm/common/services/` | Still `BaseService` + `errors` only |

---

## Domain model

### AssistService

Thin `BaseService` subclass:

| Responsibility | Delegates to |
|----------------|--------------|
| List/describe assist scenarios | Contributor registry + definitions catalog |
| Start assist scenario | `execution/flows` — `run_wizard` on assist flow id |
| Session verbs (input, backtrack, resume, cancel) | `AssistSession` → underlying `FlowSession` |
| Read shortcuts (doctor, catalog slices) | `system`, `definitions` service methods |
| Handoff | Build handoff view + return target `flow_id` / optional existing `session_id` + operator hints |
| Dispatch | `parse_assist_command(path)` → route table (mirrors `FlowExecutionService.dispatch`) |

### AssistSession

Wrapper over `FlowSession` with assist-specific view enrichment:

- `operator_hint` from `palm/common/operator/compact.py`
- `compose_status` when assist flow includes resource steps (reuse `build_compose_status`)
- `handoff_ready` flag when scenario terminal step requests business flow start

### Assist scenarios

Two sources, merged at bootstrap:

1. **Built-in catalog flows** — e.g. `palm-operator-entry`, `palm-compose-guide` (wizard pattern)
2. **Contributors** — `AssistContributor(scenario_id=…, flow_id=…, routes=…, register=…)`

Scenarios are **flows** in the definition catalog. Assist service owns **how to enter and route** them, not the wizard phase implementation.

---

## Routing vs ResourceLeaf

### Assist routes (service dispatch)

Transport-agnostic command paths registered in `assist/registry.py`:

| Command id | Path pattern | Summary |
|------------|--------------|---------|
| `list_scenarios` | `assist`, `scenarios` | List registered assist scenarios |
| `describe_scenario` | `assist`, `scenarios`, `{scenario_id}` | Scenario metadata + entry flow |
| `start_scenario` | `assist`, `scenarios`, `{scenario_id}`, `start` | Create assist session |
| `session_context` | `assist`, `session`, `{session_id}` | Inspect assist session |
| `session_input` | `assist`, `session`, `{session_id}`, `input` | Plain-string input |
| `session_handoff` | `assist`, `session`, `{session_id}`, `handoff` | Emit handoff payload |
| `doctor` | `assist`, `doctor` | Shortcut → `system.doctor()` |
| `catalog_flows` | `assist`, `catalog`, `flows` | Shortcut → definitions list flows |

REST maps 1:1 under `/v1/api/assist/…` (same convention as flows).

### Resource steps (wizard / ResourceLeaf)

Inside assist **flow definitions**, compositional work uses existing wizard resource phases:

```python
{
    "slug": "run-child",
    "step_kind": "resource",
    "resource_ref": "submit-ingest-etl",  # palm provider submit_flow
    "output_key": "child_job",
}
```

Execution path: `ResourceLeaf` → `ProviderExecutionService` → palm provider local/remote. **No assist-specific resource engine.**

This matches `examples/definitions/compositional_demo.py` and `tests/test_nested_wizard_resource.py`.

---

## Handoff contract

When an assist scenario completes (or reaches a handoff step), `AssistService.handoff(session_id)` returns:

```json
{
  "handoff": {
    "kind": "flow",
    "flow_id": "todo-builder",
    "session_id": null,
    "create_params": {},
    "operator_hint": "Use palm_flows_create_session or palm_assist path flows/{id}/create"
  }
}
```

Kinds (0.18):

| `kind` | Action |
|--------|--------|
| `flow` | Caller starts or resumes `execution/flows` session |
| `process` | Caller uses `execution/processes` submit (when 0.17.1 shipped) |
| `none` | Terminal assist — no business handoff |

Assist **does not** auto-start business sessions unless the scenario explicitly includes a resource step that already submitted a child flow.

---

## Contributor registry

```python
@dataclass(frozen=True)
class AssistContributor:
    contributor_id: str
    scenario_id: str
    flow_id: str
    summary: str = ""
    register_routes: Callable[[list[CommandSpec]], None] | None = None
    register_mcp_paths: Callable[[dict[str, str]], None] | None = None
```

- `register_assist_contributor()` in `palm/services/assist/registry.py` (thread-safe `RLock`, bootstrap time)
- Pattern apps **may** register assist scenarios in `ready()` (optional, same model as MCP contributors)
- App-level: `register_app_assist_contributor()` in `palm/app/assist_registry.py` (mirror `mcp_registry.py`)

0.19: contributors may add **path aliases** for `palm_assist` without new MCP tool names.

---

## REST surface (0.18)

Prefix: `/v1/api/assist`

| Method | Path | Handler |
|--------|------|---------|
| `GET` | `/v1/api/assist/scenarios` | `list_scenarios` |
| `GET` | `/v1/api/assist/scenarios/{scenario_id}` | `describe_scenario` |
| `POST` | `/v1/api/assist/scenarios/{scenario_id}/start` | `start_scenario` |
| `GET` | `/v1/api/assist/session/{session_id}` | `session_context` |
| `POST` | `/v1/api/assist/session/{session_id}/input` | `session_input` |
| `POST` | `/v1/api/assist/session/{session_id}/handoff` | `handoff` |
| `GET` | `/v1/api/assist/doctor` | `doctor` |

Session resume/backtrack/cancel: reuse flows handlers via assist service delegation (same verbs as `/v1/api/flows/…/session/…`).

---

## MCP surface

### 0.18 — No new stable tool

Document assist REST and catalog flow `palm-operator-entry`. Agents continue `palm_flows_*` for session driving after handoff.

Optional: `palm_assist_start` **experimental** behind env `PALM_MCP_ASSIST=1` — not required for 0.18.0 ship.

### 0.19 — Stable proxy

Single tool:

```
palm_assist(
  action: "dispatch",           # default
  path: ["assist", "scenarios", "operator-entry", "start"],
  params: { "body": {} },
)
```

Implementation:

1. Resolve path against assist registry **or** delegate to known service prefixes (`flows`, `definitions`, `system`, `providers`, `processes`)
2. Return compact operator view (reuse `compact.py`)
3. Catalog of valid paths exposed as MCP resource `palm://assist/routes` (generated from registries)

**Problem solved:** Agent config keeps one tool id; Palm adds routes/scenarios without MCP server schema churn.

`palm_providers_invoke` remains the generic resource invoke tool — assist proxy is for **session + guide** workflows, not raw provider HTTP.

---

## Host wiring

```python
# ApplicationHost (0.18)
self._assist = AssistService(
    commands=...,
    queries=...,
    schemas=...,
    definitions=self._definitions,
    execution=self._execution,
    system=self._system,
)

# ServerContext exposes ctx.assist
```

Add `"assist"` to `INSTALLED_SERVICES` in `palm/services/_apps.py`.

---

## Catalog: `palm-operator-entry` (0.18)

Defined wizard flow (in `examples/definitions/` or bundled defaults):

| Step kind | Purpose |
|-----------|---------|
| `input` / `choice` | Greet, triage intent (run flow, inspect system, compose help) |
| `transform` | Shape hints from doctor/catalog reads |
| `resource` | Optional demo invoke or `submit_flow` child for training wheels |
| `summary` | Emit handoff recommendation |

Metadata:

```python
FlowDefinition(
    id="flow-palm-operator-entry",
    name="palm-operator-entry",
    pattern="wizard",
    options={
        "metadata": {
            "assist": {
                "scenario_id": "operator-entry",
                "handoff_flows": ["todo-builder", "compositional-parent"],
            }
        },
        ...
    },
)
```

---

## Phase breakdown

| Release | Theme | Key deliverables |
|---------|-------|------------------|
| **0.17.x** | Prerequisite | Service API complete — system REST, processes, palm provider remote, OpenAPI |
| **0.18.0** | Assist MVP | `palm/services/assist/`, REST, host, `palm-operator-entry`, docs, tests |
| **0.19.0** | Stable MCP | `palm_assist`, contributor path aliases, `palm://assist/routes`, migration guide |
| **0.20+** | Experience | Explorer assist UI, WebSocket, rich contributors |

**Note:** 0.18.0 WebSocket on `execution/flows` (mentioned in 0.17 plan) is independent — assist MVP does not require it.

---

## Testing strategy

| Area | Tests |
|------|-------|
| Registry | `test_assist_registry.py` — routes, contributor merge |
| Service dispatch | `test_assist_service.py` — start, input, handoff payload |
| REST | `test_assist_service_routes.py` — path parity with registry |
| Integration | Start `palm-operator-entry` → input steps → handoff contains `flow_id` |
| MCP (0.19) | `test_palm_assist_tool.py` — dispatch paths, delegation to flows |
| Guard | `just guard-common` — no assist-specific logic leaked into `palm/common/` beyond operator helpers |

---

## Documentation checklist

| Release | Files |
|---------|-------|
| 0.18.0 | `VISION-0.18-ASSIST.md`, `MIGRATION-0.18.md`, `CHANGELOG [0.18.0]`, `RELEASE-0.18.0.md`, `docs/MCP.md` assist section, `docs/llms.txt`, `AGENTS.md`, `STATUS.md` |
| 0.19.0 | `MIGRATION-0.19.md`, `CHANGELOG [0.19.0]`, `RELEASE-0.19.0.md`, update `palm://agent/guide` |

---

## Alternatives considered

| Alternative | Why not chosen |
|-------------|----------------|
| Fold assist into `system` | System is observe/debug; assist is interactive meta-orchestration |
| Fold assist into `execution/flows` | Pollutes business flow REPL with operator-only scenarios |
| Only MCP prompts (no service) | Not testable, not REST-addressable, no handoff contract |
| Replace all MCP tools with one proxy in 0.18 | Too big a bang; defer stable proxy to 0.19 after assist routes exist |
| `palm/services/palm/` | Duplicates provider plugin; violates 0.16/0.17 boundary |

---

## References

- [VISION-0.18-ASSIST.md](../../VISION-0.18-ASSIST.md)
- [0.17 service completion design](2026-07-01-0.17-service-completion-design.md)
- [ADR-005](../../adr/005-service-domain-api.md)
- [docs/MCP.md](../../MCP.md)
- `src/palm/services/execution/flows/service.py` — `dispatch` model to mirror
- `src/palm/common/operator/compose_status.py`
- `examples/definitions/compositional_demo.py`