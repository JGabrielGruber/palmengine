"""KV resource provider package."""

from plugins.providers.kv import registry as registry
from plugins.providers.kv.provider import KvProvider

__all__ = ["KvProvider", "registry"]