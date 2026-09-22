"""Authoring resource provider package (0.70.5).

Working name ``authoring``. Duals the kit package. José may rename.
Walks ``palm.kits.authoring.bound().commit`` (started host, ``0.70.7``). See SD-025.
"""

from plugins.providers.authoring import registry as registry
from plugins.providers.authoring.provider import AuthoringProvider

__all__ = ["AuthoringProvider", "registry"]
