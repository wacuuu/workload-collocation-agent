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
from typing import Tuple

from wca.scheduler.algorithms import \
    BaseAlgorithm, substract_resources, sum_resources, used_free_requested

log = logging.getLogger(__name__)


class Fit(BaseAlgorithm):
    """Filter all nodes where the scheduled app does not fit.
       Supporting any number of dimensions.
       Treats MEMBW_READ and MEMBW_WRITE differently than other dimensions."""

    def app_fit_node(self, node_name, app_name, data_provider_queried) -> Tuple[bool, str]:
        nodes_capacities, assigned_apps_counts, apps_spec = data_provider_queried

        # Current node context: used and free currently
        used, free, requested, capacity, membw_read_write_ratio, metrics = \
            used_free_requested(node_name, app_name, self.dimensions,
                                nodes_capacities, assigned_apps_counts, apps_spec)
        self.metrics.extend(metrics)

        # SUBTRACT: "free" after simulated assigment of requested
        free_after_bind = substract_resources(
            capacity,
            sum_resources(requested, used),
            membw_read_write_ratio)

        # CHECK
        broken_capacities = {r: abs(v) for r, v in free_after_bind.items() if v < 0}

        if not broken_capacities:
            return True, ''
        else:
            broken_capacities_str = \
                ','.join(['({}: {})'.format(r, v) for r, v in broken_capacities.items()])
            # print('broken capacity:', app_name, node_name, broken_capacities_str)
            return False, 'Could not fit node for dimensions: ({}).'.format(broken_capacities_str)

    def priority_for_node(self, node_name: str, app_name: str,
                          data_provider_queried: Tuple) -> float:
        """no prioritization method for FitGeneric"""
        return 0.0

# class FitGenericTesting(FitGeneric):
#     """with some testing cluster specific hacks"""
#
#     def prioritize(self, extender_args: ExtenderArgs) -> List[HostPriority]:
#         nodes = extender_args.NodeNames
#         log.info('[Prioritize] Nodes: %r' % nodes)
#         nodes = sorted(extender_args.NodeNames)
#         return self.testing_prioritize(nodes)
#
#     @staticmethod
#     def testing_prioritize(nodes):
#         priorities = []
#
#         # Trick to not prioritize:
#         # nodeSelector:
#         #   goal: load_generator
#         if nodes[0] == 'node200':
#             return priorities
#
#         if len(nodes) > 0:
#             for node in sorted(nodes):
#                 priorities.append(HostPriority(node, 0))
#             priorities[0].Score = 100
#         return priorities
