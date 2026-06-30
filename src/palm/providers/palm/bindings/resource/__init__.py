"""Resource engine bindings — provider contract surface."""

from palm.providers.palm.bindings.resource.descriptor import describe, health
from palm.providers.palm.bindings.resource.invoke import (
    fetch_job,
    inject_parent_job_from_state,
    invoke_action,
    new_child_job_id,
)

__all__ = [
    "describe",
    "fetch_job",
    "health",
    "inject_parent_job_from_state",
    "invoke_action",
    "new_child_job_id",
]
