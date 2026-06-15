"""
Transform wizard example — declarative transform steps inside a wizard flow.

Demonstrates ``step_kind: transform`` with the ``string_format`` rule: collect a
name, build a greeting, pick a role, and format a badge — then review in summary.

Try::

    palm flow start transform-example
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition

TRANSFORM_EXAMPLE_FLOW = FlowDefinition(
    id="flow-transform-example",
    name="transform-example",
    pattern="wizard",
    state_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "minLength": 2},
            "greeting": {"type": "string"},
            "role": {"type": "string", "enum": ["developer", "manager", "designer"]},
            "badge": {"type": "string"},
        },
        "required": ["name", "greeting", "role", "badge"],
    },
    options={
        "include_summary": True,
        "allow_backtrack": True,
        "steps": [
            {
                "slug": "name",
                "title": "Your Name",
                "prompt": "What should we call you?",
                "state_schema": {"type": "string", "minLength": 2},
            },
            {
                "slug": "format_greeting",
                "step_kind": "transform",
                "title": "Greeting",
                "source_key": "name",
                "target_key": "greeting",
                "rule": "string_format",
                "options": {
                    "template": "Hello, {value}!",
                    "case": "title",
                },
            },
            {
                "slug": "role",
                "title": "Your Role",
                "prompt": "Pick a role",
                "field_type": "choice",
                "choices": ["developer", "manager", "designer"],
            },
            {
                "slug": "format_badge",
                "step_kind": "transform",
                "title": "Badge",
                "source_key": "role",
                "target_key": "badge",
                "rule": "string_format",
                "options": {
                    "template": "[{value}]",
                    "case": "upper",
                },
            },
        ],
    },
)

TRANSFORM_EXAMPLE_PROCESS = ProcessDefinition(
    id="proc-transform-example",
    name="transform-example",
    flows=[TRANSFORM_EXAMPLE_FLOW],
    metadata={
        "example": True,
        "description": "Wizard with string_format transform steps between inputs",
    },
)


def register_definitions(repository: object) -> None:
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(TRANSFORM_EXAMPLE_FLOW)
    if callable(save_process):
        save_process(TRANSFORM_EXAMPLE_PROCESS)