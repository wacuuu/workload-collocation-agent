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
from typing import Dict

from dataclasses import dataclass

from wca.detectors import AnomalyDetector, TasksMeasurements, TasksResources, TasksLabels
from wca.metrics import Metric
from wca.platforms import Platform

log = logging.getLogger(__name__)


@dataclass
class AEPDetector(AnomalyDetector):
    """Cyclic deterministic dummy anomaly detector."""
    node_labels: Dict[str, str]

    def detect(self,
               platform: Platform,
               tasks_measurements: TasksMeasurements,
               tasks_resources: TasksResources,
               tasks_labels: TasksLabels
               ):
        log.info('detect called, task=%i', len(tasks_labels))
        node_contention_score = 1.0
        metrics = [
            Metric('node_contention_score', node_contention_score, self.node_labels)
        ]

        for task_id, labels in tasks_labels.items():
            measurements = tasks_measurements[task_id]
            if 'app' in labels:
                app = labels['app']
                labels = dict(app=app)
                metrics_data = dict(
                    app_rw_ratio=measurements.get('task_rw_ratio', -1),
                    app_dram_hit_ratio=measurements.get('task_dram_hit_ratio', -1),
                    app_wss=measurements.get('wss', -1),
                    app_cache_utilization=measurements.get('task_rw_ratio', -1) * measurements.get(
                        'wss', -1) / 2 ** 37  # 128GB
                )
                for name, value in metrics_data.items():
                    metrics.append(
                        Metric(
                            name=name,
                            value=value,
                            labels=labels,
                        )
                    )
        return [], metrics
