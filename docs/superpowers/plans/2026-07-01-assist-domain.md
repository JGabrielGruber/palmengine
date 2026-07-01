# Assist Domain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `palm/services/assist/` as the fifth service domain — conversational operator guidance with wizard scenarios, REST dispatch, handoff to business flows, and (0.19) a stable `palm_assist` MCP proxy.

**Architecture:** `AssistService` composes `definitions`, `execution/flows`, and `system`; assist wizards are normal catalog flows with optional `step_kind: resource` steps. Thin REST/MCP mounts. Contributor registry for extension.

**Tech Stack:** Python 3.11+, Palm `ApplicationHost`, `FlowExecutionService`, wizard pattern, `pytest`, `just docs-check` / `just guard-common`

**Design spec:** [docs/superpowers/specs/2026-07-01-assist-domain-design.md](../specs/2026-07-01-assist-domain-design.md)

**Vision:** [docs/VISION-0.18-ASSIST.md](../../VISION-0.18-ASSIST.md)

**Prerequisite:** [0.17 service completion](2026-07-01-0.17-service-completion.md) shipped (system REST, processes, palm provider remote, OpenAPI)

---

## File map

| Area | Create | Modify |
|------|--------|--------|
| Assist service | `services/assist/__init__.py`, `service.py`, `session.py`, `registry.py`, `grammar.py`, `schemas.py` | `services/_apps.py` |
| Host | — | `app/host/application_host.py`, server context wiring |
| REST | `runtimes/server/surfaces/rest/assist/routes.py`, `handlers.py` | `rest/service_routes.py`, `openapi_registry.py` (0.18) |
| Catalog | `examples/definitions/operator_entry.py` | definition bootstrap / defaults loader |
| App registry | `app/assist_registry.py` | — |
| MCP (0.19) | `runtimes/mcp/assist/tools.py`, `dispatch.py` | `runtimes/mcp/server.py`, `in_process.py` |
| Docs | `MIGRATION-0.18.md`, `RELEASE-0.18.0.md`, ADR 006 | `STATUS.md`, `MCP.md`, `AGENTS.md`, `docs/llms.txt`, `CHANGELOG.md` |
| Tests | `test_assist_registry.py`, `test_assist_service.py`, `test_assist_service_routes.py`, `test_operator_entry_flow.py` | `test_service_registries.py` |

---

## Phase 0.18.0 — Assist MVP

### Task 1: Assist registry + command grammar

**Files:**
- Create: `src/palm/services/assist/registry.py`
- Create: `src/palm/services/assist/grammar.py`
- Create: `tests/test_assist_registry.py`

- [ ] **Step 1: Write failing registry test**

```python
# tests/test_assist_registry.py
from palm.services.assist.registry import assist_commands, register_assist_contributor, AssistContributor

def test_assist_commands_include_start_and_handoff() -> None:
    ids = {spec.command_id for spec in assist_commands()}
    assert "start_scenario" in ids
    assert "session_handoff" in ids
    assert "list_scenarios" in ids

def test_assist_contributor_registers_scenario() -> None:
    register_assist_contributor(
        AssistContributor(
            contributor_id="test",
            scenario_id="demo",
            flow_id="flow-palm-operator-entry",
            summary="Demo",
        )
    )
    # assert list_scenarios includes demo (isolate registry in test via fixture cleanup)
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `uv run pytest tests/test_assist_registry.py -v`  
Expected: FAIL — module missing

- [ ] **Step 3: Implement `registry.py`**

- `CommandSpec` tuple (mirror `execution/flows/registry.py`)
- `AssistContributor` dataclass + `register_assist_contributor()` with `threading.RLock`
- `assist_commands()`, `list_scenario_rows()`, `scenario_by_id()`

- [ ] **Step 4: Implement `grammar.py`**

- `AssistCommandKind` enum
- `parse_assist_command(path: list[str])` — same path-token model as flows

- [ ] **Step 5: Run test — expect PASS**

Run: `uv run pytest tests/test_assist_registry.py -v`

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(0.18.0): assist command registry and grammar"
```

---

### Task 2: AssistService + AssistSession

**Files:**
- Create: `src/palm/services/assist/service.py`
- Create: `src/palm/services/assist/session.py`
- Create: `src/palm/services/assist/schemas.py`
- Create: `src/palm/services/assist/__init__.py`
- Create: `tests/test_assist_service.py`

- [ ] **Step 1: Write failing service test**

