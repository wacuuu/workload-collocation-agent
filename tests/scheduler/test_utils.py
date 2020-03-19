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

from wca.scheduler.utils import calculate_used_node_resources, get_nodes_used_resources
from wca.scheduler.types import ResourceType

TEST_DIMENSIONS = set([
    ResourceType.CPU,
    ResourceType.MEM,
    ResourceType.MEMBW_READ,
    ResourceType.MEMBW_WRITE
])

TEST_APP_SPEC = {
        'memcached-mutilate-big': {
            ResourceType.CPU: 4.,
            ResourceType.MEM: 40.,
            ResourceType.MEMBW_READ: 4.,
            ResourceType.MEMBW_WRITE: 2.
            },
        'memcached-mutilate-medium': {
            ResourceType.CPU: 2.,
            ResourceType.MEM: 20,
            ResourceType.MEMBW_READ: 2.,
            ResourceType.MEMBW_WRITE: 1.
        },
        'memcached-mutilate-small': {
            ResourceType.CPU: 1.,
            ResourceType.MEM: 10.,
            ResourceType.MEMBW_READ: 1.,
            ResourceType.MEMBW_WRITE: .5
            }
}


@pytest.mark.parametrize('dimensions, assigned_apps, apps_spec, expected', [
    (TEST_DIMENSIONS, {}, TEST_APP_SPEC, {'cpu': 0, 'mem': 0, 'membw_read': 0, 'membw_write': 0}),
    (TEST_DIMENSIONS, {'memcached-mutilate-big': 1}, TEST_APP_SPEC,
        {'cpu': 4.0, 'mem': 40.0, 'membw_read': 4.0, 'membw_write': 2.0}),
    (TEST_DIMENSIONS, {'memcached-mutilate-big': 4, 'memcached-mutilate-small': 2}, TEST_APP_SPEC,
        {'cpu': 18.0, 'mem': 180.0, 'membw_read': 18.0, 'membw_write': 9.0}),
])
def test_calculate_used_node_resources(dimensions, assigned_apps, apps_spec, expected):
    assert calculate_used_node_resources(dimensions, assigned_apps, apps_spec) == expected


@pytest.mark.parametrize('dimensions, apps_on_node, apps_spec, expected', [
    (TEST_DIMENSIONS, {}, TEST_APP_SPEC, {}),
    (TEST_DIMENSIONS, {
        'node101': {}
        },
        TEST_APP_SPEC, {
        'node101': {'cpu': 0, 'mem': 0, 'membw_read': 0, 'membw_write': 0}
        }),
    (TEST_DIMENSIONS, {
        'node101': {},
        'node102': {'memcached-mutilate-big': ['memcached-mutilate-big-0']}
        },
        TEST_APP_SPEC, {
        'node101': {'cpu': 0, 'mem': 0, 'membw_read': 0, 'membw_write': 0},
        'node102': {'cpu': 4.0, 'mem': 40.0, 'membw_read': 4.0, 'membw_write': 2.0}
        }),
    (TEST_DIMENSIONS, {
        'node101': {},
        'node102': {
            'memcached-mutilate-big': [
                'memcached-mutilate-big-0',
                'memcached-mutilate-big-1',
                'memcached-mutilate-big-2',
                'memcached-mutilate-big-3'],
            'memcached-mutilate-small': [
                'memcached-mutilate-small-0',
                'memcached-mutilate-small-1'],
            }
        },
        TEST_APP_SPEC, {
        'node101': {'cpu': 0, 'mem': 0, 'membw_read': 0, 'membw_write': 0},
        'node102': {'cpu': 18.0, 'mem': 180.0, 'membw_read': 18.0, 'membw_write': 9.0}
        }),
    ])
def test_get_nodes_used_resources(dimensions, apps_on_node, apps_spec, expected):
    assert get_nodes_used_resources(dimensions, apps_on_node, apps_spec) == expected
