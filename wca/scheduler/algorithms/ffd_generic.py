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
from typing import List, Tuple

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
                     node_free_resources: Resources) -> Tuple[bool, str]:

        for resource in self.resources:

            requested = requested_resources[resource]
            free = node_free_resources[resource]

            if requested < free:
                continue
            else:
                return (False,
                        'Not enough %r ( requested: %r | free: %r )' % (resource, requested, free))

        return (True, '')

    def filter(self, extender_args: ExtenderArgs) -> ExtenderFilterResult:
        app, nodes, namespace, name = extract_common_input(extender_args)
        extender_filter_result = ExtenderFilterResult()

        log.debug('Getting app requested and node free resources.')
        log.debug('ExtenderArgs: %r' % extender_args)

        requested_resources = self.data_provider.get_app_requested_resources(app, self.resources)
        # 'wca_scheduler_requested_pod_resources' { 'app' 'resource' } value
        # 'wca_scheduler_node_free_resources' { 'node', 'resource' } value
        node_free_resources = self.data_provider.get_node_free_resources(self.resources)

        log.debug('Checking nodes.')
        for node in nodes:
            if node in node_free_resources:
                passed, message = self.app_fit_node(requested_resources, node_free_resources[node])
                if not passed:
                    extender_filter_result.FailedNodes[node] = message
                else:
                    extender_filter_result.NodeNames.append(node)
            else:
                log.warning('Missing Node %r information!' % node)
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
class FFDGeneric_AsymetricMembw(Algorithm):
    """Fit first decreasing; supports as many dimensions as needed."""

    data_provider: DataProvider
    dimensions: Tuple[ResourceType] = (ResourceType.CPU, ResourceType.MEM,
                                       ResourceType.MEMBW_WRITE, ResourceType.MEMBW_READ)

    def basic_check(self, app_requested: Dict[ResourceType, int], node_free_space: Dict[ResourceType, int]) -> bool:
        return all([app_requested[resource] < node_free_space[resource] for resource in self.dimensions])

    @staticmethod
    def membw_check(app_requested: Dict[ResourceType, int],
                    node_free_space: Dict[ResourceType, int],
                    node_membw_read_write_ratio: float) -> bool:
        """
        read/write ratio, e.g. 40GB/s / 10GB/s = 4,
        what means reading is 4 time faster
        """

        # Assert that required dimensions are available.
        for resource in (ResourceType.MEMBW_WRITE, ResourceType.MEMBW_READ,):
            for source in (app_requested, node_free_space):
                assert resource in source

        # To shorten the notation.
        WRITE = ResourceType.MEMBW_WRITE
        READ = ResourceType.MEMBW_READ
        requested = app_requested
        node = node_free_space
        ratio = node_membw_read_write_ratio

        return (node[READ] - requested[READ] - requested[WRITE] * ratio) > 0 and \
               (node[WRITE] - requested[WRITE] - requested[READ] / ratio) > 0

    def app_fit_node(self, app, node):
        app_requested   = {resource: self.data_provider.get_app_requested_resource(app, resource)
                           for resource in self.dimensions}
        node_free_space = {resource: self.data_provider.get_node_free_space_resource(node, resource)
                           for resource in self.dimensions}

        if not self.basic_check(app_requested, node_free_space):
            return False

        node_membw_read_write_ratio = self.data_provider.get_membw_read_write_ratio(node)

        return self.membw_check(app_requested, node_free_space, node_membw_read_write_ratio)

    def filter(self, extender_args: ExtenderArgs) -> ExtenderFilterResult:
        app, nodes, namespace, name = extract_common_input(extender_args)
        extender_filter_result = ExtenderFilterResult()

        for i, node in enumerate(nodes):
            if not self.app_fit_node(app, node):
                extender_filter_result.FailedNodes[node] = "Not enough resources."

        return extender_filter_result

    def prioritize(self, extender_args: ExtenderArgs) -> List[HostPriority]:
        app, nodes, namespace, name = extract_common_input(extender_args)
        # choose node which has the most free resources
        return []
