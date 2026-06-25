"""
Wizard app manifest — declares Palm layer dependencies and registry hooks.

Read this file first to understand which Palm subsystems the wizard pattern dogfoods.
"""

from __future__ import annotations

from typing import Any

WIZARD_APP: dict[str, Any] = {
    "name": "wizard",
    "label": "Interactive multi-step flow",
    "palm_layers": [
        "core.behavior_tree",
        "core.context",
        "core.event",
        "core.resource",
        "core.orchestration",
        "common.patterns",
        "common.transforms",
        "common.resource",
        "common.compensation",
        "definitions.flow",
        "instances",
    ],
    "registry_hooks": [
        "builder",
        "instance_sync",
        "submission_metadata",
    ],
}

__all__ = ["WIZARD_APP"]