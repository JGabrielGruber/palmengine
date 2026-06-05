"""
Palm Core — pure foundational engines.

**Invariant:** nothing inside ``palm.core`` may import from outside ``palm.core``.

Engines:
- ``behavior_tree`` — control-flow patterns with pluggable state
- ``state`` — ``BaseState`` abstraction for execution state
- ``resource`` — external provider coordination
- ``storage`` — persistence backend coordination
- ``orchestration`` — job lifecycle
- ``context`` — scoped execution metadata
- ``event`` — observability bus
- ``auth`` — authentication primitives
"""

from palm.core.auth import AuthEngine, Principal
from palm.core.base import BasePalmEngine
from palm.core.behavior_tree import (
    BaseNode,
    BasePattern,
    BehaviorTreeEngine,
    PatternStatus,
    RootNode,
)
from palm.core.context import ContextEngine
from palm.core.event import Event, EventEngine
from palm.core.exceptions import (
    BackendNotOpenError,
    ConfigurationError,
    ContextError,
    EngineError,
    PalmError,
    RegistryError,
    StateError,
    StateNotConfiguredError,
    StorageError,
    StorageNotConfiguredError,
)
from palm.core.orchestration import Job, JobStatus, OrchestrationEngine
from palm.core.registry import (
    pattern_registry,
    provider_registry,
    storage_registry,
)
from palm.core.resource import BaseProvider, ResourceEngine
from palm.core.state import STATE_FRAME_KEY, BaseState
from palm.core.storage import BaseBackend, StorageEngine

__all__ = [
    "AuthEngine",
    "BackendNotOpenError",
    "BaseBackend",
    "BasePalmEngine",
    "BaseNode",
    "BasePattern",
    "BaseProvider",
    "BehaviorTreeEngine",
    "BaseState",
    "ConfigurationError",
    "ContextError",
    "ContextEngine",
    "EngineError",
    "Event",
    "EventEngine",
    "Job",
    "JobStatus",
    "OrchestrationEngine",
    "PalmError",
    "PatternStatus",
    "Principal",
    "RootNode",
    "RegistryError",
    "ResourceEngine",
    "StorageEngine",
    "StorageError",
    "StorageNotConfiguredError",
    "pattern_registry",
    "provider_registry",
    "storage_registry",
    "STATE_FRAME_KEY",
    "StateError",
    "StateNotConfiguredError",
]
