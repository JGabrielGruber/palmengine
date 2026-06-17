"""Built-in Palm compositional provider."""

from palm.providers.palm import registry as registry  # noqa: F401 — side effect
from palm.providers.palm.provider import PalmProvider

__all__ = ["PalmProvider"]