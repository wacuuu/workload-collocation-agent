# Copyright (c) 2018 Intel Corporation
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
from itertools import chain

from wca.mesos import create_metrics, sanitize_label
from wca.metrics import Metric, merge_measurements, MetricName, \
    DerivedMetricName, METRICS_METADATA, \
    export_metrics_from_measurements, MetricMetadata, \
    MetricType, METRICS_LEVELS, MetricUnit, MetricSource


@pytest.mark.parametrize('label_key,expected_label_key', (
    ('org.apache.ble', 'ble'),
    ('org.apache.aurora.metadata.foo', 'foo'),
    ('some.dots.found', 'some_dots_found'),
))
def test_sanitize_labels(label_key, expected_label_key):
    assert sanitize_label(label_key) == expected_label_key


@pytest.mark.parametrize('task_measurements,expected_metrics', (
        ({}, []),
        ({'cpu': 15},
         [Metric(name='cpu', value=15)]),
        ({'cpu': 15, 'ram': 30},
         [
             Metric(name='cpu', value=15),
             Metric(name='ram', value=30)
         ]),
))
def test_create_metrics(task_measurements, expected_metrics):
    got_metrics = create_metrics(task_measurements)
    assert expected_metrics == got_metrics


@pytest.mark.parametrize('measurements_list,expected_merge', (
    ([{}, {}], {}),
    ([{'m1': 3}, {'m1': 5}, {'m2': 7}], {'m1': 8, 'm2': 7}),
    ([{'m1': 8}, {'m1': 3, 'm2': 2}], {'m1': 11, 'm2': 2}),
    ([{'m1': 8}, {'m1': 3}], {'m1': 11}),
    ([{'m1': 8, 'm2': 3}, {'m1': 3, 'm2': 7}, {'m1': 3}], {'m1': 14, 'm2': 10}),
    ([{'ipc': 2}, {'ipc': 4}], {'ipc': 3}),
    ([{'ipc': 2}, {'ipc': 4}], {'ipc': 3}),
    ([{'ipc': 2}, {'ipc': 4}, {'m1': 2}, {'m1': 3}], {'ipc': 3, 'm1': 5}),
    ([{'cycles': 2}, {'cycles': 4}], {'cycles': 6}),
))
def test_merge_measurements(measurements_list, expected_merge):
    assert merge_measurements(measurements_list) == expected_merge


def test_metric_meta_exists():
    for metric_name in chain(MetricName, DerivedMetricName):
        assert metric_name in METRICS_METADATA, 'missing metadata for metric %s' % metric_name


@pytest.mark.parametrize(
    'measurements, expected', [
        ({MetricName.MEM_NUMA_STAT_PER_TASK: {'1': 10, '2': 20}, }, 2),
        ({MetricName.CYCLES: 1123}, 1),
        ({}, 0)
    ])
def test_export_metrics_from_measurements(measurements, expected):
    result = export_metrics_from_measurements('PLATFORM__', measurements)
    assert len(result) == expected


class TestMetric(object):
    """To create and delete a test metric from metrics module structures."""
    def __enter__(self):
        MetricName.TEST_METRIC = 'test_metric'
        METRICS_METADATA['test_metric'] = MetricMetadata('Non existing metric for unit test.',
                                                         MetricType.COUNTER, MetricUnit.NUMERIC,
                                                         MetricSource.GENERIC)
        METRICS_LEVELS['test_metric'] = ['numa_node', 'container']  # two levels

    def __exit__(self, type, value, traceback):
        """if exception was raised the metrics structeres will be cleaned up."""
        del METRICS_METADATA['test_metric']
        del METRICS_LEVELS['test_metric']
        del MetricName.TEST_METRIC


def test_export_metrics_from_measurements_artifical_metric():
    """We currently do not have a metric which len(METRICS_LEVELS[X]) > 1,
        so the need to add such metric in metrics structures for the test."""
    with TestMetric():
        measurements = {'test_metric': {'id0': {'stress': 0, 'dbmango': 1},
                                        'id1': {'stress': 10, 'dbmango': 20}}}
        result = export_metrics_from_measurements('PLATFORM__', measurements)
        assert len(result) == 4
        assert result[0].name == 'PLATFORM__test_metric'
        assert 'numa_node' in result[0].labels and 'container' in result[0].labels
        assert sorted([item.value for item in result]) == [0, 1, 10, 20]  # values for metrics
