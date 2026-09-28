"""Compat shim — product inspect lived here as ``SystemService`` (SD-007).

Prefer :mod:`services.inspect` / :class:`~services.inspect.InspectService`.
"""

from services.inspect import InspectService
from services.inspect.service import InspectService as SystemService

__all__ = ["InspectService", "SystemService"]
