
================================
Available metrics
================================

**This software is pre-production and should not be deployed to production servers.**

.. contents:: Table of Contents

.. csv-table::
	:header: "Name", "Help", "Unit", "Type", "Source"
	:widths: 10, 20, 10, 10

	"instructions", "Linux Perf counter for instructions per container.", "numeric", "counter", "perf event"
	"cycles", "Linux Perf counter for cycles per container.", "numeric", "counter", "perf event"
	"cache_misses", "Linux Perf counter for cache-misses per container.", "numeric", "counter", "perf event"
	"cpu_usage_per_cpu", "Logical CPU usage in 1/USER_HZ (usually 10ms).Calculated using values based on /proc/stat", "ms", "counter", "/proc"
	"cpu_usage_per_task", "cpuacct.usage (total kernel and user space)", "numeric", "counter", "cgroup"
	"memory_bandwidth", "Total memory bandwidth using Memory Bandwidth Monitoring.", "bytes", "counter", "resctrl"
	"memory_usage_per_task_bytes", "Memory usage_in_bytes per tasks returned from cgroup memory subsystem.", "bytes", "gauge", "cgroup"
	"memory_max_usage_per_task_bytes", "Memory max_usage_in_bytes per tasks returned from cgroup memory subsystem.", "bytes", "gauge", "cgroup"
	"memory_limit_per_task_bytes", "Memory limit_in_bytes per tasks returned from cgroup memory subsystem.", "bytes", "gauge", "cgroup"
	"memory_soft_limit_per_task_bytes", "Memory soft_limit_in_bytes per tasks returned from cgroup memory subsystem.", "bytes", "gauge", "cgroup"
	"llc_occupancy", "LLC occupancy", "bytes", "gauge", "resctrl"
	"memory_usage", "Total memory used by platform in bytes based on /proc/meminfo and uses heuristic based on linux free tool (total - free - buffers - cache).", "bytes", "gauge", "/proc"
	"stalls_mem_load", "Mem stalled loads", "numeric", "counter", "perf event"
	"cache_references", "Cache references", "numeric", "counter", "perf event"
	"scaling_factor_max", "Perf metric scaling factor, MAX value", "numeric", "gauge", "perf event"
	"scaling_factor_avg", "Perf metric scaling factor, average from all CPUs", "numeric", "gauge", "perf event"
	"memory_numa_stat", "NUMA Stat TODO!", "numeric", "gauge", "cgroup"
	"memory_numa_free", "NUMA memory free per numa node TODO!", "numeric", "gauge", "/proc"
	"memory_numa_used", "NUMA memory used per numa node TODO!", "numeric", "gauge", "/proc"
	"memory_bandwidth_local", "Total local memory bandwidth using Memory Bandwidth Monitoring.", "bytes", "counter", "resctrl"
	"memory_bandwidth_remote", "Total remote memory bandwidth using Memory Bandwidth Monitoring.", "bytes", "counter", "resctrl"
	"offcore_requests_l3_miss_demand_data_rd", "Increment each cycle of the number of offcore outstanding demand data read requests from SQ that missed L3.", "numeric", "counter", "perf event"
	"offcore_requests_outstanding_l3_miss_demand_data_rd", "Demand data read requests that missed L3.", "numeric", "counter", "perf event"
	"cpus", "Tasks resources cpus initial requests.", "numeric", "gauge", "generic"
	"mem", "Tasks resources memory initial requests.", "numeric", "gauge", "generic"
	"last_seen", "Time the task was last seen.", "numeric", "counter", "generic"
	"up", "Time the was was last seen.", "numeric", "counter", "internal"
	"ipc", "Instructions per cycle", "numeric", "gauge", "perf event"
	"ips", "Instructions per second", "numeric", "gauge", "perf event"
	"cache_hit_ratio", "Cache hit ratio, based on cache-misses and cache-references", "numeric", "gauge", "perf event"
	"cache_misses_per_kilo_instructions", "Cache misses per kilo instructions", "numeric", "gauge", "perf event"