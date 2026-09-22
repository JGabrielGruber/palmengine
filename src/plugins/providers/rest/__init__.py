"""Rest provider app."""

from plugins.providers.rest import registry as registry
from plugins.providers.rest.provider import RestProvider

__all__ = ["RestProvider", "registry"]
