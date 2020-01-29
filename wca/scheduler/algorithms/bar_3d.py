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
from typing import List, Tuple, Union

from wca.metrics import Metric
from wca.scheduler.algorithms import Algorithm
from wca.scheduler.types import ExtenderArgs, ExtenderFilterResult, HostPriority, ResourceType


class Bar3D(Algorithm):
    """Extended Balanced resource allocation algorithm from k8s priorities
    with memory bandwidth.
    https://github.com/kubernetes/kubernetes/blob/18cc21ed68f8fa4be75a8410c354a56c496b2dc7/pkg/scheduler/algorithm/priorities/balanced_resource_allocation.go#L42
    """
    def filter(self, extender_args: ExtenderArgs) -> Tuple[
            ExtenderFilterResult, List[Metric]]:
        # TODO: Use filter from First Fit Decreasing algorithm.
        pass

    def prioritize(self, extender_args: ExtenderArgs) -> Tuple[
            List[HostPriority], List[Metric]]:

        # TODO: Replace with real data from provider.
        requested = {
                ResourceType.CPU: 2,
                ResourceType.MEM: 10000,
                ResourceType.MEMORY_BANDWIDTH_READS: 10000,
                ResourceType.MEMORY_BANDWIDTH_WRITES: 10000
                }

        # TODO: Replace with real data from provider.
        capacity = {
                ResourceType.CPU: 4,
                ResourceType.MEM: 20000,
                ResourceType.MEMORY_BANDWIDTH_READS: 20000,
                ResourceType.MEMORY_BANDWIDTH_WRITES: 20000
        }

        cpu_fraction = fraction_of_capacity(
                requested[ResourceType.CPU], capacity[ResourceType.CPU])
        memory_fraction = fraction_of_capacity(
                requested[ResourceType.MEM], capacity[ResourceType.MEM])

        # TODO: Check if it's correct.
        memory_bandwidth_requested = requested[ResourceType.MEMORY_BANDWIDTH_READS] + requested[ResourceType.MEMORY_BANDWIDTH_WRITES]

        memory_bandwidth_capacity = capacity[ResourceType.MEMORY_BANDWIDTH_READS] + capacity[ResourceType.MEMORY_BANDWIDTH_WRITES]

        memory_bandwidth_fraction = fraction_of_capacity(
                memory_bandwidth_requested, memory_bandwidth_capacity)

        mean = cpu_fraction + memory_fraction + memory_bandwidth_fraction / 3
        variance = ((cpu_fraction - mean) * (cpu_fraction - mean)) + ((memory_fraction - mean) * (memory_fraction - mean)) + ((memory_bandwidth_fraction - mean) 

        variance = pow((cpu_fraction-mean), 2) + pow((memory_fraction-mean), 2) + pow((memory_bandwidth_fraction - mean), 2)
        variance = variance / 3




def fraction_of_capacity(requested: Union[int, float], capacity: Union[int, float]) -> float:
    if capacity == 0:
        return 1.0
    return float(requested) / float(capacity)
