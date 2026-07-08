# Session Management

## Golden rules

1. **Never assume state** — always re-read after advancing.
2. **Check `mutation` block** — if `mutations_allowed` is false, read-only tools only; at `confirm_step`, wait for explicit user yes/no.
3. Track `session_id`, `job_id`, and current `step`.
4. Use `format=assistant` when presenting state to the user.
5. Drive one session at a time; resume child wait only when `waiting_for_child` is true.
6. **Plain strings only** — `input="yes"`, choice slugs, text. Never JSON answer blobs.

## After every input

```
palm_flows_session(session_id, format="assistant")
```

Or unified assist (0.21.10+):

```
palm_assist(params={session_id, flow_id, value})
```

## Input by step type

| Step type | What to send |
|-----------|----------------|
| Text | `input="any plain string"` |
| Choice | `input="beta"` or `input="2"` (match assistant `choices`) |
| Summary / confirm | `input="yes"` or `input="no"` — only when user explicitly decides |
| Collection menu | `input="add"` then field values; or `collection_action` via assist |

When `PALM_MCP_REQUIRE_INPUT_TOKEN=1`, pass `mutation.input_token` from the last inspect on every write.

## Common commands

| Situation | Tool |
|-----------|------|
| Inspect | `palm_flows_session` + `format="assistant"` |
| Send answer | `palm_flows_session_input(session_id, input="…")` |
| Stack summary | `palm_flows_compose_status(session_id)` |
| Stuck resource | `palm_flows_session_resume(session_id)` |
| Child wait | `palm_flows_session_resume_child_wait(session_id)` |
| Only job_id known | `palm_system_inspect_job(job_id)` |
| Start custom flow | `palm_flows_create_session(flow_id="my-flow")` after design commit |

Running a flow you just published? See **`palm://agent/references/design-flows`** §C.

## Anti-patterns

- Multiple inputs without re-inspecting between them.
- Guessing collection phase or current step slug.
- Omitting `session_id` when continuing a flow.
- Calling `palm_processes_submit` on interactive entry flows.
- Auto-confirming summary (`input="yes"`) without explicit user approval.
- Sending JSON like `{"answer": "beta"}` instead of `input="beta"`.