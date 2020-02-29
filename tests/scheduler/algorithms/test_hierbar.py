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

from wca.scheduler.algorithms.hierbar import (
    _calc_average_resources, _resources_to_shape, _shape_diff,
    _create_shapes_from_nodes, reverse_node_shapes, merge_shapes)
from wca.scheduler.types import ResourceType as rt


@pytest.mark.parametrize('list_of_resources, expected_avg', [
    ([], {}),
    ([dict(x=1)], dict(x=1)),
    ([dict(x=1), dict(x=3)], dict(x=2)),
    ([dict(x=1, y=5), dict(x=3, y=7)], dict(x=2, y=6)),
])
def test_calc_average_resources_of_nodes(list_of_resources, expected_avg):
    avg = _calc_average_resources(list_of_resources)
    assert avg == expected_avg


@pytest.mark.parametrize('resources, expected_shape', [
    [{}, tuple()],
    [dict(x=1), (('x', 1),)],
    [dict(x=1, y=2), (('x', 1), ('y', 2))],
    [dict(z=1, y=2), (('y', 2), ('z', 1))],
])
def test_resources_to_shape(resources, expected_shape):
    got_shape = _resources_to_shape(resources)
    assert got_shape == expected_shape


@pytest.mark.parametrize('resources1, resources2, expected_diff', [
    [dict(x=1, y=2), dict(x=1, y=2), 0],
    [dict(x=1, y=2), dict(x=1, y=1), pytest.approx(0.7, 0.1)],
    [dict(x=1, y=10), dict(x=1, y=1), pytest.approx(6, 1)],
])
def test_shape_diff(resources1, resources2, expected_diff):
    shape1 = _resources_to_shape(resources1)
    shape2 = _resources_to_shape(resources2)
    got_diff = _shape_diff(shape1, shape2)
    assert got_diff == expected_diff


@pytest.mark.parametrize('resources1, resources2, expected_diff', [
    [dict(x=1, y=2), dict(x=1, y=2), 0],
    [dict(x=1, y=2), dict(x=1, y=3), pytest.approx(0.7, 0.1)],
    [dict(x=1, y=2), dict(x=1, y=1), pytest.approx(0.7, 0.1)],
    [dict(x=1, y=10), dict(x=1, y=1), pytest.approx(6, 1)],
])
def test_shape_diff(resources1, resources2, expected_diff):
    shape1 = _resources_to_shape(resources1)
    shape2 = _resources_to_shape(resources2)
    got_diff = _shape_diff(shape1, shape2)
    assert got_diff == expected_diff


@pytest.mark.parametrize(
    'merge_threshold, nodes, expected_shapes_number', [
        [0, [], 0],
        [0, [{rt.MEMBW_READ: 1, rt.MEMBW_WRITE: 1}], 1],
        [1, [{rt.MEMBW_READ: 1, rt.MEMBW_WRITE: 1}, {rt.MEMBW_READ: 1, rt.MEMBW_WRITE: 1}], 1],
        [1, [{rt.MEMBW_READ: 1, rt.MEMBW_WRITE: 1}, {rt.MEMBW_READ: 10, rt.MEMBW_WRITE: 10}], 1],
        [1, [{rt.MEMBW_READ: 1, rt.MEMBW_WRITE: 1}, {rt.MEMBW_READ: 15, rt.MEMBW_WRITE: 10}], 2],
        [1, [{rt.MEMBW_READ: 1, rt.MEMBW_WRITE: 1}, {rt.MEMBW_READ: 10, rt.MEMBW_WRITE: 10},
             {rt.MEMBW_READ: 15, rt.MEMBW_WRITE: 10}], 2],
    ])
def test_merge_shapes(merge_threshold: float, nodes, expected_shapes_number):
    node_capacities = {'n%i' % i: resources for i, resources in enumerate(nodes)}
    node_shapes = _create_shapes_from_nodes(node_capacities)
    shape_to_nodes = reverse_node_shapes(node_shapes)
    new_shape_to_nodes = merge_shapes(merge_threshold, node_capacities, shape_to_nodes)
    assert len(new_shape_to_nodes) == expected_shapes_number
