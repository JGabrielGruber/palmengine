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


class ContextError(EngineError):
    """Raised when context stack operations fail."""