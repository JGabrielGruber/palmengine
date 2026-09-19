"""Authoring resource provider package (0.70.5).

Working name ``authoring``. Duals the kit package. José may rename.
Walks ``palm.kits.authoring.bound().commit``. See SD-025.
"""

from palm.providers.authoring import registry as registry
from palm.providers.authoring.provider import AuthoringProvider

__all__ = ["AuthoringProvider", "registry"]
