"""File document resource provider package."""

from plugins.providers.file import registry as registry
from plugins.providers.file.provider import FileProvider

__all__ = ["FileProvider", "registry"]