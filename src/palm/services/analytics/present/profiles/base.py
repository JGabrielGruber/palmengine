"""Analytics present profile enum."""

from __future__ import annotations

from enum import Enum


class AnalyticsPresentProfile(str, Enum):
    RAW = "raw"
    TABLE = "table"
    SERIES = "series"
    KPI = "kpi"


__all__ = ["AnalyticsPresentProfile"]
