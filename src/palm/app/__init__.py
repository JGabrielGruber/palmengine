"""
Palm application layer — configuration, bootstrap, and multi-runtime orchestration.

Prefer :class:`~palm.app.host.ApplicationHost` for CLI, services, and deployments.
Use :class:`~palm.app.kernel.PalmKernel` directly only for low-level embedding tests.
"""

from palm.app.host.roles import DeploymentProfile
from palm.app.kernel import PalmKernel
from palm.app.registry import RuntimeHandle, RuntimeKind, RuntimeRegistry
from palm.app.session import create_cli_host, create_console
from palm.app.settings import PalmSettings

__all__ = [
    "ApplicationHost",
    "DeploymentProfile",
    "PalmKernel",
    "PalmSettings",
    "RuntimeHandle",
    "RuntimeKind",
    "RuntimeRegistry",
    "create_cli_host",
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
