"""Compat re-export — prefer :mod:`services.inspect.registry`."""

from services.inspect.registry import ObserveOperation, ObserveVerb, observe_verbs

__all__ = ["ObserveOperation", "ObserveVerb", "observe_verbs"]
