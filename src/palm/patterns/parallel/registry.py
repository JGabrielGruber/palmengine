"""
Parallel pattern registry wiring.
"""

from __future__ import annotations

from palm.core.registry import pattern_registry
from palm.patterns._registry import (
    register_builder,
    register_instance_sync,
    register_submission_metadata,
)
from palm.patterns.parallel.builder import build
from palm.patterns.parallel.pattern import ParallelPattern
from palm.patterns.parallel.persistence import (
    extract_instance_fields_from_job,
    prepare_parallel_resume_state,
)
from palm.patterns.parallel.submission import parallel_submission_metadata

pattern_registry.register("parallel", ParallelPattern)
register_builder("parallel", build)
register_instance_sync(
    "parallel",
    fields=extract_instance_fields_from_job,
    resume=prepare_parallel_resume_state,
)
register_submission_metadata("parallel", parallel_submission_metadata)
