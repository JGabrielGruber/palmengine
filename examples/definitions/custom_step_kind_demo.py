"""
Custom wizard step kind — register a leaf factory and use it in a flow.

Demonstrates Palm's registry-driven wizard extensibility without editing
``tree.py``.
"""

from __future__ import annotations

from palm.core.behavior_tree import ActionNode, BaseNode, PatternStatus
from palm.definitions import FlowDefinition, ProcessDefinition
from palm.patterns.wizard import WizardPhaseContext, default_wizard_step_registry


def _build_log_step(ctx: WizardPhaseContext) -> BaseNode:
    """Auto-tick step that records a marker in wizard answers."""

    slug = ctx.step.slug

    def mark(state: object) -> PatternStatus:
        from palm.patterns.wizard import WizardKeys

        answers = state.get(WizardKeys.ANSWERS, {}) or {}
        if isinstance(answers, dict):
            answers = dict(answers)
            answers[slug] = f"logged:{ctx.step.prompt}"
            state.set(WizardKeys.ANSWERS, answers)
        return PatternStatus.SUCCESS

    return ActionNode(slug, action=mark)


default_wizard_step_registry().register("log", _build_log_step)

CUSTOM_STEP_FLOW = FlowDefinition(
    id="flow-custom-step",
    name="custom_step_demo",
    pattern="wizard",
    options={
        "steps": [
            {"slug": "name", "title": "Name", "prompt": "Your name?"},
            {
                "slug": "audit",
                "title": "Audit",
                "prompt": "custom-step-demo",
                "step_kind": "log",
            },
        ],
    },
)

CUSTOM_STEP_PROCESS = ProcessDefinition(
    id="proc-custom-step",
    name="custom-step-demo",
    flows=[CUSTOM_STEP_FLOW],
)


def register_definitions(repository: object) -> None:
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(CUSTOM_STEP_FLOW)
    if callable(save_process):
        save_process(CUSTOM_STEP_PROCESS)