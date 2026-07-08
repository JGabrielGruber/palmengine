# Vision 0.27 — Compositional Design Parity

**Theme:** Complete agent-safe catalog evolution and consistent declarative schemas — flows, resources, and human-facing copy — building on 0.25 Design Service and 0.12 Compositional Power.

**Status:** Planned (post **0.26.0**)  
**Depends on:** [0.25 Design Service](VISION-0.25.md) ✅ · [0.26 CQRS parity](superpowers/plans/2026-07-08-cqrs-bus-parity-and-0.26.md) ✅  
**ADR:** [010-prompt-state-interpolation.md](adr/010-prompt-state-interpolation.md) · **Plan:** [compositional-design-parity-0.27.md](superpowers/plans/2026-07-08-compositional-design-parity-0.27.md)  
**Reference flow:** `examples/definitions/coconut_npc.py` (`coconut-npc`)

---

## Why 0.27

**0.26.0** hardened Design Service transport (CQRS bus parity, registry dispatch, MCP guides). Dogfooding via the **`coconut-npc`** reference flow (built through MCP `palm_design_*`) exposed gaps that matter for **general orchestration**, not game NPCs:

| Symptom | Root cause |
|---------|------------|
| Agents can't propose `ResourceDefinition`s | Design Service covers **flows only** |
| Transform steps fail design validation unless wrapped | Design contributor schema ≠ runtime builder schema |
| Computed state (`mood_line`) doesn't appear in prompts | `{{ state.* }}` binds resource params, not wizard copy |
| Resource wizards fail opaquely in dev/MCP | REST provider needs `base_url`; errors don't steer operators |
| Hub branching is powerful but under-documented | `route_on_answer` / `complete_on` lack a first-class playbook |

Palm's priority remains **human-first orchestration, agent operators, and compositional workflows** — not NPC engines. Coconut is a **stress-test profile** for branching wizards; the 0.27 work generalizes what that test proved useful.

---

## Goal

| Shift | From (0.26) | To (0.27) |
|-------|-------------|-----------|
| Design catalog scope | Flow proposals only | **Flows + resources** (+ processes when ready) |
| Declarative step shape | Design validator diverges from builder | **One canonical schema** per step kind |
| Wizard copy | Static `prompt` strings | **`{{ state.key }}` interpolation** in prompts/titles |
| Resource failures | Hard block, vague MCP errors | **Preflight + optional resilience** params |
| Branching patterns | Scattered examples | **Documented reference** (`coconut-npc`, agent skill) |

**Non-goals for 0.27:**

- Raw behavior-tree node API for external editors
- Random/bark pools or game-quest blackboards
- Ambient / simultaneous character simulation
- Deprecating `DefinitionService` direct CRUD (layered coexistence per ADR-008)

---

## What ships (target)

### 0.27.0 — Design schema parity

- Wizard design contributor accepts **flat transform steps** (same as `transform-example` and repo examples).
- Optional normalizer: nested `"transform": {...}` → flat fields in `prepare_flow_from_body`.
- Tests: design propose validates `coconut-npc` body without workaround wrappers.
- Docs: canonical transform JSON in `palm://agent/references/design-flows`.

### 0.27.1 — Prompt / state interpolation

- Interpolate `{{ state.key }}` in wizard `prompt` and `title` at tick/publish time (ADR-010).
- Shared binding helper with resource param resolution.
- Explorer + `format=assistant` show resolved copy.

### 0.27.2 — Design service: resources

- `propose_resource` / impact / commit (revision-aware where applicable).
- Provider/pattern design contributors for resource contracts.
- MCP `palm_design_propose_resource` (or unified `kind` parameter).
- Impact reports flows that reference changed `resource_ref` values.

### 0.27.3 — Resource operator ergonomics

- `palm_system_doctor` preflight: REST `base_url`, reachable providers.
- Resource step param `on_resource_failure`: `block` | `skip` | `branch` (default `block`).
- MCP invoke errors include remediation hints.

### 0.27.4 — Branching playbook

- `palm://agent/references/branching-flows` (hub menu, loop-back, `complete_on`).
- `coconut-npc` registered in examples + skill cross-links.
- Assist catalog entry optional (low priority vs docs).

---

## Reference: Coconut (`coconut-npc`)

Shipped example — **not** a product direction, but a durable regression profile:

```
player_name → build_greeting (string_format)
           → reputation (choice)
           → mood_line (lookup)
           → topic (hub) ──route_on_answer──┬→ rumors ──┐
                                            ├→ trade → trade_buy
                                            ├→ about
                                            └→ farewell (complete_on)
```

**Try:**

```bash
palm flow start coconut-npc
```

**MCP:**

```text
palm_design_propose_flow  # revise coconut-npc via base_flow_id
palm_flows_create_session(flow_id="coconut-npc")
```

---

## Architecture (unchanged layers)

```
Agent / MCP / CLI / Explorer
        ↓
palm/services/design/     propose_* → validate → impact → commit (extended kinds)
        ↓
palm/services/definitions/  catalog CRUD + revisioning (unchanged contract)
        ↓
palm/patterns/wizard/     step kinds → behavior tree (ResourceLeaf, TransformLeaf, phases)
        ↓
palm/core/                pure engines (no new imports from services)
```

Extension remains **registry-based** — design contributors per pattern/provider, not core edits.

---

## Success criteria

- [x] MCP agent proposes `coconut-npc` rev N+1 with flat transform steps — `valid: true` on first propose.
- [x] Prompt shows `mood_line` on hub step via `{{ state.mood_line }}` (0.27.1).
- [x] Agent proposes a `ResourceDefinition` via `palm_design_propose_resource`, commits, impact lists referencing flows.
- [x] `palm doctor` reports REST resource misconfiguration before a wizard session stalls.
- [ ] `just docs-check` + parity tests green; `coconut-npc` session replay test in CI.

---

## References

- Dogfood origin: MCP-only `coconut-npc` build (July 2026)
- Compositional Power: [VISION-0.12.md](VISION-0.12.md)
- Design Service: [VISION-0.25.md](VISION-0.25.md) · [ADR-008](adr/008-design-service.md)
- CQRS parity: [ADR-009](adr/009-service-cqrs-contributors.md)
- Examples: [examples/README.md](../examples/README.md) · `examples/definitions/coconut_npc.py`