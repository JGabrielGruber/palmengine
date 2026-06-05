"""
Embedded runtime — in-process Palm execution for libraries and tests.
"""

from __future__ import annotations

from typing import Any

import palm.patterns  # — register patterns
import palm.providers  # — register providers
import palm.storages  # noqa: F401 — register backends
from palm import __version__
from palm.core import BehaviorTreeEngine, OrchestrationEngine, StorageEngine


class EmbeddedRuntime:
    """Wires core engines for in-process use."""

    def __init__(self) -> None:
        self.behavior_tree = BehaviorTreeEngine()
        self.orchestration = OrchestrationEngine()
        self.storage = StorageEngine()

    def start(self, **options: Any) -> None:
        self.behavior_tree.initialize(**options)
        self.orchestration.initialize(**options)
        self.storage.initialize(backend=options.get("backend", "memory"))

    def stop(self) -> None:
        self.storage.shutdown()
        self.orchestration.shutdown()
        self.behavior_tree.shutdown()

    @property
    def version(self) -> str:
        return __version__
