"""
EmbeddedMode — deprecated alias for :class:`~palm.runtimes.schedulers.inline.InlineScheduler`.
"""

from __future__ import annotations

import warnings

from palm.core.orchestration.execution.base_runner import JobRunner
from palm.runtimes.schedulers.inline import InlineScheduler


class EmbeddedMode(InlineScheduler):
    """Deprecated: use :class:`~palm.runtimes.schedulers.inline.InlineScheduler`."""

    def __init__(
        self,
        *,
        runner: JobRunner | None = None,
        backend: JobRunner | None = None,
        budget: int = 10_000,
        name: str = "EmbeddedMode",
    ) -> None:
        warnings.warn(
            "EmbeddedMode is deprecated; use InlineScheduler from palm.runtimes.schedulers",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(
            runner=runner,
            backend=backend,
            budget=budget,
            name=name,
        )