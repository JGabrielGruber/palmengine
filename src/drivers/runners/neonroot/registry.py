"""Register neonroot WorkloadRuntime class."""

from palm.core.workload.registry import workload_runtime_registry
from drivers.runners.neonroot.runtime import NeonrootWorkloadRuntime

workload_runtime_registry.register("neonroot", NeonrootWorkloadRuntime)
