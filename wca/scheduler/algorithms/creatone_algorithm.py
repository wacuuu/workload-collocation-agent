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

from wca.metrics import MetricName

from wca.scheduler.algorithms import Algorithm
from wca.scheduler.prometheus import do_query
from wca.scheduler.types import ExtenderArgs, ExtenderFilterResult, HostPriority

log = logging.getLogger(__name__)


@dataclass
class FAILURE_MESSAGE:
    NOT_PMM_NODE = "Not PMM node."
    NOT_ACCEPTABLE_MB = "Not acceptable memory bandwidth."


@dataclass
class CreatoneAlgorithm(Algorithm):
    prometheus_ip: str

    def filter(self, extender_args: ExtenderArgs) -> ExtenderFilterResult:
        metadata = extender_args.Pod.get('metadata', {})
        pod_namespace = metadata.get('namespace', None)

        extender_filter_result = ExtenderFilterResult()

        if pod_namespace != self.namespace:
            message = 'Different k8s namespace! ( %r != %r )'.format(pod_namespace, self.namespace)
            log.warning(message)
            extender_filter_result.Error = message
            return extender_filter_result

        for node_name in extender_args.NodeNames:
            if not _pmm_available(self.prometheus_ip, node_name):
                extender_filter_result.FailedNodes[node_name] = FAILURE_MESSAGE.NOT_PMM_NODE

            if not _mb_acceptable(self.prometheus_ip, node_name):
                extender_filter_result.FailedNodes[node_name] = FAILURE_MESSAGE.NOT_ACCEPTABLE_MB

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


def _pmm_available(prometheus_ip, node):
    # TODO: Implementation.
    return False


def _mb_acceptable(prometheus_ip, node):
    # TODO: Implementation.
    return False
