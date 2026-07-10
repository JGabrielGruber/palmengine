"""Pure present profiles: raw | table | series | kpi."""

from palm.services.analytics.present.profiles.base import AnalyticsPresentProfile
from palm.services.analytics.present.profiles.kpi import present_kpi
from palm.services.analytics.present.profiles.raw import present_raw
from palm.services.analytics.present.profiles.series import present_series
from palm.services.analytics.present.profiles.table import present_table

__all__ = [
    "AnalyticsPresentProfile",
    "present_kpi",
    "present_raw",
    "present_series",
    "present_table",
]
