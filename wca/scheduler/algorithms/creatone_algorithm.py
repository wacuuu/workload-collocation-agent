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
from dataclasses import dataclass
import logging
from typing import List


from wca.scheduler.algorithms import Algorithm
from wca.scheduler.types import ExtenderArgs, ExtenderFilterResult, HostPriority

log = logging.getLogger(__name__)


@dataclass
class FAILURE_MESSAGE:
    NOT_AVAILABLE = "Not available node."
    NOT_PMM_NODE = "Not PMM node."
    NOT_ACCEPTABLE_MB = "Not acceptable memory bandwidth."


@dataclass
class CreatoneAlgorithm(Algorithm):
    namespace: str
    prometheus_ip: str

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
        app_label = extender_args.Pod['metadata'].get('labels', {}).get('app', None)
        if app_label:
            # TODO
            pass
        else:
            log.warning('No app label!')
            return extender_filter_result

        # Check which nodes acceptable criteria.
        for node_name in extender_args.NodeNames:
            if not _available_node(node_name):
                extender_filter_result.FailedNodes[node_name] = FAILURE_MESSAGE.NOT_AVAILABLE
                continue

            if not _pmm_available(self.prometheus_ip, node_name):
                extender_filter_result.FailedNodes[node_name] = FAILURE_MESSAGE.NOT_PMM_NODE
                continue

            if not _mb_acceptable(self.prometheus_ip, node_name):
                extender_filter_result.FailedNodes[node_name] = FAILURE_MESSAGE.NOT_ACCEPTABLE_MB
                continue

            extender_filter_result.NodeNames.append(node_name)

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
    if node == 'node37':
        return False
    return True


def _pmm_available(prometheus_ip, node):
    # TODO: Implementation.
    return True


def _mb_acceptable(prometheus_ip, node):
    # TODO: Implementation.
    return True
