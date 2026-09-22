"""Register host WorkloadRuntime class."""

from palm.core.workload.registry import workload_runtime_registry
from plugins.runners.host.runtime import HostWorkloadRuntime

workload_runtime_registry.register("host", HostWorkloadRuntime)
