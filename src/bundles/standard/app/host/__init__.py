"""
ApplicationHost — role-based deployment coordinator for Palm 0.10+.
"""

from bundles.standard.app.host.application_host import ApplicationHost, run_host
from bundles.standard.app.host.composition import CompositionProfile
from bundles.standard.app.host.events import HostEventType
from bundles.standard.app.host.roles import DeploymentProfile, DeploymentProfilePreset, DeploymentRoleName

__all__ = [
    "ApplicationHost",
    "BootMode",
    "CompositionProfile",
    "DeploymentProfile",
    "DeploymentProfilePreset",
    "DeploymentRoleName",
    "HostEventType",
    "run_host",
]
