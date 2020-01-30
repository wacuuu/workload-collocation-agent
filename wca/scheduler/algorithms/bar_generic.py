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
from typing import Dict, List, Any, Callable

from wca.metrics import Metric
from wca.scheduler.algorithms import Algorithm
from wca.scheduler.algorithms.ffd_generic import FFDAsymmetricMembw
from wca.scheduler.types import ExtenderArgs, ExtenderFilterResult, HostPriority, ResourceType, Resources


class BARGeneric(FFDAsymmetricMembw):
    def app_requested_fraction(self, requested, free) -> Dict[ResourceType, float]:
        """Flats MEMBW_WRITE and MEMBW_READ to single dimension MEMBW_FLAT"""
        fractions = {}
        for dimension in self.dimensions:
            if dimension not in (rt.MEMBW_READ, rt.MEMBW_WRITE):
                fractions[dimension] = float(requested[dimension]) / float(free[dimension])
        fractions[rt.MEMBW_FLAT] = (requested[rt.MEMBW_READ] + 4*requested[rt.MEMBW_WRITE]) \
                                   / (free[rt.MEMBW_READ] + 4*free[rt.MEMBW_WRITE])
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

            priorities.append(Host)

            node_used_resources = used_resources_on_node(self.dimenions, assigned_tasks[node])
            node_free_resources = free_resources_on_node(self.dimenions, capacity, used)  # allocable

            app_requested_fraction = self.app_requested_fraction()
            mean = sum([v for v in app_requested_fraction.values()])/len(app_requested_fraction)
            if len(app_requested_fraction) > 2:
                variance = sum([(fraction - mean)*(fraction - mean)for fraction in app_requested_fraction]) / len(app_requested_fraction)
            else:
                variance = abs()
            score = int((1-variance) * self.get_max_node_score())
            priorities.append(HostPriority(node, score))

        return priorities
