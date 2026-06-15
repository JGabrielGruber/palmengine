"""
Transform pipeline demo — declarative transform steps in a flow definition.

Runs built-in rules from ``palm.common.transforms`` via the ``pipeline`` pattern
and :class:`~palm.core.behavior_tree.nodes.leaf.transform_leaf.TransformLeaf`.

Try::

    palm flow start transform-demo

Or drive programmatically::

    from palm.common.patterns import build_pattern
    from palm.common.transforms import autoload

    autoload()
    pattern = build_pattern(flow, context)
    pattern.tick(state)
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition

TRANSFORM_DEMO_FLOW = FlowDefinition(
    id="flow-transform-demo",
    name="transform-demo",
    pattern="pipeline",
    options={
        "initial_state": {
            "raw_users": [
                {"first_name": "Ada", "active": True},
                {"first_name": "Bob", "active": False},
                {"first_name": "Grace", "active": True},
            ],
        },
        "steps": [
            {
                "name": "normalize_names",
                "source_key": "raw_users",
                "target_key": "users",
                "rule": "rename_field",
                "batch": True,
                "options": {"from_key": "first_name", "to_key": "name"},
            },
            {
                "name": "keep_active",
                "source_key": "users",
                "target_key": "active_users",
                "rule": "filter_items",
                "options": {"field": "active", "equals": True},
            },
        ],
    },
)

TRANSFORM_DEMO_PROCESS = ProcessDefinition(
    id="proc-transform-demo",
    name="transform-demo",
    flows=[TRANSFORM_DEMO_FLOW],
    metadata={
        "example": True,
        "description": "Pipeline of rename_field + filter_items transform steps",
    },
)


def register_definitions(repository: object) -> None:
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(TRANSFORM_DEMO_FLOW)
    if callable(save_process):
        save_process(TRANSFORM_DEMO_PROCESS)
