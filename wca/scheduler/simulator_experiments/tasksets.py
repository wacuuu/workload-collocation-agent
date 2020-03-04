# Copyright (c) 2020 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Set
from wca.scheduler.cluster_simulator import Task
from wca.scheduler.types import ResourceType as ResourceType
from wca.scheduler.cluster_simulator import Resources


# wca_load_balancing_multidemnsional_2lm_v0.2
TASK_DEFINITIONS__2LM_V02 = [
    Task(name='memcached_big',
         requested=Resources({ResourceType.CPU: 2, ResourceType.MEM: 28,
                              ResourceType.MEMBW: 1.3, ResourceType.WSS: 1.7})),
    Task(name='memcached_medium',
         requested=Resources({ResourceType.CPU: 2, ResourceType.MEM: 12,
                              ResourceType.MEMBW: 1.0, ResourceType.WSS: 1.0})),
    Task(name='memcached_small',
         requested=Resources({ResourceType.CPU: 2, ResourceType.MEM: 2.5,
                              ResourceType.MEMBW: 0.4, ResourceType.WSS: 0.4})),
    # ---
    Task(name='redis_big',
         requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 29,
                              ResourceType.MEMBW: 0.5, ResourceType.WSS: 14})),
    Task(name='redis_medium',
         requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 11,
                              ResourceType.MEMBW: 0.4, ResourceType.WSS: 10})),
    Task(name='redis_small',
         requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 1.5,
                              ResourceType.MEMBW: 0.3, ResourceType.WSS: 1.5})),
    # ---
    Task(name='stress_stream_big',
         requested=Resources({ResourceType.CPU: 3, ResourceType.MEM: 13,
                              ResourceType.MEMBW: 18, ResourceType.WSS: 12})),
    Task(name='stress_stream_medium',
         requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 12,
                              ResourceType.MEMBW: 6, ResourceType.WSS: 10})),
    Task(name='stress_stream_small',
         requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 7,
                              ResourceType.MEMBW: 5, ResourceType.WSS: 6})),
    # ---
    Task(name='sysbench_big',
         requested=Resources({ResourceType.CPU: 3, ResourceType.MEM: 9,
                              ResourceType.MEMBW: 13, ResourceType.WSS: 7.5})),
    Task(name='sysbench_medium',
         requested=Resources({ResourceType.CPU: 2, ResourceType.MEM: 2,
                              ResourceType.MEMBW: 10, ResourceType.WSS: 2})),
    Task(name='sysbench_small',
         requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 1,
                              ResourceType.MEMBW: 8, ResourceType.WSS: 1}))
]

TASK_DEFINITIONS__ARTIFICIAL_3TYPES = [
    # Artificial workloads
    Task(name='cpu', requested=Resources({ResourceType.CPU: 10, ResourceType.MEM: 50, ResourceType.MEMBW_READ: 2, ResourceType.MEMBW_WRITE: 1, ResourceType.WSS: 1})),
    Task(name='mem', requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 100, ResourceType.MEMBW_READ: 1, ResourceType.MEMBW_WRITE: 0, ResourceType.WSS: 1})),
    Task(name='mbw', requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 1,   ResourceType.MEMBW_READ: 10, ResourceType.MEMBW_WRITE: 5, ResourceType.WSS: 1})),
]

TASK_DEFINITIONS__ARTIFICIAL_2DIM_2TYPES = [
    Task(name='cputask', requested=Resources(
        {ResourceType.CPU: 20, ResourceType.MEM: 40, ResourceType.MEMBW_READ: 0, ResourceType.MEMBW_WRITE: 0, ResourceType.WSS: 0})),
    Task(name='memtask', requested=Resources(
        {ResourceType.CPU: 10, ResourceType.MEM: 200, ResourceType.MEMBW_READ: 0, ResourceType.MEMBW_WRITE: 0, ResourceType.WSS: 0})),
]

TASK_DEFINITIONS__ARTIFICIAL_2 = [
    # Artificial workloads
    Task(name='cpu', requested=Resources({ResourceType.CPU: 10, ResourceType.MEM: 50, ResourceType.MEMBW_READ: 2, ResourceType.MEMBW_WRITE:1, ResourceType.WSS: 1})),
    Task(name='cpu2', requested=Resources({ResourceType.CPU: 5, ResourceType.MEM: 25, ResourceType.MEMBW_READ: 2, ResourceType.MEMBW_WRITE:0, ResourceType.WSS: 1})),
    Task(name='mem', requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 25, ResourceType.MEMBW_READ: 1, ResourceType.MEMBW_WRITE:0, ResourceType.WSS: 1})),
    Task(name='mem2', requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 20, ResourceType.MEMBW_READ: 1, ResourceType.MEMBW_WRITE:1, ResourceType.WSS: 1})),
    Task(name='mbw', requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 1, ResourceType.MEMBW_READ: 10, ResourceType.MEMBW_WRITE:5, ResourceType.WSS: 1})),
    Task(name='mbw2', requested=Resources({ResourceType.CPU: 1, ResourceType.MEM: 1, ResourceType.MEMBW_READ: 7, ResourceType.MEMBW_WRITE:1, ResourceType.WSS: 1})),
]


def taskset_dimensions(dimensions: Set[ResourceType], taskset):
    new_taskset = []
    dimensions_to_remove = set(taskset[0].requested.data.keys()).difference(dimensions)
    for task in taskset:
        task_copy = task.copy()
        for dim in dimensions_to_remove:
            task_copy.remove_dimension(dim)
        new_taskset.append(task_copy)
    return new_taskset
