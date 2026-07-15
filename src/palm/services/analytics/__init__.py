"""Analytics domain — BI exposure / query / present (0.35+)."""

# Contribute the analytics preflight probe on package import (django-app style),
# so `common` drains it rather than importing analytics up. The host imports this
# package at module load, so the probe is present by doctor/preflight time.
from palm.common.resource.preflight_registry import register_resource_preflight_probe
from palm.services.analytics.errors import (
    AnalyticsActionNotAllowedError,
    AnalyticsDisabledError,
    AnalyticsError,
    DatasetNotFoundError,
)
from palm.services.analytics.exposure import (
    AnalyticsExposure,
    is_analytics_published,
    parse_analytics_exposure,
)
from palm.services.analytics.preflight import build_analytics_preflight
from palm.services.analytics.service import AnalyticsService

register_resource_preflight_probe("analytics", build_analytics_preflight)

__all__ = [
    "AnalyticsActionNotAllowedError",
    "AnalyticsDisabledError",
    "AnalyticsError",
    "AnalyticsExposure",
    "AnalyticsService",
    "DatasetNotFoundError",
    "is_analytics_published",
    "parse_analytics_exposure",
]
