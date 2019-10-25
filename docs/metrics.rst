
================================
Available metrics
================================

**This software is pre-production and should not be deployed to production servers.**

.. contents:: Table of Contents

.. csv-table:: Metrics
   :header: "Name", "Help", "Unit", "Type"
   :widths: 15, 30, 10, 10

   instructions, Linux Perf counter for instructions per container., numeric, counter
   cycles, Linux Perf counter for cycles per container., numeric, counter
   cache_misses, Linux Perf counter for cache-misses per container., numeric, counter
   cpu_usage_per_cpu, Logical CPU usage in 1/USER_HZ (usually 10ms).Calculated using values based on /proc/stat, ms, counter
   cpu_usage_per_task, [ns] cpuacct.usage (total kernel and user space), numeric, counter
   memory_bandwidth, Total memory bandwidth using Memory Bandwidth Monitoring., bytes, counter
   memory_usage_per_task_bytes, Memory usage_in_bytes per tasks returned from cgroup memory subsystem., bytes, gauge
   memory_max_usage_per_task_bytes, Memory max_usage_in_bytes per tasks returned from cgroup memory subsystem., bytes, gauge
   memory_limit_per_task_bytes, Memory limit_in_bytes per tasks returned from cgroup memory subsystem., bytes, gauge
   memory_soft_limit_per_task_bytes, Memory soft_limit_in_bytes per tasks returned from cgroup memory subsystem., bytes, gauge
   llc_occupancy, LLC occupancy, bytes, gauge
   memory_usage, Total memory used by platform in bytes based on /proc/meminfo and uses heuristic based on linux free tool (total - free - buffers - cache)., bytes, gauge
   stalls_mem_load, Mem stalled loads, numeric, counter
   cache_references, Cache references, numeric, counter
   scaling_factor_max, Perf metric scaling factor, MAX value, numeric, gauge
   scaling_factor_avg, Perf metric scaling factor, average from all CPUs, numeric, gauge
   memory_numa_stat, NUMA Stat TODO!, numeric, gauge
   memory_numa_free, NUMA memory free per numa node TODO!, numeric, gauge
   memory_numa_used, NUMA memory used per numa node TODO!, numeric, gauge
   memory_bandwidth_local, Total local memory bandwidth using Memory Bandwidth Monitoring., bytes, counter
   memory_bandwidth_remote, Total remote memory bandwidth using Memory Bandwidth Monitoring., bytes, counter
   offcore_requests_l3_miss_demand_data_rd, Increment each cycle of the number of offcore outstanding demand data read requests from SQ that missed L3., numeric, counter
   offcore_requests_outstanding_l3_miss_demand_data_rd, Demand data read requests that missed L3., numeric, counter
   cpus, Tasks resources cpus initial requests., numeric, gauge
   mem, Tasks resources memory initial requests., numeric, gauge
   last_seen, Time the task was last seen., numeric, counter
   up, Time the was was last seen., numeric, counter
   ipc, Instructions per cycle, numeric, gauge
   ips, Instructions per second, numeric, gauge
   cache_hit_ratio, Cache hit ratio, based on cache-misses and cache-references, numeric, gauge
   cache_misses_per_kilo_instructions, Cache misses per kilo instructions, numeric, gauge