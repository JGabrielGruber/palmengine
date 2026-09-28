"""Compat re-export — prefer :class:`services.inspect.InspectService`."""

from services.inspect.service import InspectService, InspectService as SystemService

__all__ = ["InspectService", "SystemService"]
