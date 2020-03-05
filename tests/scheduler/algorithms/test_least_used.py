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
from wca.scheduler.algorithms.least_used import calculate_least_used_score
from wca.scheduler.types import CPU, MEM, MEMBW

@pytest.mark.parametrize('requested_fraction,weights,expected_score',[
    ({CPU: 0.5, MEM: 0.6}, {CPU: 1, MEM: 1}, 0.45),
    ({CPU: 0.4, MEM: 0.4}, {CPU: 1, MEM: 1}, 0.6),
    ({CPU: 0.1, MEM: 0.6}, {CPU: 1, MEM: 1}, 0.65),
    ({CPU: 0.1, MEM: 0.6}, {CPU: 1, MEM: 0.5}, approx(0.73, abs=0.1)),
])
def test_least_used_score(requested_fraction, weights, expected_score):
    free_fraction, got_score = calculate_least_used_score(requested_fraction, weights)
    assert got_score == expected_score
