"""Provider execution service — invoke surface (distinct from flows)."""

from __future__ import annotations

from palm.common.services.base import BaseService


class ProviderExecutionService(BaseService):
    """One-shot provider invocation — populated in 0.16d."""


__all__ = ["ProviderExecutionService"]