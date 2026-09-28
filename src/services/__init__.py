"""Product services.

The composition record names which service packages to import.
:func:`services._apps.autoload` walks those names.
Importing this package does not import those services.
"""

from __future__ import annotations

import importlib
from typing import Any

from services._apps import INSTALLED_SERVICES, autoload

_EXPORTS: dict[str, tuple[str, str]] = {
    "ContinueTarget": ("services.session", "ContinueTarget"),
    "DefinitionService": ("services.definitions", "DefinitionService"),
    "ExecutionService": ("services.execution", "ExecutionService"),
    "FlowExecutionService": ("services.execution", "FlowExecutionService"),
    "FlowSession": ("services.execution", "FlowSession"),
    "InspectService": ("services.inspect", "InspectService"),
    "ReplSession": ("services.execution", "ReplSession"),
    "SessionService": ("services.session", "SessionService"),
    # SD-007 compat: product SystemService was the inspect door.
    "SystemService": ("services.inspect", "InspectService"),
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
