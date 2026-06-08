"""
PlanRegistry — in-memory staging for prepared execution plans.

Supports deferred submission (prepare now, submit later) for server runtimes
and future batch coordinators.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

from palm.common.exceptions import PlanNotFoundError

if TYPE_CHECKING:
    from palm.common.plans.execution_plan import ExecutionPlan


@dataclass(frozen=True)
class StoredPlan:
    """A validated plan held for deferred submission."""

    plan_id: str
    plan: ExecutionPlan
    principal_id: str | None = None


class PlanRegistry:
    """Thread-safe store of prepared :class:`~palm.common.plans.execution_plan.ExecutionPlan` objects."""

    def __init__(self) -> None:
        self._entries: dict[str, StoredPlan] = {}
        self._lock = threading.RLock()

    def store(self, plan: ExecutionPlan, *, principal_id: str | None = None) -> StoredPlan:
        """Validate and stage a plan; returns the stored record."""
        plan.validate()
        plan_id = f"plan-{uuid.uuid4().hex[:12]}"
        stored = StoredPlan(plan_id=plan_id, plan=plan, principal_id=principal_id)
        with self._lock:
            self._entries[plan_id] = stored
        return stored

    def get(self, plan_id: str) -> StoredPlan:
        with self._lock:
            stored = self._entries.get(plan_id)
        if stored is None:
            raise PlanNotFoundError(plan_id)
        return stored

    def consume(self, plan_id: str) -> ExecutionPlan:
        """Remove and return a staged plan (one-shot submission)."""
        with self._lock:
            stored = self._entries.pop(plan_id, None)
        if stored is None:
            raise PlanNotFoundError(plan_id)
        return stored.plan

    def summary(self, stored: StoredPlan) -> dict[str, object]:
        plan = stored.plan
        return {
            "plan_id": stored.plan_id,
            "job_id": plan.job_id,
            "metadata": dict(plan.metadata),
            "principal_id": stored.principal_id,
        }