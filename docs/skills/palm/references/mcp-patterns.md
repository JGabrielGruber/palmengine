# MCP Tool Description Patterns

When creating or updating Palm MCP tools in `src/palm/runtimes/mcp/` or pattern `bindings/mcp.py`, follow this structure.

## Required format

```markdown
To use this tool: call_connected_tool(tool_name="palm___<name>", arguments={...}).

[Clear purpose + when to use]

Examples::

    palm_assist()
    palm_assist(alias="operator-entry/start")
    palm_assist(params={"session_id": "inst-xxx", "value": "yes"})

[Optional: path vs alias vs params; use X instead of Y]
```

## Implementation

Use the shared helper:

```python
from palm.runtimes.mcp.descriptions import tool_description

_DESC = tool_description(
    "palm_flows_session",
    "Inspect a running flow session.",
    when="Use format=assistant for human-readable turns. Re-inspect after every input.",
    examples=[
        'palm_flows_session(session_id="inst-xxx", format="assistant")',
        'palm_flows_session(session_id="inst-xxx")  # powertool default',
    ],
    use_instead="Use palm_assist(params={session_id, flow_id, value}) to send input and inspect in one call.",
)

@mcp.tool(description=_DESC)
def palm_flows_session(...):
```

Design tools follow the same pattern — see `src/palm/runtimes/mcp/design/tools.py`:

```python
_PALM_DESIGN_PROPOSE_DESC = tool_description(
    "palm_design_propose_flow",
    "Create a design proposal from a wizard flow body.",
    when="Run propose → impact → commit. Load palm://agent/references/design-flows for agent playbook.",
    examples=['palm_design_propose_flow(body={"name": "foo-bar", "pattern": "wizard", "options": {...}})'],
    use_instead="Do not use palm_definitions_* create/update for agent catalog writes.",
)

@mcp.tool(description=_PALM_DESIGN_PROPOSE_DESC)
def palm_design_propose_flow(...):
    ...
```

FastMCP also accepts docstrings — assign `_DESC` as the function docstring before registration.

## Key rules

1. Always lead with `call_connected_tool` (Grok connected-tool hosts prefix `palm___`).
2. Include 3–4 realistic examples with real parameter shapes.
3. Document `path` vs `alias` vs `params` for `palm_assist`.
4. Note alternatives when similar tools exist (`palm_flows_session_input` vs `palm_assist`).
5. Keep descriptions self-contained — agents may not load `docs/MCP.md` first.

## Canonical agent guide

`docs/mcp.txt` → `palm://agent/guide`. Sync bundled copy: `src/palm/runtimes/mcp/data/mcp.txt`.