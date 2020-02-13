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
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

from wca.metrics import Metric, MetricType
from wca.storage import (convert_to_prometheus_exposition_format,
                         is_convertable_to_prometheus_exposition_format)

log = logging.getLogger(__name__)

PREFIX = 'wca_scheduler_'


class MetricName(str, Enum):
    POD_IGNORE_FILTER = PREFIX + 'pod_ignore_filter'
    POD_IGNORE_PRIORITIZE = PREFIX + 'pod_ignore_prioritize'
    FILTER = PREFIX + 'filter'
    PRIORITIZE = PREFIX + 'prioritize'
    APP_REQUESTED_RESOURCE = PREFIX + 'app_requested_resource'
    NODE_CAPACITY_RESOURCE = PREFIX + 'node_capacity_resource'
    NODE_USED_RESOURCE = PREFIX + 'node_used_resource'

    def __repr__(self):
        return repr(self.value)


@dataclass
class MetricRegistry:
    """Store metrics in prometheus way"""
    _storage: Dict[MetricName, List[Metric]] = field(default_factory=lambda: {})

    def add(self, metric: Metric):
        # Check if metric is already in registry.
        if metric.name in self._storage:

            # Check if there is no same metric in registry.
            metric_already_here = False
            for registered_metric in self._storage[metric.name]:
                if registered_metric.labels == metric.labels:
                    metric_already_here = True
                    # Check metric type.
                    if metric.type == MetricType.GAUGE:
                        # Gauges should be overwriten.
                        registered_metric.value = metric.value
                    elif metric.type == MetricType.COUNTER:
                        # Counters should be incremented.
                        registered_metric.value += metric.value

            # If there is no same metric, add new one.
            if not metric_already_here:
                self._storage[metric.name].append(metric)

        # There is no this kind metrics.
        else:
            self._storage[metric.name] = [metric]

    def clean(self):
        self._storage = {}

    def prometheus_exposition(self) -> str:
        metrics = []

        for _, new_metrics in self._storage.items():
            log.debug('[Metrics] %s', new_metrics)
            metrics.extend(new_metrics)

        if is_convertable_to_prometheus_exposition_format(metrics):
            prometheus_exposition = convert_to_prometheus_exposition_format(metrics)
            return prometheus_exposition
        else:
            log.warning('[Metrics] Cannot convert metrics '
                        'to prometheus exposition format!')
            return ""
