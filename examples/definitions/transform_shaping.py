"""
Transform shaping demo — pipeline using calculate, lookup, and conditional rules.

Try::

    palm flow start transform-shaping
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition

TRANSFORM_SHAPING_FLOW = FlowDefinition(
    id="flow-transform-shaping",
    name="transform-shaping",
    pattern="pipeline",
    options={
        "initial_state": {
            "order": {"sku": "widget", "price": 25, "qty": 2},
        },
        "steps": [
            {
                "name": "compute_total",
                "source_key": "order",
                "target_key": "total",
                "rule": "calculate",
                "options": {"expression": "price * qty"},
            },
            {
                "name": "resolve_category",
                "source_key": "order",
                "target_key": "category",
                "rule": "lookup",
                "options": {
                    "key_field": "sku",
                    "table": {
                        "widget": "hardware",
                        "gadget": "hardware",
                        "service": "support",
                    },
                    "default": "misc",
                },
            },
            {
                "name": "classify_order",
                "source_key": "total",
                "target_key": "size_label",
                "rule": "conditional",
                "options": {
                    "gt": 40,
                    "then": "large",
                    "else": "standard",
                },
            },
        ],
    },
)

TRANSFORM_SHAPING_PROCESS = ProcessDefinition(
    id="proc-transform-shaping",
    name="transform-shaping",
    flows=[TRANSFORM_SHAPING_FLOW],
    metadata={
        "example": True,
        "description": "Pipeline with calculate, lookup, and conditional transform rules",
    },
)


def register_definitions(repository: object) -> None:
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(TRANSFORM_SHAPING_FLOW)
    if callable(save_process):
        save_process(TRANSFORM_SHAPING_PROCESS)