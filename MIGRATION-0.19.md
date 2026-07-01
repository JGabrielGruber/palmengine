# Migration Guide — Palm 0.19

**Experimental policy:** 0.19 adds a stable MCP proxy; existing per-domain MCP tools remain available.

**Builds on:** [MIGRATION-0.18.md](MIGRATION-0.18.md)

---

## 0.19.0 — Stable `palm_assist` MCP proxy

Palm ships one parametric MCP tool — **`palm_assist`** — that dispatches service command paths without schema churn when Palm adds routes or assist scenarios.

### What is new

| Surface | Entry |
|---------|-------|
| MCP tool | `palm_assist(path=…, params=…)` or `palm_assist(alias=…)` |
| MCP resource | `palm://assist/routes` — command-path catalog + contributor aliases |
| Contributor aliases | `operator-entry/start`, `operator-entry/handoff` (requires `session_id` param) |

### Agent config (recommended for new setups)

Configure **one** write tool instead of the full per-domain tier table:

```json
{
  "mcpServers": {
    "palm": {
      "command": "uv",
      "args": ["run", "--extra", "mcp", "palm-mcp"],
      "env": { "PALM_MCP_IN_PROCESS": "1" }
    }
  }
}
```

Operator loop with `palm_assist` only:

```
palm_assist(alias="operator-entry/start")
  → input loop via palm_assist(path=["assist","session",id,"input"], params={"value":"…"})
  → palm_assist(alias="operator-entry/handoff", params={"session_id": id})
  → palm_assist(path=["flows","todo-builder","create"])
  → palm_assist(path=["flows","todo-builder","session",id,"input"], params={"value":"…"})
```

Read catalogs via MCP resources (`palm://assist/routes`, `palm://definitions/flows`) — unchanged.

### Migration from `palm_flows_*` (optional, not required)

| Old tool | `palm_assist` equivalent |
|----------|--------------------------|
| `palm_flows_create_session(flow_id="onboard")` | `palm_assist(path=["flows","onboard","create"])` |
| `palm_flows_session(session_id)` | `palm_assist(path=["flows",flow_id,"session",session_id])` |
| `palm_flows_session_input(…)` | `palm_assist(path=[…,"input"], params={"value": "yes"})` |
| `palm_system_doctor()` | `palm_assist(path=["assist","doctor"])` or `["system","doctor"]` |

**No forced removal** — `palm_flows_*`, `palm_system_*`, `palm_definitions_*`, and `palm_providers_invoke` continue to work in 0.19.

### Contributor aliases

Apps and built-in scenarios may register stable aliases:

```python
AssistContributor(
    scenario_id="operator-entry",
    flow_id="flow-palm-operator-entry",
    mcp_aliases=(
        ("operator-entry/start", ("assist", "scenarios", "operator-entry", "start")),
        ("operator-entry/handoff", ("assist", "session", "{session_id}", "handoff")),
    ),
)
```

### Breaking changes

None. `palm_assist` is additive.

---

## References

- [docs/MCP.md](docs/MCP.md) — full tool inventory (per-domain + assist proxy)
- [docs/VISION-0.18-ASSIST.md](docs/VISION-0.18-ASSIST.md)
- [RELEASE-0.19.0.md](RELEASE-0.19.0.md)