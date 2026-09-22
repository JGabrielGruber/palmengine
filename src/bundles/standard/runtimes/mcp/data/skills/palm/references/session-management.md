# Session Management

## Vocabulary (0.58 — memorize)

| Term | Use for |
|------|---------|
| **`session_id`** | System outside subject (`sess-…` or service `sess-svc-…`). Bind / own / operate. |
| **`instance_id`** | Product continue handle for one flow run. Paths emit segment **`instance`**. |
| **BoundSurface** | Product bind snapshot: system `session_id` + continue `instance_id` + kind/origin. |
| **SessionService** | Surface door (`host.session` / kit `resolve_session_service`). Does not resume. |
| **Wait plane** | Only continue path (resume parked work). No private completer→parent hooks. |

**Law:** session ≠ instance ≠ job. One session may own many instances. Active = focus only (not a foreign pass). Dual-own is forbidden.

**Soft land:** MCP/REST may accept legacy param name `session_id` or path segment `session` for the **continue** handle when the value is not a system `sess-…` id. Prefer `instance_id` / segment `instance` on new calls.

**REST product paths (0.58.19+):**

- `/v1/api/assist/instance/{instance_id}/…`
- `/v1/api/flows/{flow_id}/instance/{instance_id}/…`

**System journey (unchanged):** `system/session/{session_id}/…` (view, focus, waiting, cancel).

## Golden rules

1. **Never assume state** — always re-read after advancing.
2. **Check `mutation` block** — if `mutations_allowed` is false, read-only tools only; at `confirm_step`, wait for explicit user yes/no.
3. Track **system** `session_id` (when bound), **continue** `instance_id`, `job_id`, and current `step`.
4. Use `format=assistant` when presenting state to the user.
5. Drive one instance at a time; when `waiting_on` is set, drive that target (parent unparks on completion).
6. **Plain strings only** — `input="yes"`, choice slugs, text. Never JSON answer blobs.

## After every input

```
palm_assist(params={instance_id, flow_id, value})
```

Or domain tools (continue handle):

```
palm_flows_session(instance_id, format="assistant")
```

Legacy tool param names may still say `session_id` for the continue handle — treat the **value** as `instance_id` unless it is `sess-…`.

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
| Inspect | `palm_flows_session` + continue id + `format="assistant"` |
| Send answer | `palm_flows_session_input` + continue id + `input="…"` |
| Unified drive | `palm_assist(params={instance_id, flow_id, value})` |
| Stack summary | `palm_flows_compose_status` + continue id |
| Stuck resource | `palm_flows_session_resume` or alias `flows/instance-resume` |
| Nested child | Drive child instance; parent auto-unparks |
| Only job_id known | `palm_system_inspect_job(job_id)` |
| Start custom flow | `palm_flows_create_session(flow_id="my-flow")` after design commit |
| Bound system view | `system/session/{session_id}/view` (operate under owner) |

Running a flow you just published? See **`palm://agent/references/design-flows`** §C.

## Anti-patterns

- Treating `session_id` and `instance_id` as the same forever.
- Multiple inputs without re-inspecting between them.
- Guessing collection phase or current step slug.
- Omitting the continue handle when advancing a flow.
- Calling `palm_processes_submit` on interactive entry flows.
- Auto-confirming summary (`input="yes"`) without explicit user approval.
- Sending JSON like `{"answer": "beta"}` instead of `input="beta"`.
- Inventing a second resume path outside the wait plane.
