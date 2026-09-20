"""Wait interests — pure continue-interest vocabulary (0.55 Reactive Interests)."""

from palm.core.wait.interest import (
    KNOWN_ON_TARGET_FAILED,
    KNOWN_WAIT_KINDS,
    ON_TARGET_FAILED_FAIL_OWNER,
    ON_TARGET_FAILED_LEAVE,
    STATE_KEY_WAIT_INTERESTS,
    WAIT_INTEREST_SCHEMA_VERSION,
    WAIT_KIND_JOB,
    WAIT_KIND_WORKLOAD,
    WaitInterest,
    WaitPolicy,
    make_job_wait,
    make_workload_wait,
)
from palm.core.wait.rehydrate import (
    rehydrate_wait_interests,
    rehydrate_wait_interests_from_snapshot,
)
from palm.core.wait.state_ops import (
    clear_wait_interests,
    close_wait_interest,
    close_wait_on_job,
    find_wait_interests,
    has_open_waits,
    list_wait_interests,
    list_waits_on_job,
    open_wait_interest,
    open_wait_on_job,
)

__all__ = [
    "KNOWN_ON_TARGET_FAILED",
    "KNOWN_WAIT_KINDS",
    "ON_TARGET_FAILED_FAIL_OWNER",
    "ON_TARGET_FAILED_LEAVE",
    "STATE_KEY_WAIT_INTERESTS",
    "WAIT_INTEREST_SCHEMA_VERSION",
    "WAIT_KIND_JOB",
    "WAIT_KIND_WORKLOAD",
    "WaitInterest",
    "WaitPolicy",
    "clear_wait_interests",
    "close_wait_interest",
    "close_wait_on_job",
    "find_wait_interests",
    "has_open_waits",
    "list_wait_interests",
    "list_waits_on_job",
    "make_job_wait",
    "make_workload_wait",
    "open_wait_interest",
    "open_wait_on_job",
    "rehydrate_wait_interests",
    "rehydrate_wait_interests_from_snapshot",
]
