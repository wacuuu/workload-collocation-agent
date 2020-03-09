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
from pytest import approx

from wca.scheduler.algorithms.bar import calculate_variance
from wca.scheduler.types import CPU, MEM, MEMBW_READ


@pytest.mark.parametrize('requested_fraction,bar_weights,expected_variance', [
    ({CPU: 0.4, MEM: 0.4}, {CPU: 1, MEM: 1}, 0),
    ({CPU: 0.5, MEM: 0.6}, {CPU: 1, MEM: 1}, approx(0.1, abs=0.01)),
    ({CPU: 0.4, MEM: 0.4, MEMBW_READ: 0.6}, {CPU: 1, MEM: 1, MEMBW_READ: 1}, approx(0.01, abs=0.01)),
    ({CPU: 0.4, MEM: 0.5, MEMBW_READ: 0.6}, {CPU: 1, MEM: 1, MEMBW_READ: 1}, approx(0.01, abs=0.01)),
    ({CPU: 0.1, MEM: 0.5, MEMBW_READ: 0.6}, {CPU: 1, MEM: 1, MEMBW_READ: 1}, approx(0.05, abs=0.01)),
    ({CPU: 0.1, MEM: 0.5, MEMBW_READ: 0.6}, {CPU: 0, MEM: 1, MEMBW_READ: 1}, approx(0.02, abs=0.01)),
    ({CPU: 0.1, MEM: 0.5, MEMBW_READ: 0.6}, {CPU: 0.5, MEM: 1, MEMBW_READ: 1}, approx(0.04, abs=0.01)),
])
def test_calculate_variance(requested_fraction, bar_weights, expected_variance):
    got_variance, _ = calculate_variance('app1', 'node1', requested_fraction, bar_weights)
    assert got_variance == expected_variance
