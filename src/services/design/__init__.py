# Register the design CQRS contributor on package import (django-app style) so
# it is present whenever this service app is autoloaded — no import-for-side-effect
# from `common`. See services._apps.autoload / palm.common.cqrs.schemas.
from services.design.bindings.cqrs import contributor as _cqrs_contributor  # noqa: F401
from services.design.service import DesignService

__all__ = ["DesignService"]