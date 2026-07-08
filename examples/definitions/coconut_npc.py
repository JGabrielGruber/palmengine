"""
Coconut NPC — branching wizard reference flow (hub menu + transforms + routing).

Dogfood profile for **compositional interactive workflows**: hub menu, built-in
transforms, ``step_kind: branch`` for returning travelers, and KV persistence.

Patterns demonstrated:

- Hub-and-spoke topic menu with loop-back (``"more": "topic"``)
- ``string_format`` + ``lookup`` + ``conditional`` transform steps
- ``step_kind: branch`` — skip reputation when ``is_returning`` (ADR-012)
- Cross-session KV persistence keyed by ``player_name`` (``kv`` provider, 0.28.2)

Try::

    palm flow start coconut-npc

MCP::

    palm_flows_create_session(flow_id="coconut-npc")
    palm_flows_session(session_id, flow_id="coconut-npc", format="assistant")
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition

MOOD_BY_REPUTATION: dict[str, str] = {
    "friend": "\"Good. Friends get the sweet coconuts and the good rumors.\"",
    "stranger": "\"Strangers pay full price and get the boring rumors.\"",
    "trouble": "\"Trouble gets watched. And the coconuts with the soft spots.\"",
}

RETURNING_TOPIC_BY_REPUTATION: dict[str, str] = {
    "friend": (
        "*(She grins — she knows your face.)*\n\n"
        "\"Welcome back, friend. Rumors, trade, or are you done for today?\""
    ),
    "stranger": (
        "*(She squints, not quite placing you.)*\n\n"
        "\"Still a stranger, then. Rumors, trade, or on your way?\""
    ),
    "trouble": (
        "*(She keeps one hand near the scales.)*\n\n"
        "\"Trouble again. Rumors, trade, or walk away while you can?\""
    ),
}

FIRST_TOPIC_PROMPT = (
    "*(She leans on the cart.)*\n\n"
    "\"Well then. What'll it be?\""
)

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
                "Branching wizard reference — hub menu, transforms, branch step, routing. "
                "See docs/adr/012-wizard-branch-step.md and examples/README.md."
            ),
            "tags": ["branching", "transform", "routing", "reference", "kv", "persistence"],
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
                "slug": "load_player",
                "title": "Recall traveler",
                "step_kind": "resource",
                "resource_ref": "load-coconut-player",
                "output_key": "player_profile_load",
            },
            {
                "slug": "unwrap_profile",
                "step_kind": "transform",
                "title": "Load profile",
                "source_key": "player_profile_load",
                "target_key": "player_profile",
                "rule": "jsonpath_extract",
                "options": {"path": "value", "default": {}},
            },
            {
                "slug": "stamp_player_name",
                "step_kind": "transform",
                "title": "Stamp player name",
                "source_key": "player_profile",
                "target_key": "player_profile",
                "rule": "jsonpath_set",
                "options": {
                    "path": "player_name",
                    "set_value_from_key": "player_name",
                },
            },
            {
                "slug": "mark_returning",
                "step_kind": "transform",
                "title": "Returning traveler?",
                "source_key": "player_profile",
                "target_key": "is_returning",
                "rule": "conditional",
                "options": {
                    "field": "visit_count",
                    "gt": 0,
                    "then": True,
                    "else": False,
                },
            },
            {
                "slug": "returning_note",
                "step_kind": "transform",
                "title": "Returning note",
                "source_key": "is_returning",
                "target_key": "returning_note",
                "rule": "conditional",
                "options": {
                    "is_truthy": True,
                    "then": " I remember you.",
                    "else": "",
                },
            },
            {
                "slug": "merge_returning_note",
                "step_kind": "transform",
                "title": "Merge returning note",
                "source_key": "player_profile",
                "target_key": "player_profile",
                "rule": "jsonpath_set",
                "options": {
                    "path": "returning_note",
                    "set_value_from_key": "returning_note",
                },
            },
            {
                "slug": "build_greeting",
                "step_kind": "transform",
                "title": "Coconut sizes you up",
                "source_key": "player_profile",
                "target_key": "greeting_line",
                "rule": "string_format",
                "options": {
                    "template": (
                        "Ah, {player_name}{returning_note} — Coconut wipes her hands "
                        "on her apron and studies you."
                    ),
                },
            },
            {
                "slug": "reputation_gate",
                "step_kind": "branch",
                "title": "Reputation routing",
                "when": {"field": "is_returning", "is_truthy": True},
                "then": [
                    {
                        "slug": "seed_reputation",
                        "step_kind": "transform",
                        "title": "Restore reputation",
                        "source_key": "player_profile",
                        "target_key": "reputation",
                        "rule": "jsonpath_extract",
                        "options": {"path": "reputation", "default": "stranger"},
                    },
                    {
                        "slug": "restore_mood",
                        "step_kind": "transform",
                        "title": "Coconut remembers",
                        "source_key": "reputation",
                        "target_key": "mood_line",
                        "rule": "lookup",
                        "options": {
                            "table": MOOD_BY_REPUTATION,
                            "default": "\"Hmph.\"",
                        },
                    },
                    {
                        "slug": "restore_topic",
                        "step_kind": "transform",
                        "title": "Returning topic menu",
                        "source_key": "reputation",
                        "target_key": "topic_prompt",
                        "rule": "lookup",
                        "options": {
                            "table": RETURNING_TOPIC_BY_REPUTATION,
                            "default": FIRST_TOPIC_PROMPT,
                        },
                    },
                ],
                "else": [
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
                            "table": MOOD_BY_REPUTATION,
                            "default": "\"Hmph.\"",
                        },
                    },
                    {
                        "slug": "first_topic_prompt",
                        "step_kind": "transform",
                        "title": "First-visit topic menu",
                        "source_key": "mood_line",
                        "target_key": "topic_prompt",
                        "rule": "string_format",
                        "options": {"template": FIRST_TOPIC_PROMPT},
                    },
                ],
            },
            {
                "slug": "merge_reputation",
                "step_kind": "transform",
                "title": "Merge reputation",
                "source_key": "player_profile",
                "target_key": "player_profile",
                "rule": "jsonpath_set",
                "options": {
                    "path": "reputation",
                    "set_value_from_key": "reputation",
                },
            },
            {
                "slug": "prep_visit_count",
                "step_kind": "transform",
                "title": "Next visit count",
                "source_key": "player_profile",
                "target_key": "next_visit_count",
                "rule": "calculate",
                "options": {"expression": "visit_count + 1"},
            },
            {
                "slug": "merge_visit_count",
                "step_kind": "transform",
                "title": "Merge visit count",
                "source_key": "player_profile",
                "target_key": "player_profile",
                "rule": "jsonpath_set",
                "options": {
                    "path": "visit_count",
                    "set_value_from_key": "next_visit_count",
                },
            },
            {
                "slug": "save_profile",
                "title": "Save profile",
                "step_kind": "resource",
                "resource_ref": "save-coconut-player",
            },
            {
                "slug": "topic",
                "title": "Coconut",
                "prompt": "{{ state.mood_line }}\n\n{{ state.topic_prompt }}",
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
                "slug": "save_profile_farewell",
                "title": "Save profile (farewell)",
                "step_kind": "resource",
                "resource_ref": "save-coconut-player",
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
        "description": "Branching wizard reference — hub menu, branch step, KV persistence",
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
    "FIRST_TOPIC_PROMPT",
    "MOOD_BY_REPUTATION",
    "RETURNING_TOPIC_BY_REPUTATION",
    "register_definitions",
]