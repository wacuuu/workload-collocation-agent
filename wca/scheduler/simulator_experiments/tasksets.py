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

from wca.scheduler.cluster_simulator import Resources
from wca.scheduler.cluster_simulator import Task
from wca.scheduler.types import ResourceType as ResourceType, CPU, MEM, MEMBW, WSS, MEMBW_READ, \
    MEMBW_WRITE

# wca_load_balancing_multidemnsional_2lm_v0.2
TASK_DEFINITIONS__2LM_V02 = [
    Task('memcached_big', Resources({CPU: 2, MEM: 28, MEMBW: 1.3, WSS: 1.7})),
    Task('memcached_medium', Resources({CPU: 2, MEM: 12, MEMBW: 1.0, WSS: 1.0})),
    Task('memcached_small', Resources({CPU: 2, MEM: 2.5, MEMBW: 0.4, WSS: 0.4})),
    # ---
    Task('redis_big', Resources({CPU: 1, MEM: 29, MEMBW: 0.5, WSS: 14})),
    Task('redis_medium', Resources({CPU: 1, MEM: 11, MEMBW: 0.4, WSS: 10})),
    Task('redis_small', Resources({CPU: 1, MEM: 1.5, MEMBW: 0.3, WSS: 1.5})),
    # ---
    Task('stress_stream_big', Resources({CPU: 3, MEM: 13, MEMBW: 18, WSS: 12})),
    Task('stress_stream_medium', Resources({CPU: 1, MEM: 12, MEMBW: 6, WSS: 10})),
    Task('stress_stream_small', Resources({CPU: 1, MEM: 7, MEMBW: 5, WSS: 6})),
    # ---
    Task('sysbench_big', Resources({CPU: 3, MEM: 9, MEMBW: 13, WSS: 7.5})),
    Task('sysbench_medium', Resources({CPU: 2, MEM: 2, MEMBW: 10, WSS: 2})),
    Task('sysbench_small', Resources({CPU: 1, MEM: 1, MEMBW: 8, WSS: 1}))
]

TASK_DEFINITIONS__ARTIFICIAL_3TYPES = [
    # Artificial workloads
    Task('cpu', Resources({CPU: 10, MEM: 50, MEMBW_READ: 2, MEMBW_WRITE: 1, WSS: 1})),
    Task('mem', Resources({CPU: 1, MEM: 100, MEMBW_READ: 1, MEMBW_WRITE: 0, WSS: 1})),
    Task('mbw', Resources({CPU: 1, MEM: 1, MEMBW_READ: 10, MEMBW_WRITE: 5, WSS: 1})),
]

TASK_DEFINITIONS__ARTIFICIAL_2DIM_2TYPES = [
    Task('cputask', Resources({CPU: 20, MEM: 40, MEMBW_READ: 0, MEMBW_WRITE: 0, WSS: 0})),
    Task('memtask', Resources({CPU: 10, MEM: 200, MEMBW_READ: 0, MEMBW_WRITE: 0, WSS: 0})),
]

TASK_DEFINITIONS__ARTIFICIAL_2 = [
    # Artificial workloads
    Task('cpu', Resources({CPU: 10, MEM: 50, MEMBW_READ: 2, MEMBW_WRITE: 1, WSS: 1})),
    Task('cpu2', Resources({CPU: 5, MEM: 25, MEMBW_READ: 2, MEMBW_WRITE: 0, WSS: 1})),
    Task('mem', Resources({CPU: 1, MEM: 25, MEMBW_READ: 1, MEMBW_WRITE: 0, WSS: 1})),
    Task('mem2', Resources({CPU: 1, MEM: 20, MEMBW_READ: 1, MEMBW_WRITE: 1, WSS: 1})),
    Task('mbw', Resources({CPU: 1, MEM: 1, MEMBW_READ: 10, MEMBW_WRITE: 5, WSS: 1})),
    Task('mbw2', Resources({CPU: 1, MEM: 1, MEMBW_READ: 7, MEMBW_WRITE: 1, WSS: 1})),
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
