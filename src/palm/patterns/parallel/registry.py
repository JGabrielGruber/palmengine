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
from palm.patterns.parallel.app import parallel_app
from palm.patterns.parallel.bindings.definitions.builder import build
from palm.patterns.parallel.bindings.instances.persistence import (
    extract_instance_fields_from_job,
    prepare_parallel_resume_state,
)
from palm.patterns.parallel.bindings.instances.submission import parallel_submission_metadata
from palm.patterns.parallel.pattern import ParallelPattern

pattern_registry.register("parallel", ParallelPattern)
register_builder("parallel", build)
register_instance_sync(
    "parallel",
    fields=extract_instance_fields_from_job,
    resume=prepare_parallel_resume_state,
)
register_submission_metadata("parallel", parallel_submission_metadata)
parallel_app.register()
