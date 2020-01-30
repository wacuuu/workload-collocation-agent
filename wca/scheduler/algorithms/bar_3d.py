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
                ResourceType.MEMBW_READ: 10000,
                ResourceType.MEMBW_WRITE: 10000
                }
        # TODO: Replace with real data from provider.
        capacity = {
                ResourceType.CPU: 4,
                ResourceType.MEM: 20000,
                ResourceType.MEMBW_READ: 20000,
                ResourceType.MEMBW_WRITE: 20000
        }

        cpu_fraction = fraction_of_capacity(
                requested[ResourceType.CPU], capacity[ResourceType.CPU])
        memory_fraction = fraction_of_capacity(
                requested[ResourceType.MEM], capacity[ResourceType.MEM])

        memory_bandwidth_requested = requested[ResourceType.MEMBW_READ] + 4 * requested[ResourceType.MEMBW_WRITE]
        memory_bandwidth_capacity = capacity[ResourceType.MEMBW_READ] + 4 * capacity[ResourceType.MEMBW_WRITE]

        memory_bandwidth_fraction = fraction_of_capacity(
                memory_bandwidth_requested, memory_bandwidth_capacity)

        mean = cpu_fraction + memory_fraction + memory_bandwidth_fraction / 3
        variance = pow((cpu_fraction-mean), 2) + pow((memory_fraction-mean), 2) + pow((memory_bandwidth_fraction - mean), 2)
        variance = variance / 3


class BARGeneric(FFDGeneric):
    def calculate_node_free_resources(self, capacity, used) -> Resources:
        free = capacity.copy()
        for dimension in self.dimensions:
            if dimension not in (rt.MEMBW_READ, rt.MEMBW_WRITE):
                free[dimension] -= used[dimension]
        free[rt.MEMBW_READ] = capacity[rt.MEMBW_READ] - (used[rt.MEMBW_READ] + used[rt.MEMBW_WRITE] * 4)
        free[rt.MEMBW_WRITE] = capacity[rt.MEMBW_WRITE] - (used[rt.MEMBW_WRITE] + used[rt.READ] / 4)
        return free

    def calculacte_app_requested_fraction(self, requested, free) -> Dict[ResourceType, float]:
        """Flats MEMBW_WRITE and MEMBW_READ to single dimension MEMBW_FLAT"""
        fractions = {}
        for dimension in self.dimensions:
            if dimension not in (rt.MEMBW_READ, rt.MEMBW_WRITE):
                fractions[dimension] = float(requested[dimension]) / float(free[dimension]])
        fractions[rt.MEMBW_FLAT] = (requested[rt.MEMBW_READ] + 4*requested[rt.MEMBW_WRITE]) / (free[rt.MEMBW_READ] + 4*free[rt.MEMBW_WRITE])
        return fractions

    def prioritize(self, extender_args: ExtenderArgs) -> List[HostPriority]:
        nodes = sorted(extender_args.NodeNames)
        log.info('[Prioritize] Nodes: %r' % nodes)

        priorities = []

        dp = self.data_provider
        assigned_tasks = dp.get_assigned_tasks_requested_resources(self.dimensions, nodes)
        node_capacities = dp.get_nodes_capacities(self.dimensions)
        app_requested = dp.get_app_requested_resources(self.dimensions, app)
        
        log.debug('Iterating through nodes.')
        for node in nodes:
            if node not in node_capacities:
                log.warning('Missing Node %r information!' % node)
                extender_filter_result.NodeNames.append(node)
                break

            node_used_resources = self.used_resources_on_node(assigned_tasks[node])
            node_free_resources = calculate_node_free_resources(capacity, used)  # allocable

            app_requested_fraction = calculacte_app_requested_fraction()
            mean = sum([v for v in app_requested_fraction.values()])/len(app_requested_fraction)
            if len(app_requested_fraction) > 2:
                variance = sum([(fraction - mean)*(fraction - mean) for fraction in app_requested_fraction]) / len(app_requested_fraction)
            else:
                variance = abs()
            score = int((1-variance) * self.get_max_node_score())
            priorities.append(HostPriority(node, score))

        return priorities



def fraction_of_capacity(requested: Union[int, float], capacity: Union[int, float]) -> float:
    if capacity == 0:
        return 1.0
    return float(requested) / float(capacity)
