"""
Concrete storage backends — memory, postgres, mongodb, and filesystem.

Import submodules to register backends with ``storage_registry``.
"""

from palm.storages import filesystem, memory, mongodb, postgres

__all__ = ["memory", "postgres", "mongodb", "filesystem"]
