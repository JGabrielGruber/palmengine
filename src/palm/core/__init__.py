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
from palm.core.context import (
    LEGACY_SCOPE_PREFIX,
    NESTED_SCOPES_KEY,
    SCOPES_ROOT_KEY,
    STATE_FRAME_KEY,
    STATE_SCOPE_FRAME_KEY,
    BaseState,
    ContextEngine,
    DictStateSchema,
    StateSchema,
    legacy_storage_key,
)
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
    StateValidationError,
    StorageCorruptionError,
    StorageError,
    StorageNotConfiguredError,
    StoragePermissionError,
)
from palm.core.orchestration import (
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
    "DictStateSchema",
    "EngineError",
    "LEGACY_SCOPE_PREFIX",
    "NESTED_SCOPES_KEY",
    "SCOPES_ROOT_KEY",
    "Event",
    "EventEngine",
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
    "StorageCorruptionError",
    "StorageEngine",
    "StorageError",
    "StorageNotConfiguredError",
    "StoragePermissionError",
    "pattern_registry",
    "provider_registry",
    "storage_registry",
    "STATE_FRAME_KEY",
    "STATE_SCOPE_FRAME_KEY",
    "StateError",
    "StateNotConfiguredError",
    "StateSchema",
    "StateValidationError",
    "legacy_storage_key",
]
