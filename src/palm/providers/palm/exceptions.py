"""Typed exceptions for the Palm compositional provider."""

from __future__ import annotations

from typing import Any


class PalmProviderError(Exception):
    """Base error for Palm provider coordination failures."""


class PalmLocalError(PalmProviderError):
    """Raised when local runtime delegation fails."""


class PalmRemoteError(PalmProviderError):
    """Raised when a remote ServerRuntime call fails."""

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


class PalmTimeoutError(PalmProviderError):
    """Raised when waiting for a child job exceeds the configured timeout."""