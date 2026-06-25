"""Typed exceptions for the REST resource provider."""

from __future__ import annotations

from typing import Any


class RestProviderError(Exception):
    """Base error for REST provider failures."""


class RestRemoteError(RestProviderError):
    """Raised when an HTTP request fails."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        payload: Any = None,
        transient: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload
        self.transient = transient