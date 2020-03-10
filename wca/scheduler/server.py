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
import time
import threading
from typing import Dict

from dataclasses import asdict
from flask import Flask, request, jsonify

from wca.config import Numeric
from wca.metrics import Metric, MetricType
from wca.scheduler.algorithms import Algorithm, RescheduleResult
from wca.scheduler.metrics import MetricName
from wca.scheduler.types import ExtenderArgs, ExtenderFilterResult

log = logging.getLogger(__name__)

DEFAULT_NAMESPACE = 'default'
DEFAULT_METRIC_LABELS = {}


class Server:
    def reschedule(self, interval: Numeric(0, 60)):
        while True:
            time.sleep(interval)
            reschedule_result: RescheduleResult = self.algorithm.reschedule()

            for node in reschedule_result:
                # TODO: kubeapi delete task
                pass

    def __init__(self, configuration: Dict[str, str]):
        self.app = Flask('k8s scheduler extender')
        self.algorithm: Algorithm = configuration['algorithm']

        interval = configuration.get('reschedule_interval', 5)

        reschedule_thread = threading.Thread(target=self.reschedule, args=[interval])
        reschedule_thread.start()

        @self.app.route('/status')
        def status():
            return jsonify(True)

        @self.app.route('/metrics')
        def metrics():
            metrics_registry = self.algorithm.get_metrics_registry()
            if metrics_registry:
                return metrics_registry.prometheus_exposition()
            else:
                return ''

        @self.app.route('/filter', methods=['POST'])
        def filter():
            extender_args = ExtenderArgs(**request.get_json())
            pod_namespace = extender_args.Pod['metadata']['namespace']
            pod_name = extender_args.Pod['metadata']['name']

            log.debug('[Filter] %r ' % extender_args)
            metrics_registry = self.algorithm.get_metrics_registry()

            if DEFAULT_NAMESPACE == pod_namespace:
                log.info('[Filter] Trying to filter nodes for Pod %r' % pod_name)

                result = self.algorithm.filter(extender_args)

                log.info('[Filter] Result: %r' % result)

                if metrics_registry:
                    metrics_registry.add(Metric(
                        name=MetricName.FILTER,
                        value=1,
                        labels=DEFAULT_METRIC_LABELS,
                        type=MetricType.COUNTER))

                return jsonify(asdict(result))
            else:
                log.info('[Filter] Ignoring Pod %r : Different namespace!' %
                         pod_name)

                if metrics_registry:
                    metrics_registry.add(Metric(
                        name=MetricName.POD_IGNORE_FILTER,
                        value=1,
                        labels=DEFAULT_METRIC_LABELS,
                        type=MetricType.COUNTER))

                return jsonify(ExtenderFilterResult(NodeNames=extender_args.NodeNames))

        @self.app.route('/prioritize', methods=['POST'])
        def prioritize():
            extender_args = ExtenderArgs(**request.get_json())
            pod_namespace = extender_args.Pod['metadata']['namespace']
            pod_name = extender_args.Pod['metadata']['name']

            metrics_registry = self.algorithm.get_metrics_registry()
            log.debug('[Prioritize-server] %r ' % extender_args)

            if DEFAULT_NAMESPACE == pod_namespace:
                log.info('[Prioritize-server] Trying to prioritize nodes for Pod %r' % pod_name)

                result = self.algorithm.prioritize(extender_args)

                priorities = [asdict(host)
                              for host in result]

                log.info('[Prioritize-server] Result: %r ' % priorities)

                if metrics_registry:
                    metrics_registry.add(Metric(
                        name=MetricName.PRIORITIZE,
                        value=1,
                        labels=DEFAULT_METRIC_LABELS,
                        type=MetricType.COUNTER))

                return jsonify(priorities)
            else:
                log.info('[Prioritize-server] Ignoring Pod %r : Different namespace!' %
                         pod_name)

                if metrics_registry:
                    metrics_registry.add(Metric(
                        name=MetricName.POD_IGNORE_PRIORITIZE,
                        value=1,
                        labels=DEFAULT_METRIC_LABELS,
                        type=MetricType.COUNTER))

                return jsonify([])
