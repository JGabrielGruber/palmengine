"""
Palm Core — pure foundational engines.

**Invariant:** nothing inside ``palm.core`` may import from outside ``palm.core``.

Engines:
- ``behavior_tree`` — control-flow patterns with pluggable state
- ``context`` — scoped metadata and ``BaseState`` for execution state
- ``resource`` — external provider coordination
- ``storage`` — persistence backend coordination
- ``orchestration`` — job lifecycle
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
from palm.core.context import STATE_FRAME_KEY, BaseState, ContextEngine
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
from palm.core.orchestration import (
    ExecutionBackend,
    ExecutionContext,
    InputCapable,
    Job,
    JobHook,
    JobHookAdapter,
    JobRunner,
    JobScheduler,
    JobState,
    JobStatus,
    OrchestrationEngine,
    OrchestrationEventType,
    OrchestrationMode,
    RunResult,
    StepInspectable,
)
from palm.core.registry import (
    pattern_registry,
    provider_registry,
    storage_registry,
)
from palm.core.resource import BaseProvider, ResourceEngine
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
    "ExecutionBackend",
    "ExecutionContext",
    "InputCapable",
    "Job",
    "JobHook",
    "JobHookAdapter",
    "JobRunner",
    "JobScheduler",
    "JobState",
    "JobStatus",
    "OrchestrationEngine",
    "OrchestrationEventType",
    "OrchestrationMode",
    "RunResult",
    "StepInspectable",
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
