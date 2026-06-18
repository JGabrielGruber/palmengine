# Vision 0.13 — Wizard Experience

**Theme:** Make interactive wizards feel first-class — in the CLI, over REST, and in Palm Explorer.

**Status:** Shipped in **0.13.0** (June 2026)

---

## Problem

Through 0.12, Palm had mature wizard *execution* (collection steps, backtrack, commit) but operators still bounced between:

- Ephemeral `job_id` for REST input
- Raw JSON job context for prompts
- No browser-native multi-item editor for collection steps

Developers building human-in-the-loop workflows needed a **stable instance-centric API** and a **polished operator surface**.

---

## Goals

| Goal | Outcome |
|------|---------|
| Instance-keyed wizard API | `/v1/wizards/{instance_id}` with rich `prompt` + `answers` |
| Explorer wizard workspace | HTMX workspace on instance detail — progress, timeline, backtrack |
| Collection mastery | Overview card, add/edit/remove, field draft, remove confirm |
| Phase clarity | Wizard BT phases modularized under `phases/` with registry |
| Documentation | EXPLORER-WIZARD guide, ARCHITECTURE section, OpenAPI examples |

---

## What shipped

### REST (`/v1/wizards`)

- Submit, get status, provide input, backtrack
- `build_wizard_view()` read model from projections + live job inspection
- CQRS commands/queries wired in server and ApplicationHost

### Explorer

- `wizard_workspace` composable (full page + HTMX partial)
- Collection UI: `collection_overview_card`, `collection_item_card`, phase-specific forms
- `collection_input.py` action resolution + compound edit/remove chaining

### Wizard engine

- Phase registry (`step_kind` → factory)
- Collection subtree: `menu` → `select_item` → `field` → `remove_confirm`
- `WizardPattern` slimmed to root tick + context binding

### Quality

- SSR + REST test coverage for wizard and collection flows
- Accessibility: ARIA regions, live regions, focus-visible, responsive collection grid
- Version 0.13.0 release docs and checklist

---

## Non-goals (deferred)

- WebSocket live prompt streaming
- Explorer authentication / multi-tenant views
- Inline schema editor for flow definitions

---

## Success criteria (met)

1. Operator can run `todo-builder` entirely from Explorer with collection add/edit/remove.
2. Integrator can drive the same flow via `/v1/wizards` without Explorer.
3. `just check` and full test suite green at 0.13.0.
4. README and website reflect wizard Explorer as a headline feature.

---

## Next (0.14+)

- WebSocket surface for job/wizard events
- Explorer flow definition preview + dry-run
- Deeper collection validation feedback in Explorer (inline field errors)