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
class FitGeneric(BaseAlgorithm):
    """Filter all nodes where the scheduled app does not fit.
       Supporting any number of dimensions.
       Treats MEMBW_READ and MEMBW_WRITE differently than other dimensions."""

    def app_fit_node(self, node_name: str, requested: Resources, used: Resources,
                     capacity: Resources) -> Tuple[bool, str]:
        """requested - requested by app; free - free on the node"""
        broken_capacities = set([r for r in self.dimensions
                                 if not requested[r] < capacity[r] - used[r]])
        if not membw_check(requested, used, capacity,
                           self.data_provider.get_node_membw_read_write_ratio(node_name)):
            broken_capacities.update((rt.MEMBW_READ, rt.MEMBW_READ,))
        broken_capacities_str = ','.join([str(e) for e in broken_capacities])

        if not broken_capacities:
            return True, ''
        else:
            return False, 'Could not fit node for dimensions: ({}).'.format(broken_capacities_str)

    def filter(self, extender_args: ExtenderArgs) -> ExtenderFilterResult:
        log.debug('ExtenderArgs: %r' % extender_args)
        app, nodes, namespace, name = extract_common_input(extender_args)
        extender_filter_result = ExtenderFilterResult()

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

            node_used_resources = used_resources_on_node(self.dimensions, assigned_tasks[node])
            passed, message = self.app_fit_node(node, app_requested_resources,
                                                node_used_resources, node_capacities[node])
            if not passed:
                extender_filter_result.FailedNodes[node] = message
            else:
                extender_filter_result.NodeNames.append(node)

        log.debug('Results: {}'.format(extender_filter_result))
        return extender_filter_result

    def prioritize(self, extender_args: ExtenderArgs) -> List[HostPriority]:
        log.info('[Prioritize] Nodes: %r' % nodes)
        nodes = sorted(extender_args.NodeNames)

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
