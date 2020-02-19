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
from typing import Tuple, Any

from wca.scheduler.algorithms import Algorithm, BaseAlgorithm
from wca.scheduler.utils import extract_common_input
from wca.scheduler.types import ExtenderArgs, ExtenderFilterResult, HostPriority, NodeName


class StaticAssigner(BaseAlgorithm):
    def __init__(self, data_provider: DataProvider,
                 targeted_assigned_apps_counts: Dict[NodeName, Dict[AppName, int]],
                 dimensions: Iterable[rt] = (rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE),
                 alias=None
                 ):
        FitGeneric.__init__(self, data_provider, dimensions, alias=alias)
        self.targeted_assigned_apps_counts = targeted_assigned_apps_counts

    def app_fit_node(self, node_name: NodeName, app_name: str,
                     data_provider_queried: Tuple[Any]) -> bool:
        """Consider if the app match the given node."""
        nodes_capacities, assigned_apps_counts, apps_spec = data_provider_queried

        if assigned_apps_counts[node_name][app_name] < self.targeted_assigned_apps_counts[node_name][app_name]:
            return True
        return False
