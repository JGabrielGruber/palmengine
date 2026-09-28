"""Product inspect door — present operator views over system facts.

Home for :class:`InspectService` (0.61.4 / SD-007). Formerly
``services.system`` / ``SystemService`` — that package remains a thin
import shim.

0.61.5: :meth:`InspectService.top` / :meth:`InspectService.vitality` present
system vitality projection only.

0.61.6 / OD-001: :meth:`InspectService.doctor` is demoted anatomy packaging.

0.61.11: :meth:`InspectService.benchmark` presents vitality tool (opt-in).
"""

from services.inspect.present import (
    present_benchmark,
    present_doctor,
    present_top,
    present_vitality,
)
from services.inspect.service import InspectService

__all__ = [
    "InspectService",
    "present_benchmark",
    "present_doctor",
    "present_top",
    "present_vitality",
]
