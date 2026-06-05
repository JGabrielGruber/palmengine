"""
Resource engine — abstract provider coordination.

Pure core module: no imports from outside ``palm.core``.
"""

from palm.core.resource.base_provider import BaseProvider
from palm.core.resource.engine import ResourceEngine

__all__ = ["BaseProvider", "ResourceEngine"]
