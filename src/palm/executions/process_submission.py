"""
Backward-compatibility shim — import from ``palm.common`` instead.
"""

from __future__ import annotations

from palm.common.executions.process_submission import prepare_process_plans
from palm.common.plans.process_plan import ProcessPlan

__all__ = ['ProcessPlan', 'prepare_process_plans']

