"""Minimal application.

One system instance. Memory storage. Structure definition ``local.embedded``.
This module does not install plugin packages and does not read a composition record.
"""

from __future__ import annotations

from bundles.minimal.runtime import MinimalRuntime

_STORAGE_BACKEND = "memory"
_STRUCTURE_ID = "local.embedded"


class MinimalApp:
    """Start and stop one constrained system instance."""

    def __init__(self) -> None:
        self._runtime: MinimalRuntime | None = None

    @property
    def runtime(self) -> MinimalRuntime:
        if self._runtime is None or not self._runtime.is_started:
            raise RuntimeError("MinimalApp is not started")
        return self._runtime

    def start(self) -> MinimalRuntime:
        """Walk the system schedule. Return the running instance."""
        if self._runtime is not None and self._runtime.is_started:
            return self._runtime
        runtime = self._runtime or MinimalRuntime()
        runtime.start(
            storage_backend=_STORAGE_BACKEND,
            structure_definition_id=_STRUCTURE_ID,
        )
        self._runtime = runtime
        return runtime

    def stop(self) -> None:
        """Stop the system instance when it is running."""
        if self._runtime is not None and self._runtime.is_started:
            self._runtime.stop()

    def __enter__(self) -> MinimalApp:
        self.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.stop()
