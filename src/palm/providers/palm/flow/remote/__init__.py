"""Remote execution path for compositional Palm invocations."""

from palm.providers.palm.flow.remote.client import (
    get_job_remote,
    invoke_resource_remote,
    submit_flow_remote,
    submit_process_remote,
    wait_for_job_remote,
)
from palm.providers.palm.flow.remote.invoker import RemotePalmInvoker

__all__ = [
    "RemotePalmInvoker",
    "get_job_remote",
    "invoke_resource_remote",
    "submit_flow_remote",
    "submit_process_remote",
    "wait_for_job_remote",
]