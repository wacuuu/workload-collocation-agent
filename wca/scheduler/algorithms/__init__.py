# Copyright (c) 2019 Intel Corporation
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

from abc import ABC, abstractmethod
from typing import List, Tuple

from wca.metrics import Metric
from wca.scheduler.types import ExtenderArgs, ExtenderFilterResult, HostPriority


class Algorithm(ABC):

    @abstractmethod
    def filter(self, extender_args: ExtenderArgs) -> Tuple[
            ExtenderFilterResult, List[Metric]]:
        pass

    @abstractmethod
    def prioritize(self, extender_args: ExtenderArgs) -> Tuple[
            List[HostPriority], List[Metric]]:
        pass


class BaseAlgorithm(ABC):
    data_provider: DataProvider
    dimensions: Tuple[rt] = (rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE)

    def filter(self, extender_args: ExtenderArgs) -> ExtenderFilterResult:
        log.debug('[Filter] ExtenderArgs: %r' % extender_args)
        app, nodes, namespace, name = extract_common_input(extender_args)
        extender_filter_result = ExtenderFilterResult()

        dp = self.data_provider
        tasks = dp.get_apps(self.dimensions, nodes)
        nodes_capacities = dp.get_nodes_capacities(self.dimensions)
        app_requested = dp.get_app_requested_resources(self.dimensions, app)

        log.debug('Iterating through nodes.')
        for node_name in nodes:
            if node_name not in nodes_capacities:
                log.warning('Missing Node %r information!' % node_name)
                extender_filter_result.NodeNames.append(node_name)
                break

            passed, message = self.app_fit_node(node_name, app_requested, tasks, nodes_capacities)
            if not passed:
                extender_filter_result.FailedNodes[node_name] = message
            else:
                extender_filter_result.NodeNames.append(node_name)

        log.debug('Results: {}'.format(extender_filter_result))
        return extender_filter_result

    def prioritize(self, extender_args: ExtenderArgs) -> List[HostPriority]:
        log.info('[Prioritize] Nodes: %r' % nodes)
        nodes = extender_args.NodeNames
        priorities = []
        for node in nodes:
            priorities.append(HostPriority(node, self.calculate_priority_for_node(node)))
        return priorities

    @abstractmethod
    def app_fit_node(node_name, app_requested, tasks, capacities) -> bool:
        pass

    @abstractmethod
    def priority_for_node(node_name, app_requested, tasks, capacities) -> int:
        pass


def used_resources_on_node(self, dimensions: Iterable[rt], tasks: Dict[TaskName, Resources]) -> Resources:
    used = {resource: 0 for resource in dimensions}
    for task, task_resources in tasks.items():
        for resource in self.dimensions:
            used[resource] += task_resources[resource]
    return used


def free_resources_on_node(dimensions: Iterable[rt], capacity: Resources, used: Resources) -> Resources:
    free = capacity.copy()
    for dimension in self.dimensions:
        if dimension not in (rt.MEMBW_READ, rt.MEMBW_WRITE):
            free[dimension] -= used[dimension]
    free[rt.MEMBW_READ] = capacity[rt.MEMBW_READ] - (used[rt.MEMBW_READ] + used[rt.MEMBW_WRITE] * 4)
    free[rt.MEMBW_WRITE] = capacity[rt.MEMBW_WRITE] - (used[rt.MEMBW_WRITE] + used[rt.READ] / 4)
    return free
