"""
Palm application layer — configuration, bootstrap, and multi-runtime orchestration.

Use :class:`~palm.app.app.PalmApp` as the top-level entrypoint when embedding
Palm in services, tests, or multi-process deployments.
"""

from palm.app.app import CLI_RUNTIME_NAME, PalmApp
from palm.app.host.roles import HostProfile
from palm.app.registry import RuntimeHandle, RuntimeKind, RuntimeRegistry
from palm.app.session import create_cli_app, create_console
from palm.app.settings import PalmSettings

__all__ = [
    "ApplicationHost",
    "CLI_RUNTIME_NAME",
    "HostProfile",
    "PalmApp",
    "PalmSettings",
    "RuntimeHandle",
    "RuntimeKind",
    "RuntimeRegistry",
    "create_cli_app",
    "create_console",
    "run_host",
]

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "ApplicationHost": ("palm.app.host.application_host", "ApplicationHost"),
    "run_host": ("palm.app.host.application_host", "run_host"),
}


def __getattr__(name: str) -> object:
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_path, attr = _LAZY_EXPORTS[name]
    import importlib

    module = importlib.import_module(module_path)
    value = getattr(module, attr)
    globals()[name] = value
    return value
