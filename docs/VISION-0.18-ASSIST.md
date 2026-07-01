# Vision 0.18–0.19 — Assist: The Operator Soul

**Theme:** A fifth service domain for conversational, wizard-driven guidance — “what should I do next with Palm?” — without replacing business execution.

**Status:** 0.18.0 shipped (July 2026) · 0.19 MCP proxy planned  
**Builds on:** [0.16.5 shipped](VISION-0.16.md) · [0.17 service completion](superpowers/specs/2026-07-01-0.17-service-completion-design.md) prerequisite  
**MVP target:** 0.18.0 · **Stable agent proxy:** 0.19.0

---

## Problem

0.16 made `palm/services/` the product API. Agents and humans still face a **tool-surface explosion**:

| Symptom | Cause |
|---------|-------|
| MCP config churn on Palm upgrades | Per-domain tools (`palm_flows_*`, `palm_system_*`, …) rename and multiply |
| No single “start here” entry | Agents must know flow ids, process rules, and tier tables before acting |
| Meta-orchestration scattered | Doctor, catalog reads, compose navigation, and handoff live in docs and prompts — not a durable session |
| Compositional work split across layers | Resource invoke (`providers`) and wizard REPL (`flows`) are correct domains but awkward for “guide me through Palm” |

Business services answer **what to run**. Nothing answers **how to operate Palm** as a first-class, extensible domain.

---

## Goal

| Shift | From | To |
|-------|------|-----|
| Agent entry | Read `docs/MCP.md` + pick a flow tool | **`palm-operator-entry`** assist scenario + optional stable `palm_assist` (0.19) |
| Meta reads | Scatter across system/definitions tools | **`assist`** routes: catalog, doctor, hints, handoff |
| Compositional side effects | Ad-hoc resource steps in business flows | **Assist wizards** with `step_kind: resource` (same as compositional demo) |
| Extension | Docs-only operator recipes | **`register_assist_contributor()`** — apps/patterns add scenarios without core edits |

**Assist does not replace** `definitions`, `execution/flows`, `execution/providers`, `execution/processes`, or `system`. It **orchestrates and hands off** to them.

**No `palm/services/palm/`** — the palm provider stays in `palm/providers/palm/` and is invoked via resource steps and existing service domains.

---

## Architecture

```
Agent / CLI / Explorer / REST / MCP
        ↓
palm/runtimes/              thin mounts (assist REST + MCP)
        ↓
palm/services/assist/       USER API — conversational operator soul
  registry.py               routes, scenarios, handoff contracts
  service.py                dispatch, reads, handoff to execution/*
  session.py                thin shell over FlowSession (assist flows)
        ↓ (handoff)
palm/services/
  definitions/              catalog reads
  execution/flows/          business wizard REPL after handoff
  execution/providers/      resource steps inside assist wizards
  execution/processes/      process submit when scenario says so
  system/                   doctor, jobs, instances
        ↓
palm/common/ + palm/core/
```

### Routing vs ResourceLeaf (two lanes, one assist session)

| Lane | Owned by | Examples |
|------|----------|----------|
| **Assist routes** | `AssistService.dispatch()` | `assist/scenarios`, `assist/doctor`, `assist/handoff`, stable MCP path mapping |
| **Resource steps** | Wizard + `ResourceLeaf` inside assist **flows** | `submit_flow`, `invoke_resource`, nested composition (see `compositional_demo.py`) |

Assist **routes** are transport-shaped entry points. Assist **wizards** are normal `FlowDefinition`s in the catalog — conversational shell (input, collection, transform) plus resource steps for compositional work.

---

## What ships

### 0.18.0 — Assist MVP

1. `palm/services/assist/` — `AssistService`, `AssistSession`, `registry.py`
2. `host.assist` on `ApplicationHost` / `ServerContext`
3. REST `/v1/api/assist/…` — start scenario, session verbs, handoff
4. Catalog flow **`palm-operator-entry`** — defined REPL wizard (stable agent entry)
5. Compose/guide resource wiring in assist scenario definitions
6. Docs: `VISION-0.18-ASSIST.md`, design spec, plan, ADR 006
7. MCP **unchanged** — agents still use `palm_flows_*` until 0.19

### 0.19.0 — Stable agent proxy

1. **`palm_assist`** (or `palm_dispatch`) — single parametric MCP tool: `action` / `path` / `params`
2. **`register_assist_contributor()`** — downstream apps register scenarios and path aliases
3. **Handoff contract** — typed payload from assist session → `execution/flows` session (or process submit)
4. Operator wizards: compose status, guide, handoff prompts baked into catalog
5. `MIGRATION-0.19.md` — agent config stabilizes; Palm can add routes under the proxy

### 0.20+ (out of scope for these releases)

- Explorer assist workspace (SSR)
- WebSocket live assist stream (binds to `execution/flows` after 0.18 WebSocket, if shipped)
- Rich third-party assist contributors (KnowKey, custom apps)

---

## Agent loop (target 0.19)

```
palm_assist(action="start", scenario="operator-entry")
  → assist session (wizard shell)
  → input loop (plain strings, collection phases)
  → resource steps invoke palm provider / REST resources internally
  → handoff { flow_id, session_id?, hints } → business flows session
  → continue via palm_assist(path=["flows", …]) OR palm_flows_* (both valid)
```

0.18 reaches the same loop via REST + `palm_flows_create_session` on the handoff target; 0.19 collapses transport behind one stable tool name.

---

## Explicitly not Assist

| Item | Where it belongs |
|------|------------------|
| Flow instance REPL | `execution/flows` |
| Provider invoke HTTP | `execution/providers` |
| Process plan submit | `execution/processes` |
| Job board / snapshots | `system` |
| Palm remote HTTP client | `providers/palm/flow/remote/` |
| Generic OpenAPI-only proxy | 0.17.3 registry work |

---

## References

- Design: [docs/superpowers/specs/2026-07-01-assist-domain-design.md](superpowers/specs/2026-07-01-assist-domain-design.md)
- Plan: [docs/superpowers/plans/2026-07-01-assist-domain.md](superpowers/plans/2026-07-01-assist-domain.md)
- ADR: [docs/adr/006-assist-domain.md](adr/006-assist-domain.md)
- Prerequisite: [0.17 service completion](superpowers/plans/2026-07-01-0.17-service-completion.md)
- Compositional pattern: `examples/definitions/compositional_demo.py`
- Operator conventions: [docs/MCP.md](MCP.md)