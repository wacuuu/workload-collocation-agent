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
import pytest
from typing import List

from wca.metrics import Metric, MetricType, MetricUnit, MetricGranularity
from wca.scheduler.metrics import MetricRegistry, MetricName


@pytest.mark.parametrize('metrics, expected_prometheus_exposition', [
    ([
        Metric(name=MetricName.FILTER, value=1, type=MetricType.COUNTER),
        Metric(name=MetricName.FILTER, value=1, type=MetricType.COUNTER)],
        "# TYPE wca_scheduler_filter counter\n"
        "wca_scheduler_filter 2\n"),
    ([
        Metric(name=MetricName.FILTER, value=5, type=MetricType.GAUGE),
        Metric(name=MetricName.FILTER, value=1, type=MetricType.GAUGE)],
        "# TYPE wca_scheduler_filter gauge\n"
        "wca_scheduler_filter 1\n"),
    ([
        Metric(name=MetricName.PRIORITIZE, value=5, type=MetricType.COUNTER),
        Metric(name=MetricName.FILTER, value=1, type=MetricType.GAUGE)],
        "# TYPE wca_scheduler_filter gauge\n"
        "wca_scheduler_filter 1\n"
        "# TYPE wca_scheduler_prioritize counter\n"
        "wca_scheduler_prioritize 5\n"),
    ])
def test_metric_registry_add(metrics: List[Metric], expected_prometheus_exposition: str):
    mr = MetricRegistry()
    for metric in metrics:
        mr.add(metric)

    assert expected_prometheus_exposition == mr.prometheus_exposition()


@pytest.mark.parametrize('metrics', [
    ([Metric(name=MetricName.FILTER, value=1, type=MetricType.GAUGE),
        Metric(name=MetricName.FILTER, value=1, type=MetricType.COUNTER)]),
    ([Metric(name=MetricName.FILTER, value=1, help="first"),
        Metric(name=MetricName.FILTER, value=1, help="second")]),
    ([Metric(name=MetricName.FILTER, value=1, unit=MetricUnit.BYTES),
        Metric(name=MetricName.FILTER, value=1, unit=MetricUnit.NUMERIC)]),
    ([Metric(name=MetricName.FILTER, value=1, granularity=MetricGranularity.PLATFORM),
        Metric(name=MetricName.FILTER, value=1, granularity=MetricGranularity.TASK)]),
    ])
def test_metric_registry_add_assert(metrics: List[Metric]):
    mr = MetricRegistry()
    with pytest.raises(AssertionError):
        for metric in metrics:
            mr.add(metric)
