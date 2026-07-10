"""Definition-driven triggers → WorkIntent."""

from palm.common.triggers.parse import TriggerSpec, parse_triggers
from palm.common.triggers.registry import TriggerRegistry

__all__ = ["TriggerRegistry", "TriggerSpec", "parse_triggers"]
