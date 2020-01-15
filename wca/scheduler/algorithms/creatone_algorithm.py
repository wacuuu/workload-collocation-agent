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
from dataclasses import dataclass, field
import logging
from typing import List


from wca.storage import Storage, DEFAULT_STORAGE
from wca.scheduler.algorithms import Algorithm
from wca.scheduler.types import ExtenderArgs, ExtenderFilterResult, HostPriority

log = logging.getLogger(__name__)


@dataclass
class FAILURE_MESSAGE:
    NOT_AVAILABLE = "Not available node."
    NOT_PMM_NODE = "Not PMM node."
    NOT_ACCEPTABLE_MB = "Not acceptable memory bandwidth."


@dataclass
class NodeType:
    DRAM = "DRAM"
    PMM = "PMM"


@dataclass
class CreatoneAlgorithm(Algorithm):
    namespace: str
    prometheus_ip: str
    metrics_storage: Storage = DEFAULT_STORAGE
    _cache: dict = field(default_factory=dict)

    def _classify_app(self, app: str):
        # TODO
        # Get memory usage.
        pass
        # Get memory bandwidth.
        pass
        # Get cpu usage.
        pass
        # Consider if it is PMM workload.
        pass

        return NodeType.DRAM

    def _acceptable_memory_bandwidth(self, node: str, app: str) -> bool:
        # TODO
        return True

    def filter(self, extender_args: ExtenderArgs) -> ExtenderFilterResult:
        extender_filter_result = ExtenderFilterResult()

        # Check if Pod is from our namespace.
        pod_namespace = extender_args.Pod['metadata']['namespace']
        if pod_namespace != self.namespace:
            message = 'Different k8s namespace! ( %r != %r )'.format(pod_namespace, self.namespace)
            log.warning(message)
            extender_filter_result.Error = message
            return extender_filter_result

        # Check if we already have any information about this kind of pod.
        app = extender_args.Pod['metadata'].get('labels', {}).get('app', None)
        if app:
            needed_node_type = self._clasiffy_app(app)

            # Check which nodes acceptable criteria.
            for node in extender_args.NodeNames:

                if needed_node_type != self._get_node_type(node):
                    continue

                if not _available_node(node, needed_node_type):
                    extender_filter_result.FailedNodes[node] = FAILURE_MESSAGE.NOT_AVAILABLE
                    continue

                if not self._acceptable_memory_bandwidth(node, app):
                    continue

                extender_filter_result.NodeNames.append(node)
        else:
            log.warning('No app label!')
            return extender_filter_result

        return extender_filter_result

    def prioritize(self, extender_args: ExtenderArgs) -> List[HostPriority]:
        metadata = extender_args.Pod.get('metadata', {})
        pod_namespace = metadata.get('namespace', None)

        host_priorities = []

        if pod_namespace != self.namespace:
            message = 'Different k8s namespace! ( %r != %r )'.format(pod_namespace, self.namespace)
            log.warning(message)
            return host_priorities

        return host_priorities


def _available_node(node):
    if node in ['node37', 'node39']:
        return False

    return True


def _pmm_available(prometheus_ip, node):
    # TODO: Implementation.
    return True


def _mb_acceptable(prometheus_ip, node):
    # TODO: Implementation.
    return True
