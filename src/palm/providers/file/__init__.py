"""File document resource provider package."""

from palm.providers.file import registry as registry
from palm.providers.file.provider import FileProvider

__all__ = ["FileProvider", "registry"]