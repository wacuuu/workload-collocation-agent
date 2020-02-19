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
from typing import Tuple, Dict, Any, Iterable

from wca.metrics import Metric, MetricType
from wca.logger import TRACE

from wca.scheduler.algorithms import used_resources_on_node, \
    calculate_read_write_ratio, substract_resources, divide_resources
from wca.scheduler.algorithms.fit import FitGeneric
from wca.scheduler.data_providers import DataProvider
from wca.scheduler.metrics import MetricName
from wca.scheduler.types import ResourceType as rt

log = logging.getLogger(__name__)


class Friend(FitGeneric):
    def __init__(self, data_provider: DataProvider,
                 dimensions: Iterable[rt] = (rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE),
                 max_node_score: int = 10,
                 alias=None
                 ):
        FitGeneric.__init__(self, data_provider, dimensions, alias=alias)
        self.max_node_score = max_node_score

    def __str__(self):
        if self.alias:
            return super().__str__()
        return '%s' % self.__class__.__name__

    def priority_for_node(self, node_name: str, app_name: str,
                          data_provider_queried: Tuple[Any]) -> int:
        nodes_capacities, assigned_apps_counts, apps_spec = data_provider_queried

        used, free, requested = \
            used_free_requested(node_name, app_name, self.dimensions,
                                nodes_capacities, assigned_apps_counts, apps_spec)
        membw_read_write_ratio = calculate_read_write_ratio(nodes_capacities[node_name])





def used_free_requested(
        node_name, app_name, dimensions,
        nodes_capacities, assigned_apps_counts, apps_spec):
    """Helper function not making any new calculations."""
    membw_read_write_ratio = calculate_read_write_ratio(nodes_capacities[node_name])
    used = used_resources_on_node(dimensions, assigned_apps_counts[node_name], apps_spec)
    free = substract_resources(nodes_capacities[node_name], used, membw_read_write_ratio)
    requested = apps_spec[app_name]
    return used, free, requested
