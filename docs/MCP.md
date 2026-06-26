# Palm MCP — Operator Adapter

**Status:** Phase 1 shipped · Phase 2a in progress · stdio transport via [FastMCP](https://pypi.org/project/fastmcp/)

Agents operate Palm through a thin **stdio MCP server** (`palm-mcp`) that proxies to the REST API. No in-process orchestration in the adapter — start `palm server` first.

## Quick start

```bash
uv sync --extra mcp
just palm-server              # terminal 1 — REST on :8080
just mcp-inspector            # terminal 2 — MCP Inspector UI
```

**Grok (project-scoped):** [`.grok/config.toml`](../.grok/config.toml) registers `palm` MCP server.

**Env vars:** `PALM_BASE_URL` (default `http://127.0.0.1:8080`), `PALM_SUBJECT` (`X-Palm-Subject`), `PALM_LLMS_TXT` (optional path to `docs/llms.txt`).

## Phase 1 — Shipped

### REST endpoints (added for MCP)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/v1/wizards/{id}/resume-child-wait` | Poll nested child, advance parent |
| `POST` | `/v1/wizards/{id}/resume-wizard-tick` | Re-drive waiting wizard / resource step |
| `GET` | `/v1/instances/{id}/tree` | Compositional invoke stack |

### MCP tools

| Tool | REST |
|------|------|
| `palm_list_waiting` | `GET /v1/jobs?status=WAITING_FOR_INPUT` |
| `palm_inspect_instance` | `GET /v1/wizards/{id}` → compact |
| `palm_wizard_input` | `POST /v1/wizards/{id}/input` |
| `palm_resume_child_wait` | `POST /v1/wizards/{id}/resume-child-wait` |

### MCP resources

| URI | Source |
|-----|--------|
| `palm://agent/guide` | `docs/llms.txt` |
| `palm://server/health` | `GET /health` |
| `palm://instances/{id}/tree` | `GET /v1/instances/{id}/tree` |

### Shared helpers (`palm/common/operator/`)

- `compact_wizard_inspect()` — agent-friendly wizard snapshot
- `compact_job_inspect()` — job context snapshot
- `build_invoke_tree()` — parent/child stack

### Discovery

`GET /v1/surfaces/mcp` → `status: stdio`, `command: palm-mcp`. Native HTTP `/mcp` transport is planned.

## Phase 2a — Shipped (operator loop completion)

| Tool | REST |
|------|------|
| `palm_resume_wizard_tick` | `POST /v1/wizards/{id}/resume-wizard-tick` |
| `palm_wizard_backtrack` | `POST /v1/wizards/{id}/backtrack` |
| `palm_inspect_job` | `GET /v1/jobs/{id}/context` → compact |
| `palm_provide_job_input` | `POST /v1/jobs/{id}/input` |
| `palm_submit_wizard` | `POST /v1/wizards` |
| `palm_submit_flow` | `POST /v1/jobs` |

## Phase 2b — Planned (definition catalogs)

- REST: `GET /v1/resources` catalog, slim `flow_summary` with step slugs
- Resources: `palm://definitions/flows`, `processes`, `resources`, `openapi`

## Phase 3+ — Deferred (YAGNI)

- `register_mcp_contributor()` (pattern-specific tools: collection, parallel)
- MCP prompts (`debug-wizard-block`, …)
- Tier 3 debug tools (`palm_diff_snapshots`, `palm_trace_events`, …)
- Native HTTP MCP on `McpSurface`
- `palm_cancel_job` (needs REST), `palm_submit_process` (plans API)

## Package layout

```
src/palm/runtimes/mcp/     # FastMCP stdio adapter (thin)
src/palm/common/operator/  # compact inspect, invoke tree
src/palm/runtimes/server/surfaces/mcp/  # discovery stub
```

Install: `pip install "palmengine[mcp]"` · CLI: `palm-mcp`