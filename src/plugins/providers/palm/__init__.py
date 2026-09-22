"""Built-in Palm compositional provider."""

from plugins.providers.palm import registry as registry  # — side effect
from plugins.providers.palm.bindings.recursion.guard import (
    PalmRecursionError,
    RecursionLimits,
    palm_invoke_frame,
)
from plugins.providers.palm.bindings.runtimes.wiring import clear_palm_runtime
from plugins.providers.palm.events_client import PalmEventsClient
from plugins.providers.palm.events_ws import PalmEventsWebSocketClient, http_base_to_ws_url
from plugins.providers.palm.exceptions import (
    PalmLocalError,
    PalmProviderError,
    PalmRemoteError,
    PalmTimeoutError,
)
from plugins.providers.palm.flow.coordinator import PalmInvokeCoordinator
from plugins.providers.palm.flow.params import PalmInvokeParams
from plugins.providers.palm.provider import PalmProvider

__all__ = [
    "PalmEventsClient",
    "PalmEventsWebSocketClient",
    "http_base_to_ws_url",
    "PalmInvokeCoordinator",
    "PalmInvokeParams",
    "PalmLocalError",
    "PalmProvider",
    "PalmProviderError",
    "PalmRecursionError",
    "PalmRemoteError",
    "PalmTimeoutError",
    "RecursionLimits",
    "clear_palm_runtime",
    "palm_invoke_frame",
]
