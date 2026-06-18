# Explorer Wizard Guide

**Palm Engine 0.13** — operating and integrating interactive wizards through Palm Explorer and the `/v1/wizards` REST API.

---

## Quick start

```bash
# Start the server (default port 8080)
python -c "from palm.runtimes.server import ServerRuntime, run_server; run_server(ServerRuntime())"

# Submit a wizard (returns instance_id)
curl -s -X POST http://localhost:8080/v1/wizards \
  -H 'Content-Type: application/json' \
  -d '{"flow_name": "todo-builder"}'

# Open the Explorer workspace
open http://localhost:8080/explorer/instances/<instance_id>
```

The instance detail page renders a **wizard workspace**: progress bar, current prompt, answers so far, step timeline, and backtrack controls. Input and backtrack use **HTMX** for smooth partial updates — no full page reload.

---

## Workspace layout

| Region | Purpose |
|--------|---------|
| Header | Flow name, status badge, step progress |
| Prompt card | Current step UI (text input, choices, or collection editor) |
| Sidebar | Answers captured so far + step timeline |
| Backtrack | Jump to prior completed steps |
| Links | REST API, snapshots, job context |

When the current step is `step_kind: collection`, the prompt card shows the **collection overview** instead of a generic text field.

---

## Collection steps in Explorer

Collection steps manage repeatable items (todos, line items, contacts) inside one wizard step.

### Menu phase (overview)

- Numbered **item cards** with label + field previews
- **Add New** — starts item field sequence
- **Edit** / **Remove** per item (compound HTMX actions)
- Progress: `X of Y minimum` respecting `min_items`
- **Continue to summary** when enough items exist

### Field phase (add / edit)

- Sequential prompts for each `item_fields` entry
- **Draft so far** panel shows in-progress item
- **Save field** advances to next field; last field returns to menu
- Choice fields render as button grid (no duplicate text input)

### Remove confirm

- Item preview card
- **Yes, remove** / **No, keep it**

### Explorer form protocol

Explorer posts to `POST /explorer/instances/{id}/input`:

| Field | Meaning |
|-------|---------|
| `collection_action=add` | Menu: add new item |
| `collection_action=edit` + `item_index=N` | Edit item N (0-based) |
| `collection_action=remove` + `item_index=N` | Remove item N |
| `collection_action=done` | Continue to summary |
| `collection_action=cancel` | Cancel select/field (where supported) |
| `collection_action=confirm_remove` + `value=yes\|no` | Confirm removal |
| `value=...` | Field-phase or standard prompt answer |

REST clients use the same wizard strings the CLI expects:

```bash
curl -s -X POST http://localhost:8080/v1/wizards/inst-abc/input \
  -H 'Content-Type: application/json' \
  -d '{"value": "Add a new item"}'
```

---

## REST API reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/wizards` | Submit wizard (`wizard`, `flow`, or `flow_name`) |
| `GET` | `/v1/wizards/{instance_id}` | Rich status + `prompt` + `answers` + `next_actions` |
| `POST` | `/v1/wizards/{instance_id}/input` | `{"value": ...}` |
| `POST` | `/v1/wizards/{instance_id}/backtrack` | `{"to_step": "slug"}` or `{}` for previous |

Interactive documentation: `GET /v1/docs` · OpenAPI: `GET /v1/openapi.json`

---

## Example flows

| Flow | Command | Highlights |
|------|---------|------------|
| `todo-builder` | `palm flow start todo-builder` | Collection step, schemas, commit hook |
| `onboard` | `palm flow start onboard` | Classic multi-step wizard |
| `schema-onboard` | `palm flow start schema-onboard` | Layered state schemas |

Register examples from `examples/definitions/` before submitting by `flow_name` on a fresh server.

---

## HTMX integration notes

- Target: `#wizard-workspace` · Swap: `outerHTML`
- Loading indicator: `#wizard-loading` (`aria-live="polite"`)
- Forms disable controls during request via `hx-disabled-elt`
- Send `HX-Request: true` header for partial responses (otherwise 302 redirect)

---

## Related documents

- [ARCHITECTURE.md](ARCHITECTURE.md) — Wizard REST + Explorer section
- [MIGRATION-WIZARD-PHASES.md](src/palm/patterns/wizard/MIGRATION-WIZARD-PHASES.md) — Phase BT refactor
- [docs/VISION-0.13.md](docs/VISION-0.13.md) — Release vision
- [CHANGELOG.md](CHANGELOG.md) — `[0.13.0]` release notes