```python
# tests/test_assist_service.py
def test_start_operator_entry_returns_session(assist_host) -> None:
    result = assist_host.assist.dispatch(
        ["assist", "scenarios", "operator-entry", "start"],
        params={"body": {}},
    )
    assert "session_id" in result
    assert result.get("scenario_id") == "operator-entry"
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `uv run pytest tests/test_assist_service.py -v`

- [ ] **Step 3: Implement `AssistService`**

Constructor injects: `definitions`, `execution` (flows facet), `system`, CQRS buses.

Methods:
- `dispatch(path, params)` — route table
- `start_scenario(scenario_id, body)` → delegates `execution.flows.run_wizard(...)` with assist flow id from contributor/catalog
- `session(session_id)` → `AssistSession`
- `handoff(session_id)` → build typed payload from session view metadata
- Shortcuts: `doctor()`, `list_flows()` → delegate

- [ ] **Step 4: Implement `AssistSession`**

Thin wrapper: `input()`, `context()`, `backtrack()`, `resume()`, `cancel()` → underlying `FlowSession`

Enrich context with `operator_hint`, optional `compose_status` when resource steps present.

- [ ] **Step 5: Wire `INSTALLED_SERVICES`**

Modify: `src/palm/services/_apps.py` — add `"assist"`

- [ ] **Step 6: Run test — expect PASS**

Run: `uv run pytest tests/test_assist_service.py -v`

- [ ] **Step 7: Commit**

```bash
git commit -m "feat(0.18.0): AssistService and AssistSession"
```

---

### Task 3: Host + ServerContext

**Files:**
- Modify: `src/palm/app/host/application_host.py`
- Modify: server context factory (grep `ctx.system` / `ServerContext`)
- Modify: `tests/conftest.py` or host fixtures if needed

- [ ] **Step 1: Write failing host attribute test**

```python
def test_application_host_exposes_assist(host) -> None:
    assert host.assist is not None
    assert hasattr(host.assist, "dispatch")
```

- [ ] **Step 2: Wire `AssistService` in `_wire_cqrs` / service bootstrap**

After `self._execution` and `self._definitions` exist:

```python
from palm.services.assist import AssistService

self._assist = AssistService(
    **bus_kw,
    definitions=self._definitions,
    execution=self._execution,
    system=self._system,
)
```

Expose `host.assist` property.

- [ ] **Step 3: Run host tests**

Run: `uv run pytest tests/test_application_host.py tests/test_assist_service.py -v` (adjust to existing host test paths)

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(0.18.0): wire host.assist on ApplicationHost"
```

---

### Task 4: REST mount `/v1/api/assist`

**Files:**
- Create: `src/palm/runtimes/server/surfaces/rest/assist/routes.py`
- Create: `src/palm/runtimes/server/surfaces/rest/assist/handlers.py`
- Modify: `src/palm/runtimes/server/surfaces/rest/service_routes.py`
- Create: `tests/test_assist_service_routes.py`

- [ ] **Step 1: Write failing route test**

```python
from palm.runtimes.server.surfaces.rest.assist.routes import ROUTES

def test_assist_routes_include_start_and_handoff() -> None:
    paths = {(e.method, e.path) for e in ROUTES}
    assert ("POST", "/v1/api/assist/scenarios/{scenario_id}/start") in paths
    assert ("POST", "/v1/api/assist/session/{session_id}/handoff") in paths
```

- [ ] **Step 2: Implement routes + handlers**

Handlers delegate to `ctx.assist` — mirror flows handler style (JSON body → `dispatch` or direct service method).

- [ ] **Step 3: Mount in `service_routes.py`**

- [ ] **Step 4: Run REST tests**

Run: `uv run pytest tests/test_assist_service_routes.py tests/test_server_runtime.py -v -k assist`

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(0.18.0): REST /v1/api/assist routes"
```

---

### Task 5: Catalog flow `palm-operator-entry`

**Files:**
- Create: `examples/definitions/operator_entry.py`
- Modify: definition loading for tests / `palm doctor` examples
- Create: `tests/test_operator_entry_flow.py`

- [ ] **Step 1: Write failing integration test**

```python
def test_operator_entry_handoff_recommends_flow(assist_host) -> None:
    started = assist_host.assist.start_scenario("operator-entry", {})
    session_id = started["session_id"]
    # drive with fixture inputs or mock to terminal step
    handoff = assist_host.assist.handoff(session_id)
    assert handoff["handoff"]["kind"] in ("flow", "none")
```

- [ ] **Step 2: Define `flow-palm-operator-entry` wizard**

Steps: greet choice → optional doctor read (transform) → summary with `metadata.assist.handoff_flows`.

Register built-in scenario in assist registry at import time (bootstrap).

- [ ] **Step 3: Run integration test**

Run: `uv run pytest tests/test_operator_entry_flow.py -v`

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(0.18.0): palm-operator-entry assist scenario"
```

---

### Task 6: App assist contributor registry (optional 0.18)

**Files:**
- Create: `src/palm/app/assist_registry.py`
- Create: `tests/test_assist_app_registry.py`

- [ ] **Step 1: Mirror `mcp_registry.py` pattern**

