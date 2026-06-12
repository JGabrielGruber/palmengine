"""
Core exception hierarchy for Palm engines.

All engines raise subclasses of ``PalmError``. Domain and runtime layers
may wrap or extend these at their own boundaries.
"""

from __future__ import annotations


class PalmError(Exception):
    """Base exception for all Palm core failures."""


class EngineError(PalmError):
    """Raised when an engine encounters an unrecoverable internal error."""


class RegistryError(PalmError):
    """Raised when registry lookup or registration fails."""


class ConfigurationError(PalmError):
    """Raised when engine configuration is invalid or incomplete."""


class StorageError(EngineError):
    """Raised when storage operations fail."""


class StorageNotConfiguredError(StorageError):
    """Raised when the storage engine has no active backend."""


class BackendNotOpenError(StorageError):
    """Raised when an operation requires an open backend."""


class StoragePermissionError(StorageError):
    """Raised when the active backend cannot read or write due to permissions."""


class StorageCorruptionError(StorageError):
    """Raised when persisted data cannot be decoded."""


class ContextError(EngineError):
    """Raised when context stack operations fail."""


class StateError(EngineError):
    """Raised when state operations fail."""


class StateNotConfiguredError(StateError):
    """Raised when an engine requires state but none is bound."""


class StateValidationError(StateError):
    """Raised when state values fail schema validation."""
