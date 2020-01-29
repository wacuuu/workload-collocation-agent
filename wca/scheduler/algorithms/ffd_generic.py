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

import logging
from typing import List, Tuple, Dict

from dataclasses import dataclass

from wca.scheduler.algorithms import Algorithm
from wca.scheduler.data_providers import DataProvider
from wca.scheduler.types import (ExtenderArgs, ExtenderFilterResult,
                                 HostPriority, Resources, TaskName)
from wca.scheduler.types import ResourceType as rt
from wca.scheduler.utils import extract_common_input

log = logging.getLogger(__name__)


@dataclass
class FFDGeneric(Algorithm):
    """Fit first decreasing; supports as many dimensions as needed."""

    data_provider: DataProvider
    dimensions: Tuple[rt] = (rt.CPU, rt.MEM,
                             rt.MEMBW_READ, rt.MEMBW_WRITE)

    def app_fit_node(self, node_name: str, requested: Resources,
                     used: Resources, capacity: Resources) -> Tuple[bool, str]:
        """requested - requested by app; free - free on the node"""
        broken_capacities = [r for r in self.dimensions if not requested[r] < capacity[r] - used[r]]
        if not broken_capacities:
            return True, ''
        else:
            broken_capacities_str = ','.join([str(e) for e in broken_capacities])
            return False, 'Could not fit node for dimensions: ({}).'.format(broken_capacities_str)

    def used_resources_on_node(self, tasks: Dict[TaskName, Resources]) -> Resources:
        used = {resource: 0 for resource in self.dimensions}
        for task, task_resources in tasks.items():
            for resource in self.dimensions:
                used[resource] += task_resources[resource]
        return used

    def filter(self, extender_args: ExtenderArgs) -> ExtenderFilterResult:
        app, nodes, namespace, name = extract_common_input(extender_args)
        extender_filter_result = ExtenderFilterResult()

        log.debug('Getting app requested and node free resources.')
        log.debug('ExtenderArgs: %r' % extender_args)

        dp = self.data_provider
        assigned_tasks = dp.get_assigned_tasks_requested_resources(self.dimensions, nodes)
        node_capacities = dp.get_nodes_capacities(self.dimensions)
        app_requested_resources = dp.get_app_requested_resources(self.dimensions, app)

        log.debug('Iterating through nodes.')
        for node in nodes:
            if node not in node_capacities:
                log.warning('Missing Node %r information!' % node)
                extender_filter_result.NodeNames.append(node)
                break

            node_used_resources = self.used_resources_on_node(assigned_tasks[node])
            passed, message = self.app_fit_node(node, app_requested_resources,
                                                node_used_resources, node_capacities[node])
            if not passed:
                extender_filter_result.FailedNodes[node] = message
            else:
                extender_filter_result.NodeNames.append(node)

        log.debug('Results: {}'.format(extender_filter_result))
        return extender_filter_result

    def prioritize(self, extender_args: ExtenderArgs) -> List[HostPriority]:
        nodes = sorted(extender_args.NodeNames)
        log.info('[Prioritize] Nodes: %r' % nodes)

        priorities = []

        # Trick to not prioritize:
        # nodeSelector:
        #   goal: load_generator
        if nodes[0] == 'node200':
            return priorities

        if len(nodes) > 0:
            for node in nodes:
                priorities.append(HostPriority(node, 0))
            priorities[0].Score = 100

        return priorities


@dataclass
class FFDAsymmetricMembw(FFDGeneric):
    """Supports asymmetric membw speed for write/read"""

    @staticmethod
    def membw_check(requested: Resources, used: Resources, capacity: Resources,
                    node_membw_read_write_ratio: float) -> bool:
        """
        read/write ratio, e.g. 40GB/s / 10GB/s = 4,
        what means reading is 4 time faster
        """

        # Assert that required dimensions are available.
        for resource in (rt.MEMBW_WRITE, rt.MEMBW_READ,):
            for source in (requested, used):
                assert resource in source

        # To shorten the notation.
        WRITE = rt.MEMBW_WRITE
        READ = rt.MEMBW_READ
        R = node_membw_read_write_ratio

        return used[READ] + R * used[WRITE] < capacity[READ]

    def app_fit_node(self, node_name: str, requested: Resources, used: Resources,
                     capacity: Resources) -> Tuple[bool, str]:
        """requested - requested by app; free - free on the node"""
        broken_capacities = set([r for r in self.dimensions
                                 if not requested[r] < capacity[r] - used[r]])
        if not self.membw_check(requested, used, capacity,
                                self.data_provider.get_node_membw_read_write_ratio(node_name)):
            broken_capacities.update((rt.MEMBW_READ, rt.MEMBW_READ,))
        broken_capacities_str = ','.join([str(e) for e in broken_capacities])

        if not broken_capacities:
            return True, ''
        else:
            return False, 'Could not fit node for dimensions: ({}).'.format(broken_capacities_str)
