"""Pure present profiles: raw | table | series | kpi."""

from services.analytics.present.profiles.base import AnalyticsPresentProfile
from services.analytics.present.profiles.kpi import present_kpi
from services.analytics.present.profiles.raw import present_raw
from services.analytics.present.profiles.series import present_series
from services.analytics.present.profiles.table import present_table

__all__ = [
    "AnalyticsPresentProfile",
    "present_kpi",
    "present_raw",
    "present_series",
    "present_table",
]
