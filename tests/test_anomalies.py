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

from owca.detectors import convert_anomalies_to_metrics
from owca.testing import anomaly, anomaly_metrics


@pytest.mark.parametrize('anomalies,expected_metrics', (
    ([], []),
    ([anomaly('t1', ['t2'])], anomaly_metrics('t1', ['t2'])),
    ([anomaly('t2', ['t1', 't3'])], anomaly_metrics('t2', ['t1', 't3'])),
))
def test_convert_anomalies_to_metrics(anomalies, expected_metrics):
    metrics_got = convert_anomalies_to_metrics(anomalies)
    assert metrics_got == expected_metrics
