"""REST provider resource engine bindings."""

from plugins.providers.rest.bindings.resource.descriptor import describe
from plugins.providers.rest.bindings.resource.invoke import fetch_resource

__all__ = ["describe", "fetch_resource"]
