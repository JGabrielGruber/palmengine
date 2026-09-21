"""
WorkloadRuntime adapters — isolation backends for WorkloadEngine.

Not process surfaces (``palm.runtimes``). Register via ``registry.py`` per runner.
See docs/VISION-0.56.md · ADR-024.

The composition record names which runners :func:`autoload` imports
(:func:`palm.common.plugins.ensure_core_plugins`), not package import.
"""

from palm.runners._apps import INSTALLED_RUNNERS, autoload

__all__ = ["INSTALLED_RUNNERS", "autoload"]
