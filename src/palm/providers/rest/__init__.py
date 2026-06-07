"""Rest provider app."""

from palm.providers.rest import registry as registry
from palm.providers.rest.provider import RestProvider

__all__ = ["RestProvider", "registry"]
