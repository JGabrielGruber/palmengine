"""Product services.

The composition record names which service packages to import.
:func:`palm.services._apps.autoload` walks those names.
Importing this package does not import those services.
"""

from __future__ import annotations

import importlib
from typing import Any

from palm.services._apps import INSTALLED_SERVICES, autoload

_EXPORTS: dict[str, tuple[str, str]] = {
    "ContinueTarget": ("palm.services.session", "ContinueTarget"),
    "DefinitionService": ("palm.services.definitions", "DefinitionService"),
    "ExecutionService": ("palm.services.execution", "ExecutionService"),
    "FlowExecutionService": ("palm.services.execution", "FlowExecutionService"),
    "FlowSession": ("palm.services.execution", "FlowSession"),
    "InspectService": ("palm.services.inspect", "InspectService"),
    "ReplSession": ("palm.services.execution", "ReplSession"),
    "SessionService": ("palm.services.session", "SessionService"),
    # SD-007 compat: product SystemService was the inspect door.
    "SystemService": ("palm.services.inspect", "InspectService"),
}


def __getattr__(name: str) -> Any:
    try:
        module_name, attr = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    value = getattr(importlib.import_module(module_name), attr)
    globals()[name] = value
    return value


__all__ = ["INSTALLED_SERVICES", "autoload", *sorted(_EXPORTS)]
