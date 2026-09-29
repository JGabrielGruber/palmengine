"""
WorkloadRuntime adapters — isolation backends for WorkloadEngine.

Not process surfaces (``palm.runtimes``). Register via ``registry.py`` per runner.
See docs/VISION-0.56.md · ADR-024.

``autoload`` does not import a runner. Import the runner module to register it.
"""

from drivers.runners._apps import INSTALLED_RUNNERS, autoload

__all__ = ["INSTALLED_RUNNERS", "autoload"]
