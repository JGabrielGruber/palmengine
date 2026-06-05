"""
Storage engine — abstract persistence coordination.

Pure core module: no imports from outside ``palm.core``.
"""

from palm.core.storage.base_backend import BaseBackend
from palm.core.storage.engine import StorageEngine

__all__ = ["BaseBackend", "StorageEngine"]