"""
UnconfiguredMode — placeholder until :meth:`~palm.core.orchestration.engine.OrchestrationEngine.initialize` sets a real mode.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.core.exceptions import ConfigurationError
from palm.core.orchestration.mode.base_mode import OrchestrationMode

if TYPE_CHECKING:
    from palm.core.orchestration.engine import OrchestrationEngine
    from palm.core.orchestration.job import Job


class UnconfiguredMode(OrchestrationMode):
    """Raises when used before the engine receives an orchestration mode."""

    def __init__(self) -> None:
        super().__init__(name="UnconfiguredMode")

    def start(self) -> None:
        return None

    def shutdown(self, *, timeout: float = 5.0) -> None:
        return None

    def is_running(self) -> bool:
        return False

    def _require_mode(self) -> None:
        raise ConfigurationError(
            "OrchestrationEngine requires initialize(scheduler=...) before accepting jobs"
        )

    def submit_job(self, engine: OrchestrationEngine, job: Job) -> None:
        self._require_mode()

    def resume_job(self, engine: OrchestrationEngine, job: Job) -> None:
        self._require_mode()