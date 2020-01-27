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
from typing import List

from dataclasses import dataclass, field

from wca.scheduler.algorithms import Algorithm
from wca.scheduler.data_providers import DataProvider
from wca.scheduler.types import (ExtenderArgs, ExtenderFilterResult,
                                 HostPriority, ResourceType, Resources)
from wca.scheduler.utils import extract_common_input

log = logging.getLogger(__name__)


@dataclass
class FFDGeneric(Algorithm):
    """Fit first decreasing; supports as many dimensions as needed."""

    data_provider: DataProvider
    resources: List[ResourceType] = field(default_factory=lambda: [
            ResourceType.CPU, ResourceType.MEM,
            ResourceType.MEMORY_BANDWIDTH_READS, ResourceType.MEMORY_BANDWIDTH_WRITES])

    def app_fit_node(self, requested_resources: Resources,
                     node_free_resources: Resources) -> bool:
        return all([
            requested_resources[resource] < node_free_resources[resource]
            for resource in self.resources])

    def filter(self, extender_args: ExtenderArgs) -> ExtenderFilterResult:
        app, nodes, namespace, name = extract_common_input(extender_args)
        extender_filter_result = ExtenderFilterResult()

        log.debug('Getting app requested and node free resources.')
        log.debug('ExtenderArgs: %r' % extender_args)

        requested_resources = self.data_provider.get_app_requested_resources(app, self.resources)
        node_free_resources = self.data_provider.get_node_free_resources(self.resources)

        log.debug('Checking nodes.')
        for node in nodes:
            if node in node_free_resources:
                if not self.app_fit_node(requested_resources, node_free_resources[node]):
                    extender_filter_result.FailedNodes[node] = "Not enough resources."
                else:
                    extender_filter_result.NodeNames.append(node)
            else:
                extender_filter_result.FailedNodes[node] =\
                    'Missing info about "{}"'.format(node)

        log.debug('Results: {}'.format(extender_filter_result))

        return extender_filter_result

    def prioritize(self, extender_args: ExtenderArgs) -> List[HostPriority]:
        app, nodes, namespace, name = extract_common_input(extender_args)
        # choose node which has the most free resources
        return []
