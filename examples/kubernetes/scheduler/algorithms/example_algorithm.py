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
from json import dumps
import logging
import math
from typing import List

from scheduler import algorithms
from scheduler.kubernetes import ExtenderFilterResult, HostPriority, ExtenderArgs
from scheduler.prometheus import do_raw_query, PrometheusException
from scheduler.utils import extract_common_input


log = logging.getLogger(__name__)


class ExampleAlgorithm(algorithms.Algorithm):

    def __str__(self):
        return "ExampleAlgorithm"

    def __repr__(self):
        return "ExampleAlgorithm"

    def __init__(self,
                 risk_threshold: float,
                 risk_query: str,
                 lookback: str,
                 time: str,
                 k8s_namespace: str,
                 prometheus_ip: str,
                 fit_query: str):
        self._risk_threshold = risk_threshold
        self._risk_query = risk_query
        self._lookback = lookback
        self._time = time
        self._k8s_namespace = k8s_namespace
        self._prometheus_ip = prometheus_ip
        self._fit_query = fit_query

    def filter(self, extender_args: ExtenderArgs) -> ExtenderFilterResult:
        log.debug('Pod: \n%s:', extender_args.Pod)
        app, nodes, namespace, name = extract_common_input(extender_args)
        nodes, error = self._filter_logic(app, nodes, namespace)
        log.info('[%s] Allowed nodes: %s', name, ', '.join(nodes))

        return ExtenderFilterResult(NodeNames=nodes, Error=error)

    def prioritize(self, extender_args: ExtenderArgs) -> List[HostPriority]:
        app, nodes, namespace, name = extract_common_input(extender_args)
        priorities = self._prioritize_logic(app, nodes, namespace)

        log.info('[%s] Priorities:  %s', name, '  '.join(
            '%s(%d), ' % (d.Host, d.Score) for d in sorted(priorities, key=lambda d: d.Host)))

        log.debug('priority list = %s', ', '.join((d for d in
                                                  sorted(priorities, key=lambda d: d.Host))))

        for d in priorities:
            assert isinstance(d.Score, int), 'will be silently discarded!'

        return dumps(priorities)

    def _prioritize_logic(self, app, nodes, namespace):
        if namespace != self._k8s_namespace:
            log.debug('ignoring pods not from %r namespace (got %r)',
                      self._k8s_namespace, namespace)
            return {}

        unweighted_priorities = self._get_priorities(app, nodes)

        priorities = [
            HostPriority(node, (priority * self._weight_multiplier))
            for node, priority in unweighted_priorities.items()
                ]

        return priorities

    def _get_priorities(self, app, nodes):
        """ in range 0 - 1 from query """
        priorities = {}
        query = self._fit_query % (app, self._lookback)
        try:
            nodes_fit = do_raw_query(self._prometheus_ip, query, 'node', self._time)
        except PrometheusException as e:
            log.warning(e)
            nodes_fit = []

        log.debug('nodes_fit for %r: %r', app, nodes_fit)
        for node in nodes:
            if node in nodes_fit:
                value = nodes_fit[node]
                if math.isnan(value):
                    log.debug('NaN fit value for %s - ignored')
                    continue
                priorities[node] = value
            else:
                log.debug('missing fit for %s - ignored')
                continue

        return priorities

    def _filter_logic(self, app, nodes, namespace):
        if namespace != self._k8s_namespace:
            log.debug('Ignoring pods not from %r namespace (got %r)', self.k8s_namespace, namespace)
            return nodes

        risks, error = self._get_risk(app, nodes)
        if len(risks) == 0:
            log.debug('"%s" risks not found - ignoring', app)
            return nodes, error
        else:
            log.debug('"%s" risks for filter %r', app, risks)
            return [{node
                    for node in nodes
                    if node in risks and
                    risks[node] < self.risk_threshold}], error

    def _get_risk(self, app, nodes):
        """ in range 0 - 1 from query """
        risks = {}
        query = self._risk_query % (app, self._lookback)

        error = ''
        try:
            nodes_risk = do_raw_query(self._prometheus_ip, query, 'node', self._time)
        except PrometheusException as e:
            log.warning(e)
            error = str(e)
            nodes_risk = []

        log.debug('nodes_risk for %r: %r', app, risks)
        for node in nodes:
            if node in nodes_risk:
                value = nodes_risk[node]
                if math.isnan(value):
                    log.debug('NaN risk value for %s - ignored')
                    continue
            else:
                log.debug('missing fit for %s - ignored')
                continue

        return risks, error