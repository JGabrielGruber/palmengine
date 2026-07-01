# Migration Guide — Palm 0.18

**Experimental policy:** 0.18 adds a new service surface; existing MCP tools and business service routes are unchanged.

**Builds on:** [MIGRATION-0.17.md](MIGRATION-0.17.md)

---

## 0.18.0 — Assist domain MVP

Palm adds a fifth service domain: **`palm/services/assist/`** — conversational operator guidance with wizard scenarios, REST dispatch, and typed handoff to business flows.

### What is new

| Surface | Prefix / entry |
|---------|----------------|
| Assist REST | `/v1/api/assist/…` |
| Host API | `host.assist` on `ApplicationHost` / `ServerContext` |
| Catalog scenario | `palm-operator-entry` (`operator-entry`) |
| OpenAPI group | **Assist** on `/v1/docs` |

### Assist REST routes

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/v1/api/assist/scenarios` | List registered assist scenarios |
| `GET` | `/v1/api/assist/scenarios/{scenario_id}` | Describe scenario + catalog flow |
| `POST` | `/v1/api/assist/scenarios/{scenario_id}/start` | Start assist session |
| `GET` | `/v1/api/assist/session/{session_id}` | Inspect assist session |
| `POST` | `/v1/api/assist/session/{session_id}/input` | Plain-string interactive input |
| `POST` | `/v1/api/assist/session/{session_id}/backtrack` | Backtrack wizard step |
| `POST` | `/v1/api/assist/session/{session_id}/resume` | Resume waiting session |
| `POST` | `/v1/api/assist/session/{session_id}/cancel` | Cancel session job |
| `POST` | `/v1/api/assist/session/{session_id}/handoff` | Typed handoff payload |
| `GET` | `/v1/api/assist/doctor` | Engine health shortcut |

### Operator entry flow

Example definition: `examples/definitions/operator_entry.py`

```bash
# REST (after palm server)
curl -s -X POST http://127.0.0.1:8080/v1/api/assist/scenarios/operator-entry/start \
  -H 'Content-Type: application/json' -d '{}'
```

Drive the session with plain-string input (`todo-builder`, `yes`, etc.), then:

```bash
curl -s -X POST http://127.0.0.1:8080/v1/api/assist/session/{session_id}/handoff
```

Handoff response:

```json
{
  "handoff": {
    "kind": "flow",
    "flow_id": "todo-builder",
    "session_id": null,
    "create_params": {},
    "operator_hint": "Use palm_flows_create_session or POST /v1/api/flows/todo-builder/create"
  }
}
```

Start the business flow via existing flows API:

```bash
curl -s -X POST http://127.0.0.1:8080/v1/api/flows/todo-builder/create \
  -H 'Content-Type: application/json' -d '{}'
```

### MCP (unchanged in 0.18)

Agents continue using `palm_flows_*`, `palm_system_*`, and related per-domain MCP tools. Assist is REST-addressable in 0.18; stable `palm_assist` proxy ships in **0.19**.

### Extension

Register scenarios without core edits:

```python
from palm.services.assist.registry import AssistContributor, register_assist_contributor

register_assist_contributor(
    AssistContributor(
        contributor_id="my-app",
        scenario_id="my-scenario",
        flow_id="flow-my-assist-wizard",
        summary="Custom operator scenario",
    )
)
```

App-level mirror: `palm/app/assist_registry.py` (`register_app_assist_contributor`).

### Resource steps in assist wizards

Assist scenarios are normal wizard `FlowDefinition`s. Compositional side effects use existing `step_kind: resource` → `ResourceLeaf` (see `examples/definitions/compositional_demo.py`). No assist-specific resource engine.

### Breaking changes

None for 0.17 integrators. Assist is additive.

---

## References

- [docs/VISION-0.18-ASSIST.md](docs/VISION-0.18-ASSIST.md)
- [docs/superpowers/specs/2026-07-01-assist-domain-design.md](docs/superpowers/specs/2026-07-01-assist-domain-design.md)
- [docs/adr/006-assist-domain.md](docs/adr/006-assist-domain.md)
- [RELEASE-0.18.0.md](RELEASE-0.18.0.md)