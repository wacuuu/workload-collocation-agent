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
from flask import Flask, request
from typing import Dict, List

import logging

app = Flask('k8s scheduler extender')

log = logging.getLogger(__name__)


@dataclass
class ExtenderArgs:
    Nodes: List[Dict]
    Pod: dict
    NodeNames: List[str]


class Server:
    def __init__(self, configuration: Dict[str, str]):
        app = Flask('k8s scheduler extender')
        self.app = app
        self.host = configuration.get('host', 'localhost')
        self.port = configuration.get('port', '12345')
        self.prometheus_ip = configuration.get('prometheus_ip', 'localhost:30900')
        self.k8s_namespace = configuration.get('k8s_namespace', 'default')
        self.risk_threshold = configuration.get('risk_threshold', 0.3)
        self.risk_query = configuration.get('risk_query')
        self.lookback = configuration.get('lookback')

        @app.route('/api/scheduler/test')
        def hello():
            return "Hello World"

        @app.route('/api/scheduler/filter', methods=['POST'])
        def filter():
            extender_args = ExtenderArgs(**request.get_json())
            return self._filter(extender_args)

        @app.route('/api/scheduler/prioritize')
        def prioritize():
            return self._prioritize()

    def run(self):
        self.app.run(host=self.host, port=self.port, debug=True)

    def _get_risk(self, app, nodes, risk_query, lookback):
        """ in range 0 - 1 from query """
        risks = {}
        query = risk_query % (app, lookback)
        return {}

    def _filter_logic(self, app, nodes, namespace, risk_query, lookback):
        if namespace != self.k8s_namespace:
            log.debug('Ignoring pods not from %r namespace (got %r)', self.k8s_namespace, namespace)
            return nodes

        risks = self._get_risk(app, nodes, risk_query, lookback)
        if len(risks) == 0:
            log.debug('"%s" risks not found - ignoring', app)
            return nodes
        else:
            log.debug('"%s" risks for filter %r', app, risks)
            return [{node for node in nodes if node in risks and risks[node] < self.risk_threshold}]

    def _filter(self, extender_args: ExtenderArgs):
        log.debug('Pod: \n%s:', extender_args.Pod)
        app, nodes, namespace, name = self._extract_common_input(extender_args)
        nodes = self._filter_logic(app, nodes, namespace)
        log.info('[%s] Allowed nodes: %s', name, ', '.join(nodes))

        return dict(
            NodeNames=nodes,
            FailedNodes={},
            Error=''
                )

    def _prioritize(self):
        return None

    def _extract_common_input(self, extender_args):
        nodes = extender_args.NodeNames
        labels = extender_args.Pod['metadata']['labels']
        name = extender_args.Pod['metadata']['name']
        namespace = extender_args.Pod['metadata']['namespace']
        app = labels.get('app', None)
        return app, nodes, namespace, name
