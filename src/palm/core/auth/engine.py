"""
Auth engine — credential and principal abstractions.

Defines authentication contracts without binding to OAuth, JWT, or API-key
implementations (those belong in future provider extensions).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from palm.core.base import BasePalmEngine


@dataclass(frozen=True)
class Principal:
    """Authenticated subject."""

    id: str
    roles: tuple[str, ...] = ()


class AuthEngine(BasePalmEngine):
    """Tracks the current principal and authorization checks."""

    def __init__(self) -> None:
        super().__init__(name="auth")
        self._principal: Principal | None = None

    @property
    def principal(self) -> Principal | None:
        return self._principal

    def authenticate(self, credentials: dict[str, Any]) -> Principal | None:
        """Validate credentials and set the current principal (stub)."""
        subject = credentials.get("subject")
        if not subject:
            return None
        self._principal = Principal(id=str(subject), roles=("user",))
        return self._principal

    def bind_principal(self, principal: Principal) -> Principal:
        """Set the active principal (runtime wiring and trusted callers)."""
        self._principal = principal
        return principal

    def authorize(self, *required_roles: str) -> bool:
        if self._principal is None:
            return False
        return any(role in self._principal.roles for role in required_roles)

    def _do_initialize(self, **options: Any) -> None:
        pass

    def _do_shutdown(self) -> None:
        self._principal = None
