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

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict


class ExperimentType(Enum):
    DRAM = 'dram'
    PMEM = 'pmem'
    HMEM_NUMA_BALANCING = 'hmem_numa_balancing'
    HMEM_NO_NUMA_BALANCING = 'hmem_no_numa_balancig'
    COLD_START = 'cold_start'
    TOPTIER = 'toptier'
    TOPTIER_WITH_COLDSTART = 'toptier_with_coldstart'


@dataclass
class Scenario:
    name: str
    # List of workload counts in every step of the experiment
    # e.g. [{'workload1': 1}, {'workload1': 3}] means that in first loop
    # workload1 will have one instance and three in the second
    workloads_count: List[Dict[str, int]]
    sleep_duration: int
    experiment_type: ExperimentType
    # If for some reason you do not want to scale workloads to 0 replicas
    # after each step set this flag to false
    reset_workloads_between_steps: bool = True


# ----------------- REDIS WORKLOADS --------------------------
#     ----------------- BIG ----------------
REDIS_MEMTIER_BIG_DRAM = 'redis-memtier-big-dram'
REDIS_MEMTIER_BIG_PMEM = 'redis-memtier-big-pmem'
REDIS_MEMTIER_BIG_DRAM_PMEM = 'redis-memtier-big-dram-pmem'
REDIS_MEMTIER_BIG_COLDSTART_TOPTIER = 'redis-memtier-big-coldstart-toptier'
REDIS_MEMTIER_BIG_TOPTIER = 'redis-memtier-big-toptier'
#     --------------- BIG WSS --------------
REDIS_MEMTIER_BIG_WSS_DRAM = 'redis-memtier-big-wss-dram'
REDIS_MEMTIER_BIG_WSS_PMEM = 'redis-memtier-big-wss-pmem'
REDIS_MEMTIER_BIG_WSS_DRAM_PMEM = 'redis-memtier-big-wss-dram-pmem'
REDIS_MEMTIER_BIG_WSS_COLDSTART_TOPTIER = 'redis-memtier-big-wss-coldstart-toptier'
REDIS_MEMTIER_BIG_WSS_TOPTIER = 'redis-memtier-big-wss-toptier'
#     --------------- MEDIUM ---------------
REDIS_MEMTIER_MEDIUM_COLDSTART_TOPTIER = 'redis-memtier-medium-coldstart-toptier'
REDIS_MEMTIER_MEDIUM_DRAM = 'redis-memtier-medium-dram'
REDIS_MEMTIER_MEDIUM_DRAM_PMEM = 'redis-memtier-medium-dram-pmem'
REDIS_MEMTIER_MEDIUM_PMEM = 'redis-memtier-medium-pmem'
REDIS_MEMTIER_MEDIUM_TOPTIER = 'redis-memtier-medium-toptier'
#     ------------- MEDIUM WSS -------------
REDIS_MEMTIER_MEDIUM_WSS_COLDSTART_TOPTIER = 'redis-memtier-medium-wss-coldstart-toptier'
REDIS_MEMTIER_MEDIUM_WSS_DRAM = 'redis-memtier-medium-wss-dram'
REDIS_MEMTIER_MEDIUM_WSS_DRAM_PMEM = 'redis-memtier-medium-wss-dram-pmem'
REDIS_MEMTIER_MEDIUM_WSS_PMEM = 'redis-memtier-medium-wss-pmem'
REDIS_MEMTIER_MEDIUM_WSS_TOPTIER = 'redis-memtier-medium-wss-toptier'
# ----------------- REDIS SCENARIOS --------------------------
SLEEP_DURATION = 900
WORKLOAD_COUNT = 1
REDIS_SCENARIOS = [
    # Dram redis memtier big
    Scenario(name='redis-memtier-big-dram',
             workloads_count=[{REDIS_MEMTIER_BIG_DRAM: 1}, {REDIS_MEMTIER_BIG_DRAM: 2}],
             sleep_duration=SLEEP_DURATION, experiment_type=ExperimentType.DRAM,
             reset_workloads_between_steps=False),
    # Pmem redis memtier big
    Scenario(name='redis-memtier-big-pmem',
             workloads_count=[{REDIS_MEMTIER_BIG_PMEM: 1}, {REDIS_MEMTIER_BIG_PMEM: 2}],
             sleep_duration=SLEEP_DURATION, experiment_type=ExperimentType.PMEM,
             reset_workloads_between_steps=False),
    # First touch policy redis memtier big
    Scenario(name='redis-memtier-big-first-touch-policy',
             workloads_count=[{REDIS_MEMTIER_BIG_DRAM_PMEM: 1}, {REDIS_MEMTIER_BIG_DRAM_PMEM: 2},
                              {REDIS_MEMTIER_BIG_DRAM_PMEM: 3}, {REDIS_MEMTIER_BIG_DRAM_PMEM: 4}],
             sleep_duration=SLEEP_DURATION, experiment_type=ExperimentType.HMEM_NO_NUMA_BALANCING,
             reset_workloads_between_steps=False),
    # Numa balancing redis memtier big
    Scenario(name='redis-memtier-big-numa-balancing',
             workloads_count=[{REDIS_MEMTIER_BIG_DRAM_PMEM: 4}],
             sleep_duration=SLEEP_DURATION, experiment_type=ExperimentType.HMEM_NUMA_BALANCING),
    # Toptier limit redis memtier big
    Scenario(name='redis-memtier-big-toptier-limit',
             workloads_count=[{REDIS_MEMTIER_BIG_TOPTIER: 4}],
             sleep_duration=SLEEP_DURATION, experiment_type=ExperimentType.TOPTIER),
    # Toptier with coldstart redis memtier big
    Scenario(name='redis-memtier-toptier-coldstart',
             workloads_count=[{REDIS_MEMTIER_BIG_COLDSTART_TOPTIER: 4}],
             sleep_duration=SLEEP_DURATION, experiment_type=ExperimentType.TOPTIER_WITH_COLDSTART)
]
