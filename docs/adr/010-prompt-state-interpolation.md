# ADR-010: Wizard Prompt State Interpolation (0.27)

## Status

**Accepted** — July 2026 (Palm 0.27.1 shipped)

## Context

Palm binds `{{ state.key }}` placeholders in **resource definition params** and resource IDs ([VISION-0.12](VISION-0.12.md), `ResourceEngine.invoke()`). Wizard step `prompt` and `title` strings are **static** at runtime — computed answers and transform outputs (e.g. `mood_line`, `greeting_line`) do not appear in operator-facing copy unless authors add extra transform-only “display” steps.

Dogfooding the **`coconut-npc`** reference flow (branching wizard built via MCP design tools) showed that hub-menu prompts should reflect prior choices without workarounds. The same gap affects approval wizards, personalized summaries, and assist-presented questions — not game NPCs specifically.

## Decision

1. **Extend state binding to wizard copy** — Resolve `{{ state.path }}` in `prompt` and `title` when publishing the active step prompt (wizard phase `publish_prompt` path), using the same binding rules as resource params (`bind_resource_value` / shared helper in `palm/common/`).

2. **Scope: wizard input and summary phases first** — Resource and transform steps keep their existing feedback strings. Collection field prompts may follow in 0.27.2 if needed.

3. **Binding context** — Promote wizard answers to the blackboard before interpolation (same as `promote_binding_keys()` for resource steps). Read-only: interpolation must not mutate state.

4. **Failure mode** — Unresolved placeholders render as empty string or literal placeholder with a single `wizard.prompt_unresolved` diagnostic in powertool inspect (configurable; default empty for human-first copy).

5. **Design proposals** — No new proposal kind required; flow bodies may include placeholders in step prompts. Design contributors validate slug references only when `validate_placeholders: true` is opt-in (0.27.2+).

6. **Core purity** — Binding helper may live in `palm/common/`; wizard phases call it. No new imports in `palm/core/` from services.

## Alternatives considered

| Alternative | Why not chosen |
|-------------|----------------|
| Transform-only display steps | Extra steps, weak-LLM friction, duplicates state already on blackboard |
| Jinja2/full templating | Heavier dependency and attack surface; `{{ state.key }}` parity with resources is enough |
| Interpolate only in assist enrichers | Explorer and CLI would diverge; interpolation belongs in wizard read path |
| Interpolate at definition commit time | Stale copy when instance state diverges from catalog defaults |

## Consequences

- Coconut hub prompt can reference `{{ state.mood_line }}` without revving transform chains.
- Agents and integrators use one binding convention for resources **and** human copy.
- Tests: unit tests for binding + wizard tick integration; `coconut-npc` replay asserts resolved prompt substring.
- Documentation: VISION-0.27, `examples/README.md`, `palm://agent/references/branching-flows` (0.27.4).

## References

- [VISION-0.27.md](../VISION-0.27.md)
- [VISION-0.12.md](../VISION-0.12.md) — resource param binding
- `examples/definitions/coconut/npc.py`