`register_app_assist_contributor()`, `app_assist_contributors()`, thread-safe.

- [ ] **Step 2: Test register + list**

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(0.18.0): app-level assist contributor registry"
```

---

### Task 7: Docs + release 0.18.0

**Files:**
- Create: `MIGRATION-0.18.md`, `RELEASE-0.18.0.md`
- Modify: `STATUS.md`, `CHANGELOG.md`, `docs/MCP.md`, `docs/llms.txt`, `AGENTS.md`, `docs/index.html` (feature blurb)

- [ ] **Step 1: Document assist REST paths and `palm-operator-entry`**

- [ ] **Step 2: Bump version to 0.18.0**

Run: `just bump-version 0.18.0`

- [ ] **Step 3: Run verification**

```bash
uv run pytest tests/test_assist_registry.py tests/test_assist_service.py \
  tests/test_assist_service_routes.py tests/test_operator_entry_flow.py -v
just docs-check
just guard-common
```

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(0.18.0): assist domain MVP docs and version bump"
```

---

## Phase 0.19.0 — Stable MCP proxy

### Task 8: `palm_assist` dispatch tool

**Files:**
- Create: `src/palm/runtimes/mcp/assist/dispatch.py`
- Create: `src/palm/runtimes/mcp/assist/tools.py`
- Modify: `src/palm/runtimes/mcp/server.py`, `in_process.py`
- Create: `tests/test_palm_assist_tool.py`

- [ ] **Step 1: Write failing MCP tool test**

```python
async def test_palm_assist_starts_operator_entry(mcp_client) -> None:
    result = await mcp_client.call_tool(
        "palm_assist",
        {"path": ["assist", "scenarios", "operator-entry", "start"], "params": {}},
    )
    assert "session_id" in parse_result(result)
```

- [ ] **Step 2: Implement dispatch resolver**

1. If path starts with `assist` → `ctx.assist.dispatch`
2. If path starts with `flows|definitions|system|providers|processes` → delegate to matching service `dispatch` (where exists)
3. Return compact operator view

- [ ] **Step 3: Register single `palm_assist` tool on MCP server**

- [ ] **Step 4: Add MCP resource `palm://assist/routes`**

Generate from assist + service command registries.

- [ ] **Step 5: Run MCP tests**

Run: `uv run pytest tests/test_palm_assist_tool.py tests/test_mcp_in_process.py -v`

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(0.19.0): palm_assist stable MCP dispatch tool"
```

---

### Task 9: Contributor path aliases + handoff docs

**Files:**
- Modify: `src/palm/services/assist/registry.py`
- Modify: `docs/MCP.md`, create `MIGRATION-0.19.md`

- [ ] **Step 1: Support `register_mcp_paths` on `AssistContributor`**

Alias map: `"start": ("assist", "scenarios", "operator-entry", "start")`

- [ ] **Step 2: Document agent loop with `palm_assist` only**

Update `docs/llms.txt` and `palm://agent/guide` bundled copy.

- [ ] **Step 3: MIGRATION-0.19.md**

Explain: agents can keep `palm_flows_*` or migrate to `palm_assist`; no forced removal in 0.19.

- [ ] **Step 4: Bump version 0.19.0 + release checklist**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(0.19.0): assist MCP aliases and migration guide"
```

---

## Final verification (0.19.0)

```bash
uv run pytest tests/test_assist_registry.py tests/test_assist_service.py \
  tests/test_assist_service_routes.py tests/test_operator_entry_flow.py \
  tests/test_palm_assist_tool.py tests/test_mcp_in_process.py -v
just docs-check
just guard-common
rg 'palm/services/palm' src/   # expect no matches
```

---

## Plan self-review

| Spec section | Task |
|--------------|------|
| Assist service + session | 2 |
| Registry + contributors | 1, 6, 9 |
| REST `/v1/api/assist` | 4 |
| `palm-operator-entry` catalog | 5 |
| host.assist | 3 |
| Handoff contract | 2, 5 |
| Resource steps in wizards | 5 (uses existing ResourceLeaf) |
| Stable `palm_assist` MCP | 8, 9 |
| No `palm/services/palm/` | *(excluded by design)* |
| 0.17 prerequisite | blocked until 0.17 plan ships |

| Placeholder scan | Status |
|------------------|--------|
| TBD / TODO in steps | None |
| Unnamed files | All paths explicit |

---

## Documentation checklist

| Release | Files |
|---------|-------|
| 0.18.0 | `VISION-0.18-ASSIST.md`, ADR 006, `MIGRATION-0.18.md`, `RELEASE-0.18.0.md`, `STATUS.md`, `CHANGELOG [0.18.0]` |
| 0.19.0 | `MIGRATION-0.19.md`, `RELEASE-0.19.0.md`, `docs/MCP.md`, `CHANGELOG [0.19.0]` |