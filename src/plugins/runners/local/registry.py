"""Register local WorkloadRuntime."""

from palm.core.workload.registry import workload_runtime_registry
from plugins.runners.local.runtime import LocalWorkloadRuntime

workload_runtime_registry.register("local", LocalWorkloadRuntime)
