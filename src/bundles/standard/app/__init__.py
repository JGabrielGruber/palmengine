"""
Palm application layer — configuration, bootstrap, and multi-runtime orchestration.

Prefer :class:`~palm.app.host.ApplicationHost` for CLI, services, and deployments.
Use :class:`~palm.app.kernel.PalmKernel` directly only for low-level embedding tests.
"""

from bundles.standard.app.host import ApplicationHost, run_host
from bundles.standard.app.host.composition import CompositionProfile
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.kernel import PalmKernel
from bundles.standard.app.registry import RuntimeHandle, RuntimeKind, RuntimeRegistry
from bundles.standard.app.session import create_cli_host, create_console
from bundles.standard.app.settings import PalmSettings

__all__ = [
    "ApplicationHost",
    "CompositionProfile",
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
