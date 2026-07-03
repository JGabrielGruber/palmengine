# Session Management

## Golden rules

1. **Never assume state** — always re-read after advancing.
2. **Check `mutation` block** — if `mutations_allowed` is false, read-only tools only; at `confirm_step`, wait for explicit user yes/no.
3. Track `session_id`, `job_id`, and current `step`.
4. Use `format=assistant` when presenting state to the user.
5. Drive one session at a time; resume child wait only when `waiting_for_child` is true.

## After every input

```
palm_flows_session(session_id, format="assistant")
```

Or unified assist (0.21.10+):

```
palm_assist(params={session_id, flow_id, value})
```

## Common commands

| Situation | Tool |
|-----------|------|
| Inspect | `palm_flows_session` + `format=assistant` |
| Send answer | `palm_flows_session_input(session_id, input="…")` |
| Stack summary | `palm_flows_compose_status(session_id)` |
| Stuck resource | `palm_flows_session_resume(session_id)` |
| Child wait | `palm_flows_session_resume_child_wait(session_id)` |
| Only job_id known | `palm_system_inspect_job(job_id)` |

## Anti-patterns

- Multiple inputs without re-inspecting between them.
- Guessing collection phase or current step slug.
- Omitting `session_id` when continuing a flow.
- Calling `palm_processes_submit` on interactive entry flows.