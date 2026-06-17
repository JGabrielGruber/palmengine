# ADR-001: Compositional Power — Resource System Evolution (0.12)

## Status

**Accepted** — June 2026 (Phases 1–4 implemented)

## Context

Palm's orchestration model is definition-driven: `FlowDefinition` and `ProcessDefinition` are declarative, persisted, and executed via Behavior Trees. External integration exists through `ResourceEngine` and `BaseProvider`, but resources are not first-class definitions. Invocation is fragmented (wizard `action` steps, `enrich_resource` transforms) without a universal BT leaf.

As Palm targets hierarchical workflows, agent delegation, and distributed handoffs, we need:

- Declarative, reusable resource contracts stored in the repository
- A richer provider model beyond `fetch(resource_id)`
- Native BT integration (`ResourceLeaf`)
- Recursion — Palm flows invoking other Palm flows (`palm` provider)

Core purity and registry-based extension must be preserved.

## Decision

Adopt **0.12 — Compositional Power** with the following architectural choices:

1. **`ResourceDefinition`** joins flows and processes in `palm/definitions/` and `DefinitionRepository`.
2. **`ResourceEngine`** evolves to resolve definitions, bind params from state, invoke provider actions, and emit observability events. Contract stays in `palm/core/resource/`.
3. **`BaseProvider`** gains `invoke(action, params)` and `describe()`; `fetch` becomes the default read action.
4. **`ResourceLeaf`** is added to core BT leaves; patterns materialize it via `step_kind: resource` and equivalent stage/node config.
5. **`palm` provider** is a new plugin at `palm/providers/palm/`, delegating to local `ApplicationHost` or remote `ServerRuntime` HTTP. Recursion guardrails are provider responsibility with engine-level correlation metadata.
6. **Integration** with transforms (`enrich_resource` + `resource_ref`), compensation (mutating invoke metadata), and CQRS projections (resource invocation timeline) ships in Phase 5 of the implementation plan.

Wizard `action` steps remain supported via compatibility mapping to resource invocation specs during a deprecation window.

### Implementation progress (June 2026)

| Phase | Status |
|-------|--------|
| 1 — `ResourceDefinition` + repository | **Shipped** |
| 2 — `ResourceEngine.invoke` + `BaseProvider` contract | **Shipped** |
| 3 — `ResourceLeaf` + wizard `step_kind: resource` | **Shipped** |
| 4 — `palm` provider | **Shipped** |
| 5 — Cross-cutting integration | Planned (partial: `enrich_resource` + `resource_ref`) |
| 6 — Release polish | Planned |

Phase 2 wires definition resolution via `palm/common/resource/resolver.py` injected at `BaseRuntime.start()` — core stays pure.

Phase 4 ships `PalmProvider` at `palm/providers/palm/` with:

- **Local mode** — `bind_palm_runtime()` at `BaseRuntime.start()`; invocations delegate to `submit_flow`, `submit_process`, `resource.invoke`, or `get_job`
- **Remote mode** — `remote_url` + optional `remote_token`; flow submit via `POST /v1/jobs`; process submit via `POST /v1/plans/prepare` + `submit`
- **Recursion** — `palm_invoke_frame()` in `recursion.py` enforces depth (default 8) and cycle detection; correlation metadata on child job `metadata`
- **Wait policy** — `wait` + `wait_timeout` params for inline completion vs fire-and-forget child job handles

## Consequences

### Positive

- Symmetric definition model (flow / process / resource)
- True compositional orchestration — sub-flows, federated Palm, agent tool patterns
- Unified BT execution model for human and automated steps
- Clear extension point for new providers without core edits

### Negative

- `BaseProvider` contract change touches all existing providers
- Remote `palm` provider introduces distributed failure modes (timeouts, partial child completion)
- Repository and Explorer surface area grows

### Risks

- Unbounded recursion without depth limits — mitigated by `palm` provider guardrails
- Schema drift between parent and child flow state — mitigated by explicit output binding keys and optional schemas on `ResourceDefinition`

## Alternatives Considered

- **Keep wizard-only action steps** — rejected; does not scale to DAG, pipeline, or agent use cases
- **Sub-flow as a new pattern** instead of provider — rejected; duplicates orchestration entry points; provider model reuses existing submit/resume infrastructure
- **Resource definitions as flow options only** — rejected; prevents reuse across flows and independent versioning

## Links

- [VISION-0.12.md](../VISION-0.12.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [SCOPE.md](../../SCOPE.md)