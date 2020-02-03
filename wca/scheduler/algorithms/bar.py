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
from typing import Tuple, Dict, Any

from wca.scheduler.algorithms import used_resources_on_node, free_resources_on_node
from wca.scheduler.algorithms.fit import FitGeneric
from wca.scheduler.types import ResourceType as rt

log = logging.getLogger(__name__)


class BARGeneric(FitGeneric):
    def app_requested_fraction(self, requested, free) -> Dict[rt, float]:
        """Flats MEMBW_WRITE and MEMBW_READ to single dimension MEMBW_FLAT"""
        fractions = {}
        for dimension in self.dimensions:
            if dimension not in (rt.MEMBW_READ, rt.MEMBW_WRITE):
                fractions[dimension] = float(requested[dimension]) / float(free[dimension])
        if rt.MEMBW_READ in self.dimensions:
            assert rt.MEMBW_WRITE in self.dimensions
            fractions[rt.MEMBW_FLAT] = (requested[rt.MEMBW_READ] + 4*requested[rt.MEMBW_WRITE]) \
                / (free[rt.MEMBW_READ] + 4*free[rt.MEMBW_WRITE])
        return fractions

    def priority_for_node(self, node_name: str, app_name: str,
                          data_provider_queried: Tuple[Any]) -> int:
        nodes_capacities, assigned_apps_counts, apps_spec = data_provider_queried

        used, free, requested = used_free_requested(node_name, app_name, self.dimensions,
                                                    *data_provider_queried)

        app_requested_fraction = self.app_requested_fraction(requested, free)
        mean = sum([v for v in app_requested_fraction.values()])/len(app_requested_fraction)
        if len(app_requested_fraction) > 2:
            variance = sum([(fraction - mean)*(fraction - mean)
                            for fraction in app_requested_fraction.values()]) \
                       / len(app_requested_fraction)
        elif len(app_requested_fraction) == 1:
            variance = abs(app_requested_fraction[0] - app_requested_fraction[1])
        else:
            variance = 0
        score = int((1-variance) * self.get_max_node_score())
        return score

    def get_max_node_score(self):
        # @TODO should be defined as parameter
        return 10


def used_free_requested(
        node_name, app_name, dimensions,
        nodes_capacities, assigned_apps_counts, apps_spec):
    used = used_resources_on_node(dimensions, assigned_apps_counts[node_name], apps_spec)
    free = free_resources_on_node(dimensions, nodes_capacities[node_name], used)  # allocable
    requested = apps_spec[app_name]
    return used, free, requested
