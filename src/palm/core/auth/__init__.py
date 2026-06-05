"""
Auth engine — authentication and authorization primitives.

Pure core module: no imports from outside ``palm.core``.
"""

from palm.core.auth.engine import AuthEngine, Principal

__all__ = ["AuthEngine", "Principal"]
