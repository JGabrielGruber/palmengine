# ADR-006: Assist Service Domain (0.18–0.19)

## Status

**Accepted** — July 2026 (Palm 0.18.0 MVP shipped · 0.19.0 stable MCP planned)

## Context

ADR-005 (0.16) established four user-facing service domains in `palm/services/`:

- `definitions` — catalog
- `execution/flows`, `execution/providers`, `execution/processes` — run
- `system` — observe and lifecycle

Agents operating Palm via MCP must learn a **large tool surface** (`palm_flows_*`, `palm_system_*`, pattern tools, provider invoke) documented in `docs/MCP.md`. Meta-orchestration — “what should I do next?”, doctor triage, catalog discovery, compositional navigation, handoff into business flows — is not modeled as a service. It lives in prose, prompts, and ad-hoc flow choices.

0.17 completes deferred transport parity (system REST, processes, palm provider remote, OpenAPI). That work finishes the **business API** but does not address **operator ergonomics** or **stable agent configuration** across Palm releases.

Compositional side effects already work via wizard `step_kind: resource` and `ResourceLeaf` (`examples/definitions/compositional_demo.py`). What is missing is a **named domain** that owns operator scenarios, dispatch routes, handoff contracts, and (later) a single MCP proxy.

## Decision

1. **Add `palm/services/assist/`** as a fifth user-facing service domain — conversational, wizard-driven guidance that composes `definitions`, `execution/flows`, and `system`.

2. **Two execution lanes inside assist:**
   - **Assist routes** — `AssistService.dispatch()` path table (start scenario, session verbs, doctor/catalog shortcuts, handoff)
   - **Resource steps** — normal assist **flow definitions** using `step_kind: resource` → `ResourceLeaf` → provider execution (no assist-specific resource engine)

3. **Assist scenarios are catalog flows** — e.g. `palm-operator-entry` — registered via built-in defaults and `register_assist_contributor()` (thread-safe registry at bootstrap). Patterns and apps may contribute scenarios without editing core.

4. **Handoff contract** — Typed payload (`kind: flow | process | none`) returned by `AssistService.handoff()`; assist does not silently auto-start business sessions except via explicit resource steps.

5. **Host surface** — `ApplicationHost` / `ServerContext` expose `.assist` alongside `.definitions`, `.execution`, `.system`.

6. **REST** — `/v1/api/assist/…` mounted like other service domains.

7. **MCP phasing:**
   - **0.18.0** — Assist REST + catalog; existing `palm_flows_*` remain canonical for session driving
   - **0.19.0** — Single stable tool `palm_assist` with parametric `path` / `params`, delegating to assist and other service dispatch tables; `palm://assist/routes` resource

8. **Explicit exclusion** — No `palm/services/palm/`. The palm provider plugin continues to consume existing service domains for local and remote invocation.

## Alternatives considered

| Alternative | Why not chosen |
|-------------|----------------|
| Extend `system` with assist verbs | Blurs observe/debug with interactive meta-orchestration |
| Put scenarios only in MCP prompts | Not REST-testable, no durable sessions, no handoff contract |
| One MCP proxy in 0.18 without assist service | Proxy needs a dispatch owner; assist service is that owner |
| Merge assist into `execution/flows` | Pollutes business flow REPL; different mental model (“guide” vs “run job”) |
| Replace all domain MCP tools in 0.19 | Too disruptive; `palm_flows_*` remain valid; proxy is opt-in stable entry |

## Consequences

### Positive

- **Operator soul** — Human-first “what next?” is a first-class, documented domain
- **Extension without core edits** — `register_assist_contributor()` mirrors pattern MCP contributors
- **Stable agent configs (0.19)** — One MCP tool name; Palm evolves routes underneath
- **Clear handoff** — Explicit boundary between assist guidance and business execution
- Reuses wizard, ResourceLeaf, `FlowSession`, and operator compact views — minimal new machinery

### Negative / cost

- Fifth service domain to wire, test, and document
- Some overlap with `docs/MCP.md` tier tables until agents adopt `palm_assist`
- Contributors must avoid putting business logic in assist routes (handoff, not duplicate execution)

### Relationship to other ADRs

- **Builds on ADR-005** — Same registry-driven service mount model
- **Does not modify ADR-004** — Still composes CQRS via `BaseService`
- **Complements 0.17** — Requires service API completion before assist handoff to processes REST

## References

- [VISION-0.18-ASSIST.md](../VISION-0.18-ASSIST.md)
- [Assist design spec](../superpowers/specs/2026-07-01-assist-domain-design.md)
- [Assist implementation plan](../superpowers/plans/2026-07-01-assist-domain.md)
- [ADR-005](005-service-domain-api.md)
- [docs/MCP.md](../MCP.md)
- `examples/definitions/compositional_demo.py`