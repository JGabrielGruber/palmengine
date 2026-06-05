"""
Minimal two-step wizard for quick CLI demos.
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition

QUICK_FLOW = FlowDefinition(
    id="flow-quick",
    name="quick",
    pattern="wizard",
    options={"steps": ["alpha", "beta"], "allow_backtrack": True},
)

QUICK_PROCESS = ProcessDefinition(
    id="proc-quick",
    name="quick-demo",
    flows=[QUICK_FLOW],
)


def register_definitions(repository: object) -> None:
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(QUICK_FLOW)
    if callable(save_process):
        save_process(QUICK_PROCESS)