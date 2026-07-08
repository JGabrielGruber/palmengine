"""KV provider registration."""

from palm.core.registry import provider_registry
from palm.providers.kv.app import kv_app
from palm.providers.kv.provider import KvProvider

provider_registry.register("kv", KvProvider)
kv_app.register()