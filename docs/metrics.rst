
================================
Available metrics
================================

**This software is pre-production and should not be deployed to production servers.**

.. contents:: Table of Contents

=================================================== ======= ======= ===========================================================================================================================================
instructions                                        counter numeric Linux Perf counter for instructions per container.                                                                                         
cycles                                              counter numeric Linux Perf counter for cycles per container.                                                                                               
cache_misses                                        counter numeric Linux Perf counter for cache-misses per container.                                                                                         
cpu_usage_per_cpu                                   counter ms      Logical CPU usage in 1/USER_HZ (usually 10ms).Calculated using values based on /proc/stat                                                  
cpu_usage_per_task                                  counter numeric [ns] cpuacct.usage (total kernel and user space)                                                                                           
memory_bandwidth                                    counter bytes   Total memory bandwidth using Memory Bandwidth Monitoring.                                                                                  
memory_usage_per_task_bytes                         gauge   bytes   Memory usage_in_bytes per tasks returned from cgroup memory subsystem.                                                                     
memory_max_usage_per_task_bytes                     gauge   bytes   Memory max_usage_in_bytes per tasks returned from cgroup memory subsystem.                                                                 
memory_limit_per_task_bytes                         gauge   bytes   Memory limit_in_bytes per tasks returned from cgroup memory subsystem.                                                                     
memory_soft_limit_per_task_bytes                    gauge   bytes   Memory soft_limit_in_bytes per tasks returned from cgroup memory subsystem.                                                                
llc_occupancy                                       gauge   bytes   LLC occupancy                                                                                                                              
memory_usage                                        gauge   bytes   Total memory used by platform in bytes based on /proc/meminfo and uses heuristic based on linux free tool (total - free - buffers - cache).
stalls_mem_load                                     counter numeric Mem stalled loads                                                                                                                          
cache_references                                    counter numeric Cache references                                                                                                                           
scaling_factor_max                                  gauge   numeric Perf metric scaling factor, MAX value                                                                                                      
scaling_factor_avg                                  gauge   numeric Perf metric scaling factor, average from all CPUs                                                                                          
memory_numa_stat                                    gauge   numeric NUMA Stat TODO!                                                                                                                            
memory_numa_free                                    gauge   numeric NUMA memory free per numa node TODO!                                                                                                       
memory_numa_used                                    gauge   numeric NUMA memory used per numa node TODO!                                                                                                       
memory_bandwidth_local                              counter bytes   Total local memory bandwidth using Memory Bandwidth Monitoring.                                                                            
memory_bandwidth_remote                             counter bytes   Total remote memory bandwidth using Memory Bandwidth Monitoring.                                                                           
offcore_requests_l3_miss_demand_data_rd             counter numeric Increment each cycle of the number of offcore outstanding demand data read requests from SQ that missed L3.                                
offcore_requests_outstanding_l3_miss_demand_data_rd counter numeric Demand data read requests that missed L3.                                                                                                  
cpus                                                gauge   numeric Tasks resources cpus initial requests.                                                                                                     
mem                                                 gauge   numeric Tasks resources memory initial requests.                                                                                                   
last_seen                                           counter numeric Time the task was last seen.                                                                                                               
up                                                  counter numeric Time the was was last seen.                                                                                                                
ipc                                                 gauge   numeric Instructions per cycle                                                                                                                     
ips                                                 gauge   numeric Instructions per second                                                                                                                    
cache_hit_ratio                                     gauge   numeric Cache hit ratio, based on cache-misses and cache-references                                                                                
cache_misses_per_kilo_instructions                  gauge   numeric Cache misses per kilo instructions                                                                                                         
=================================================== ======= ======= ===========================================================================================================================================
