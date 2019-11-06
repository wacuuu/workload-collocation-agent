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

from wca.resources import calculate_pod_resources


def test_calculate_resources_empty():
    container_spec = [{'resources': {}}]
    assert {} == calculate_pod_resources(container_spec)


def test_calculate_resources_with_requests_and_limits():
    container_spec = [
        {'resources': {'limits': {'cpu': '250m', 'memory': '64Mi'},
                       'requests': {'cpu': '250m', 'memory': '64Mi'}}}
    ]
    assert {'limits_cpu': 0.25,
            'limits_memory': float(64 * 1024 ** 2),
            'requests_cpu': 0.25,
            'requests_memory': float(64 * 1024 ** 2),
            'cpus': 0.25,
            'mem': float(64 * 1024 ** 2)
            } == calculate_pod_resources(container_spec)


def test_calculate_resources_multiple_containers():
    container_spec = [
        {'resources': {'requests': {'cpu': '250m', 'memory': '67108864'}}},
        {'resources': {'requests': {'cpu': '100m', 'memory': '32Mi'}}}
    ]
    assert {'requests_cpu': 0.35, 'requests_memory':
            float(67108864 + 32 * 1024 ** 2),
            'cpus': 0.35,
            'mem': float(67108864 + 32 * 1024 ** 2)
            } == calculate_pod_resources(container_spec)
