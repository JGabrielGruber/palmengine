"""REST provider resource engine bindings."""

from palm.providers.rest.bindings.resource.descriptor import describe
from palm.providers.rest.bindings.resource.invoke import fetch_resource

__all__ = ["describe", "fetch_resource"]