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
from typing import Tuple, Any, Dict, Iterable
import logging

from wca.scheduler.algorithms import Algorithm
from wca.scheduler.algorithms.base import BaseAlgorithm
from wca.scheduler.utils import extract_common_input
from wca.scheduler.types import ExtenderArgs, ExtenderFilterResult, \
        HostPriority, NodeName, ResourceType as rt, AppName
from wca.scheduler.data_providers import DataProvider
from wca.logger import TRACE

log = logging.getLogger(__name__)


class StaticAssigner(BaseAlgorithm):
    def __init__(self, data_provider: DataProvider,
                 targeted_assigned_apps_counts: Dict[NodeName, Dict[AppName, int]],
                 dimensions = (rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE),
                 alias=None
                 ):
        BaseAlgorithm.__init__(self, data_provider, dimensions, alias=alias)
        self.targeted_assigned_apps_counts = targeted_assigned_apps_counts

    def app_fit_node(self, node_name: NodeName, app_name: str,
                     data_provider_queried) -> Tuple[bool, str]:
        """Consider if the app match the given node."""
        nodes_capacities, assigned_apps_counts, apps_spec = data_provider_queried
        log.debug(assigned_apps_counts)
        if node_name not in self.targeted_assigned_apps_counts:
            return False, 'node {} not specified in self.targeted_assigned_apps_counts'.format(node_name)
        if app_name not in self.targeted_assigned_apps_counts[node_name]:
            return False, 'app {} not specified in self.targeted_assigned_apps_counts'.format(app_name)

        if app_name not in assigned_apps_counts[node_name]:
            if self.targeted_assigned_apps_counts[node_name][app_name] > 0:
                return True, ''
            else:
                return False, 'app {} count on node {} already matching self.targeted_assigned_apps_counts'.format(app_name, node_name)

        if assigned_apps_counts[node_name][app_name] < \
                self.targeted_assigned_apps_counts[node_name][app_name]:
            return True, ''

        assert assigned_apps_counts[node_name][app_name] == \
            self.targeted_assigned_apps_counts[node_name][app_name]
        return False, 'app {} count on node {} already matching self.targeted_assigned_apps_counts'.format(app_name, node_name)

    def priority_for_node(self, node_name: str, app_name: str,
                          data_provider_queried: Tuple[Any]) -> float:
        """Considering priority of the given node."""
        return 0
