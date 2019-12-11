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
import logging

from scheduler import algorithms
from scheduler.utils import ExtenderArgs, extract_common_input


log = logging.getLogger(__name__)


class TestAlgorithms(algorithms.Algorithms):

    def __init__(self,
                 risk_threshold: float,
                 risk_query: str,
                 lookback: str):
        self._risk_threshold = risk_threshold
        self._risk_query = risk_query
        self._lookback = lookback

    def filter(self, extender_args: ExtenderArgs, k8s_namespace: str):
        log.debug('Pod: \n%s:', extender_args.Pod)
        app, nodes, namespace, name = extract_common_input(extender_args)
        nodes = self._filter_logic(app, nodes, namespace, k8s_namespace)
        log.info('[%s] Allowed nodes: %s', name, ', '.join(nodes))

        return dict(
            NodeNames=nodes,
            FailedNodes={},
            Error=''
                )

    def prioritize(self):
        pass

    def _filter_logic(self, app, nodes, namespace, k8s_namespace):
        if namespace != k8s_namespace:
            log.debug('Ignoring pods not from %r namespace (got %r)', self.k8s_namespace, namespace)
            return nodes

        risks = self._get_risk(app, nodes)
        if len(risks) == 0:
            log.debug('"%s" risks not found - ignoring', app)
            return nodes
        else:
            log.debug('"%s" risks for filter %r', app, risks)
            return [{node for node in nodes if node in risks and risks[node] < self.risk_threshold}]

    def _get_risk(self, app, nodes):
        """ in range 0 - 1 from query """
        risks = {}
        return risks
