"""
WorkloadRuntime adapters — isolation backends for WorkloadEngine.

Not process surfaces (``palm.runtimes``). Register via ``registry.py`` per runner.
See docs/VISION-0.56.md · ADR-024.

Registries populate via :func:`autoload` at bootstrap
(:func:`palm.common.plugins.ensure_core_plugins`), not on package import.
"""

from palm.runners._apps import INSTALLED_RUNNERS, autoload

__all__ = ["INSTALLED_RUNNERS", "autoload"]
