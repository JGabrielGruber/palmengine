# Register the definitions CQRS contributor on package import (django-app style)
# so it is present whenever this service app is autoloaded — no import-for-side-effect
# from `common`. See palm.services._apps.autoload / palm.common.cqrs.catalog.
from palm.services.definitions.bindings.cqrs import (
    contributor as _cqrs_contributor,  # noqa: F401
)
from palm.services.definitions.service import DefinitionService

__all__ = ["DefinitionService"]