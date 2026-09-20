"""Shared auth helpers used by host CQRS and server surfaces."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from palm.system.runtime.base import BaseRuntime


def current_principal_id(runtime: BaseRuntime) -> str | None:
    principal = runtime.auth.principal
    return principal.id if principal is not None else None
