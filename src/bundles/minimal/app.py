"""Minimal application.

One system instance. Memory storage. Structure definition ``local.embedded``.
This module does not install plugin packages and does not read a composition record.
"""

from __future__ import annotations

from bundles.minimal.bind import bind_memory
from bundles.minimal.runtime import MinimalRuntime

_STRUCTURE_ID = "local.embedded"


class MinimalApp:
    """Start and stop one constrained system instance.

    The runtime exists before ``start`` so the caller can install registries.
    """

    def __init__(self) -> None:
        self._runtime = MinimalRuntime()

    @property
    def runtime(self) -> MinimalRuntime:
        return self._runtime

    def start(self) -> MinimalRuntime:
        """Walk the system schedule. Return the running instance."""
        if self._runtime.is_started:
            return self._runtime
        self._runtime.start(
            drivers=bind_memory(),
            structure_definition_id=_STRUCTURE_ID,
        )
        return self._runtime

    def stop(self) -> None:
        """Stop the system instance when it is running."""
        if self._runtime.is_started:
            self._runtime.stop()

    def __enter__(self) -> MinimalApp:
        self.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.stop()
