"""Process execution service — process-scoped runs."""

from __future__ import annotations

from palm.common.services.base import BaseService


class ProcessExecutionService(BaseService):
    """Process-scoped execution — populated in 0.16d."""


__all__ = ["ProcessExecutionService"]