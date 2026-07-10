"""Analytics domain errors (0.35)."""

from __future__ import annotations


class AnalyticsError(Exception):
    """Base analytics error with machine-readable ``code``."""

    def __init__(self, message: str, *, code: str, http_status: int = 400) -> None:
        self.code = code
        self.http_status = http_status
        super().__init__(message)


class DatasetNotFoundError(AnalyticsError):
    """Missing or unpublished dataset (404 — do not leak existence)."""

    def __init__(self, dataset: str) -> None:
        self.dataset = dataset
        super().__init__(
            f"Dataset not found: {dataset}",
            code="dataset_not_found",
            http_status=404,
        )


class AnalyticsActionNotAllowedError(AnalyticsError):
    """Published resource action is not BI-safe (403)."""

    def __init__(self, dataset: str, action: str) -> None:
        self.dataset = dataset
        self.action = action
        super().__init__(
            f"Analytics cannot invoke action {action!r} on {dataset}",
            code="analytics_action_not_allowed",
            http_status=403,
        )


class AnalyticsDisabledError(AnalyticsError):
    """Analytics domain disabled on this host (503)."""

    def __init__(self) -> None:
        super().__init__(
            "Analytics is disabled",
            code="analytics_disabled",
            http_status=503,
        )


class AnalyticsResponseTooLargeError(AnalyticsError):
    """Serialized row payload exceeds configured byte cap."""

    def __init__(self, size: int, limit: int) -> None:
        super().__init__(
            f"Analytics response too large ({size} > {limit} bytes)",
            code="response_too_large",
            http_status=413,
        )


__all__ = [
    "AnalyticsActionNotAllowedError",
    "AnalyticsDisabledError",
    "AnalyticsError",
    "AnalyticsResponseTooLargeError",
    "DatasetNotFoundError",
]
