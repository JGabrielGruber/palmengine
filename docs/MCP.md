# Palm MCP — Operator Adapter

**Status:** Phase 1–4 shipped · stdio transport via [FastMCP](https://pypi.org/project/fastmcp/)

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

## Phase 2b — Shipped (definition catalogs)

### REST enhancements

| Method | Path | Notes |
|--------|------|-------|
| `GET` | `/v1/resources` | Resource catalog (paginated) |
| `GET` | `/v1/resources/{ref}` | Describe by name or id |
| `GET` | `/v1/flows/{id}?verbose=0` | Slim summary with `step_slugs` (default `verbose=1` = full) |
| `GET` | `/v1/flows` | List includes `step_slugs` for wizard flows |

### MCP resources

| URI | REST |
|-----|------|
| `palm://definitions/flows` | `GET /v1/flows` |
| `palm://definitions/flows/{id}` | `GET /v1/flows/{id}?verbose=0` |
| `palm://definitions/processes` | `GET /v1/processes` |
| `palm://definitions/processes/{id}` | `GET /v1/processes/{id}` |
| `palm://definitions/resources` | `GET /v1/resources` |
| `palm://definitions/resources/{ref}` | `GET /v1/resources/{ref}` |
| `palm://openapi` | `GET /v1/openapi.json` |

## Phase 3 — Shipped (pattern contributors + prompts)

### Registry

Patterns register MCP tools via `register_mcp_contributor()` in `palm/patterns/_registry.py` (same model as CQRS contributors). The stdio server autoloads `INSTALLED_PATTERNS` and applies contributors at startup.

### Pattern-specific tools

| Pattern | Tool | Purpose |
|---------|------|---------|
| **wizard** | `palm_wizard_collection_action` | `add` / `edit` / `remove` / `done` / `cancel` / `confirm_remove` with optional `item_index` |
| **wizard** | `palm_wizard_commit_preview` | Answers + `commit_hook` payload before confirm |
| **parallel** | `palm_parallel_branch_status` | Branch slugs, active branch, merge preview |
| **pipeline** | `palm_pipeline_step_trace` | Transform chain from flow definition |

### MCP prompts

| Prompt | Use |
|--------|-----|
| `debug-wizard-block` | Find validation, child-wait, or collection blockers |
| `drive-wizard-to-step` | Advance instance toward a target step |
| `explain-compositional-stack` | Summarize invoke tree and next action |
| `operator-handoff` | Human-readable summary with Explorer links |

### Shared helpers (extended)

- `resolve_wizard_collection_action()` — maps collection UI actions to wizard input values
- `wizard_commit_preview()` — commit handler preview from wizard read model

## Phase 4 — Shipped (debug + lifecycle)

### REST endpoints (added for MCP)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/v1/jobs/{job_id}/cancel` | Cancel non-terminal jobs |
| `POST` | `/v1/flows/validate` | Dry-run flow build without submit |
| `GET` | `/v1/doctor` | JSON engine health (registries, storage, jobs) |

### Tier 3 + lifecycle MCP tools

| Tool | REST / source |
|------|---------------|
| `palm_cancel_job` | `POST /v1/jobs/{id}/cancel` |
| `palm_submit_process` | `POST /v1/plans/prepare` + `POST /v1/plans/submit` |
| `palm_trace_events` | `GET /v1/jobs/{id}/context` → `recent_events` |
| `palm_diff_snapshots` | `GET /v1/instances/{id}/snapshots/{a\|b}` |
| `palm_explain_step` | `GET /v1/flows/{id}?verbose=1` |
| `palm_validate_flow` | `POST /v1/flows/validate` |
| `palm_doctor` | `GET /v1/doctor` |
| `palm_fetch_job` | `POST /v1/resources/invoke` (palm `fetch`) |

### Shared helpers (extended)

- `diff_snapshot_states()` — blackboard key diff between snapshots
- `explain_flow_step()` — step metadata from flow definition
- `build_doctor_report()` — JSON doctor for REST/MCP

## Phase 5 — Shipped (native HTTP + resource invoke)

### Native HTTP transport

When the `mcp` extra is installed, `palm server` exposes **streamable HTTP** MCP at `POST /mcp` (same tool surface as stdio, loopback REST). Discovery reports `status: active` and `endpoint: /mcp`.

| Transport | Entry |
|-----------|-------|
| stdio | `palm-mcp` (proxies to `PALM_BASE_URL`) |
| streamable-http | `POST /mcp` on the running server (`Accept: application/json, text/event-stream`) |

### New MCP tools

| Tool | Purpose |
|------|---------|
| `palm_invoke_resource` | `POST /v1/resources/invoke` — any resource ref, action, params, state |
| `palm_compose_status` | Compositional session summary (invoke tree + compact wizard inspect) |

### App-level contributor registry

Applications register optional MCP tools via `register_app_mcp_contributor()` in `palm/app/mcp_registry.py` (same model as pattern contributors). Downstream apps (e.g. KnowKey) can expose `knowkey_compose_status` without modifying core Palm.

## Phase 6+ — Deferred (YAGNI)

- Split `server.py` into `tools.py` / `resources.py` as inventory grows
- Dedicated SSE-only transport tuning on `McpSurface`
- Version bump / CHANGELOG entry for 0.14.0 release train

## Package layout

```
src/palm/runtimes/mcp/     # FastMCP stdio adapter (thin)
src/palm/common/operator/  # compact inspect, invoke tree
src/palm/runtimes/server/surfaces/mcp/  # discovery stub
```

Install: `pip install "palmengine[mcp]"` · CLI: `palm-mcp`