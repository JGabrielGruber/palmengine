from palm.common.operator.session_view_registry import register_session_view_enricher
from services.assist.service import AssistService
from services.assist.session import AssistSession
from services.assist.session_view_enricher import merge_assist_session_actions

# Contribute the assist CTA enricher on package import (django-app style), so
# `common`'s flow session view blends assist verbs without importing assist up.
register_session_view_enricher(merge_assist_session_actions)

__all__ = ["AssistService", "AssistSession"]