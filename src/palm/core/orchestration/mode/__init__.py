"""Runtime modes for orchestration."""

from palm.core.orchestration.mode.base_mode import OrchestrationMode

# Preferred name for the scheduling strategy (0.6+).
JobScheduler = OrchestrationMode

__all__ = ["JobScheduler", "OrchestrationMode"]
