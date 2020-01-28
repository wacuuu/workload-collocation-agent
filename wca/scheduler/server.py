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
from dataclasses import asdict
from flask import Flask, request, jsonify
from typing import Dict, List

from wca.metrics import Metric
from wca.scheduler.metrics import MetricName
from wca.scheduler.types import ExtenderArgs, ExtenderFilterResult
from wca.storage import (convert_to_prometheus_exposition_format,
                         is_convertable_to_prometheus_exposition_format)

log = logging.getLogger(__name__)

DEFAULT_NAMESPACE = 'default'


class Server:
    def __init__(self, configuration: Dict[str, str]):
        self.app = Flask('k8s scheduler extender')
        self.algorithm = configuration['algorithm']
        self.metrics_storage: List[Metric] = []

        self.filter_metrics: List[Metric] = []
        self.prioritize_metrics: List[Metric] = []

        # Internal counters.
        self.internal_counters: Dict[MetricName, int] = _prepare_internal_counters()

        @self.app.route('/status')
        def status():
            return jsonify('running')

        @self.app.route('/metrics')
        def metrics():
            for name, counter in self.internal_counters.items():
                self.metrics_storage.append(Metric(name, float(counter)))

            self.metrics_storage.append(self.filter_metrics)
            self.metrics_storage.append(self.prioritize_metrics)

            if is_convertable_to_prometheus_exposition_format(self.metrics_storage):
                prometheus_exposition = convert_to_prometheus_exposition_format(
                        self.metrics_storage)
                self.metrics_storage = []
                return prometheus_exposition
            else:
                log.warning('[Metrics] Cannot convert internal metrics '
                            'to prometheus exposition format!')
                self.metrics_storage = []
                return jsonify([])

        @self.app.route('/filter', methods=['POST'])
        def filter():
            extender_args = ExtenderArgs(**request.get_json())
            pod_namespace = extender_args.Pod['metadata']['namespace']
            pod_name = extender_args.Pod['metadata']['name']

            log.debug('[Filter] %r ' % extender_args)

            if DEFAULT_NAMESPACE == pod_namespace:
                log.info('[Filter] Trying to filter nodes for Pod %r' % pod_name)
                result, metrics = self.algorithm.filter(extender_args)
                log.info('[Filter] Result: %r' % result)

                self.filter_metrics = metrics
                self.internal_counters[MetricName.FILTER] += 1
                return jsonify(asdict(result))
            else:
                self.internal_counters[MetricName.POD_IGNORE_FILTER] += 1
                log.info('[Filter] Ignoring Pod %r : Different namespace!' %
                         pod_name)
                return jsonify(ExtenderFilterResult(NodeNames=extender_args.NodeNames))

        @self.app.route('/prioritize', methods=['POST'])
        def prioritize():
            extender_args = ExtenderArgs(**request.get_json())
            pod_namespace = extender_args.Pod['metadata']['namespace']
            pod_name = extender_args.Pod['metadata']['name']

            log.debug('[Prioritize] %r ' % extender_args)

            if DEFAULT_NAMESPACE == pod_namespace:
                log.info('[Prioritize] Trying to prioritize nodes for Pod %r' % pod_name)

                result, metrics = self.algorithm.prioritize(extender_args)

                priorities = [asdict(host)
                              for host in result]

                log.info('[Prioritize] Result: %r ' % priorities)

                self.prioritize_metrics = metrics
                self.internal_counters[MetricName.PRIORITIZE] += 1
                return jsonify(priorities)
            else:
                self.internal_counters[MetricName.POD_IGNORE_PRIORITIZE] += 1
                log.info('[Prioritize] Ignoring Pod %r : Different namespace!' %
                         pod_name)
                return jsonify([])


def _prepare_internal_counters() -> Dict[MetricName, int]:
    return {
        MetricName.POD_IGNORE_FILTER: 0,
        MetricName.POD_IGNORE_PRIORITIZE: 0,
        MetricName.FILTER: 0,
        MetricName.PRIORITIZE: 0
            }
