"""
Coconut NPC — branching wizard reference flow (hub menu + transforms + routing).

Dogfood profile for **compositional interactive workflows**: not game-NPC product
work, but a vivid stress test of wizard behavior trees compiled from declarative
steps — ``route_on_answer``, ``complete_on``, transform chains, and durable session
state.

Patterns demonstrated:

- Hub-and-spoke topic menu with loop-back (``"more": "topic"``)
- ``string_format`` + ``lookup`` transform steps between inputs
- Reputation-style branching via choice + lookup table
- Clean exit via ``complete_on`` on a farewell step

Built originally via MCP ``palm_design_*`` (0.26 dogfood). Shipped here as a
canonical example for CLI, Explorer, and agent playbooks.

Try::

    palm flow start coconut-npc

MCP::

    palm_flows_create_session(flow_id="coconut-npc")
    palm_flows_session(session_id, flow_id="coconut-npc", format="assistant")
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition

COCONUT_NPC_FLOW = FlowDefinition(
    id="flow-coconut-npc",
    name="coconut-npc",
    pattern="wizard",
    options={
        "include_summary": False,
        "allow_backtrack": True,
        "metadata": {
            "example": True,
            "description": (
                "Branching wizard reference — hub menu, transforms, route_on_answer. "
                "See docs/VISION-0.27.md and examples/README.md."
            ),
            "tags": ["branching", "transform", "routing", "reference"],
        },
        "steps": [
            {
                "slug": "player_name",
                "title": "Approach",
                "prompt": (
                    "*(You approach Coconut's stall — coconuts, rumors, "
                    "and questionable advice.)*\n\n"
                    "What name do you give?"
                ),
                "validation": [{"rule": "min_length", "params": {"min": 1}}],
            },
            {
                "slug": "build_greeting",
                "step_kind": "transform",
                "title": "Coconut sizes you up",
                "source_key": "player_name",
                "target_key": "greeting_line",
                "rule": "string_format",
                "options": {
                    "template": "Ah, {value} — Coconut wipes her hands on her apron and studies you.",
                },
            },
            {
                "slug": "reputation",
                "title": "Coconut",
                "prompt": (
                    "*(Coconut considers your greeting.)*\n\n"
                    "\"So — friend, stranger, or trouble?\""
                ),
                "field_type": "choice",
                "choices": ["friend", "stranger", "trouble"],
            },
            {
                "slug": "mood_line",
                "step_kind": "transform",
                "title": "Coconut reacts",
                "source_key": "reputation",
                "target_key": "mood_line",
                "rule": "lookup",
                "options": {
                    "table": {
                        "friend": (
                            "\"Good. Friends get the sweet coconuts and the good rumors.\""
                        ),
                        "stranger": (
                            "\"Strangers pay full price and get the boring rumors.\""
                        ),
                        "trouble": (
                            "\"Trouble gets watched. And the coconuts with the soft spots.\""
                        ),
                    },
                    "default": "\"Hmph.\"",
                },
            },
            {
                "slug": "topic",
                "title": "Coconut",
                "prompt": (
                    "*(She leans on the cart.)*\n\n"
                    "\"Well then. What'll it be?\""
                ),
                "field_type": "choice",
                "choices": ["rumors", "trade", "about", "leave"],
                "params": {
                    "route_on_answer": {
                        "rumors": "rumors",
                        "trade": "trade",
                        "about": "about",
                        "leave": "farewell",
                    },
                },
            },
            {
                "slug": "rumors",
                "title": "Coconut — Rumors",
                "prompt": (
                    "\"The jarl's steward bought every rope in town — make of that what you will.\"\n\n"
                    "\"Old Mora says the well water tastes of iron since the last storm.\"\n\n"
                    "\"Someone left an offering at the shrine at midnight. I didn't see who.\""
                ),
                "field_type": "choice",
                "choices": ["more", "leave"],
                "params": {
                    "route_on_answer": {"more": "topic", "leave": "farewell"},
                },
            },
            {
                "slug": "trade",
                "title": "Coconut — Trade",
                "prompt": (
                    "\"Fresh coconuts, two septims. Dried slices for the road, five.\"\n\n"
                    "\"Pay first. Coconut's policy.\""
                ),
                "field_type": "choice",
                "choices": ["buy", "more", "leave"],
                "params": {
                    "route_on_answer": {
                        "buy": "trade_buy",
                        "more": "topic",
                        "leave": "farewell",
                    },
                },
            },
            {
                "slug": "trade_buy",
                "title": "Coconut",
                "prompt": (
                    "\"A fine choice. Don't drop it on the cobbles — "
                    "I won't refund dignity.\"\n\n"
                    "*(You now have a coconut.)*"
                ),
                "field_type": "choice",
                "choices": ["more", "leave"],
                "params": {
                    "route_on_answer": {"more": "topic", "leave": "farewell"},
                },
            },
            {
                "slug": "about",
                "title": "Coconut — About",
                "prompt": (
                    "\"Name's Coconut. My mother had a sense of humor.\"\n\n"
                    "\"Twenty years on this road. I know who's lying and who's just ugly.\"\n\n"
                    "\"Don't ask which you are.\""
                ),
                "field_type": "choice",
                "choices": ["more", "leave"],
                "params": {
                    "route_on_answer": {"more": "topic", "leave": "farewell"},
                },
            },
            {
                "slug": "farewell",
                "title": "Coconut",
                "prompt": (
                    "\"Safe roads, traveler. And if the bells ring twice at dawn — "
                    "don't look back.\"\n\n"
                    "*(Coconut returns to arranging her wares.)*"
                ),
                "field_type": "text",
                "required": False,
                "params": {"complete_on": ["exit", "done", "leave", "bye", ""]},
            },
        ],
    },
)

COCONUT_NPC_PROCESS = ProcessDefinition(
    id="proc-coconut-npc",
    name="coconut-npc",
    flows=[COCONUT_NPC_FLOW],
    metadata={
        "example": True,
        "description": "Branching wizard reference — hub menu, transforms, routing",
    },
)


def register_definitions(repository: object) -> None:
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(COCONUT_NPC_FLOW)
    if callable(save_process):
        save_process(COCONUT_NPC_PROCESS)


__all__ = [
    "COCONUT_NPC_FLOW",
    "COCONUT_NPC_PROCESS",
    "register_definitions",
]