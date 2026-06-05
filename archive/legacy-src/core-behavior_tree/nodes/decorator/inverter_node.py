"""
InverterNode – decorator that flips SUCCESS ↔ FAILURE.

RUNNING and WAITING_FOR_INPUT are passed through unchanged.

This module is part of Palm's general-purpose Behavior Tree Engine and must remain
completely independent of any wizard, UI, persistence, or domain concerns.
"""

from __future__ import annotations

from ...base import BaseNode, Blackboard, NodeStatus
from ...decorator import DecoratorNode


class InverterNode(DecoratorNode):
    """
    Inverts the terminal result of its single child.

    - Child SUCCESS → Inverter FAILURE
    - Child FAILURE → Inverter SUCCESS
    - Child RUNNING / WAITING → forwarded unchanged
    """

    def __init__(self, name: str, child: BaseNode) -> None:
        super().__init__(name, child=child)

    def _tick_impl(self, blackboard: Blackboard) -> NodeStatus:
        status = self.child.tick(blackboard)
        if status == NodeStatus.SUCCESS:
            return NodeStatus.FAILURE
        if status == NodeStatus.FAILURE:
            return NodeStatus.SUCCESS
        return status  # RUNNING or WAITING

    def __repr__(self) -> str:
        return f"InverterNode(name={self.name!r}, child={self.child.name!r})"
