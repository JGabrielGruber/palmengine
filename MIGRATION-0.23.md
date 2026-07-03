# Migration guide — 0.23.0 (input_token strict mode)

**Release:** 0.23.0 · **Prior:** [MIGRATION-0.22.md](MIGRATION-0.22.md)

## Summary

0.23.0 adds optional CSRF-style `input_token` enforcement for MCP/REST wizard mutations. Default behavior is unchanged — strict mode is opt-in via environment variable.

## What changed

| Area | Change |
|------|--------|
| Inspect views | `mutation.input_token` issued when `mutations_allowed` |
| Instance metadata | `mutation_gate` stored on `ProcessInstance.metadata` |
| Writes | Optional `input_token` param on session input (REST body, MCP tools, `palm_assist` params) |
| Strict mode | `PALM_MCP_REQUIRE_INPUT_TOKEN=1` rejects writes without valid token |

## Agent / MCP operators

When strict mode is enabled:

1. Inspect before every write: `palm_flows_session` or `palm_assist` session read
2. Copy `mutation.input_token` from the response
3. Pass `input_token` with `value`/`input` on the next mutation
4. Re-inspect after each successful input (tokens are step-bound)

Example:

```python
inspect = palm_flows_session(session_id="inst-xxx", format="assistant")
token = inspect["mutation"]["input_token"]
palm_assist(params={"session_id": "inst-xxx", "value": "todo-builder", "input_token": token})
```

## Environment variables

```bash
PALM_MUTATION_SECRET=change-me-in-production   # required in production when strict mode on
PALM_MCP_REQUIRE_INPUT_TOKEN=0                  # set to 1 for agent hardening
```

## Docker

Add to `.env` or `docker-compose.yml` environment block. See [docs/DOCKER.md](docs/DOCKER.md).

## Breaking changes

None by default. Enabling `PALM_MCP_REQUIRE_INPUT_TOKEN=1` requires clients to pass `input_token` — update agent loops per `docs/mcp.txt` §12.

## 0.23.1 — inspect-only catalog

Operator-entry **`inspect-only`** now routes to a **catalog** step instead of summary/commit:

- Session stays `WAITING_FOR_INPUT` until the user says `exit`
- `operator_mode: inspect` on instance metadata at catalog step
- Read alias: `palm_assist(alias="operator-entry/inspect")` — no session required
- Menu number `3` coerces to `inspect-only` on choice steps (MCP assist path)

Agents that mapped user "inspect" to menu item 3 no longer reach an accidental summary confirm.