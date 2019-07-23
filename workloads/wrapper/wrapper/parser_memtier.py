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

from io import TextIOWrapper
from typing import List
import json
from wca.metrics import Metric, MetricType
from wrapper import wrapper_main

EOF_line = "Stop-Mutilate-Now"


def parse(input: TextIOWrapper, regexp: str, separator: str = None,
          labels=None, metric_name_prefix: str = '') -> List[Metric]:
    """Custom parse function for memtier_benchmark
    memtier return json if properly configured, it's not 100% compliant but python json should
    be able to take care of it
    """
    if labels is None:
        labels = {}
    new_metrics = []

    json_data = json.load(input)

    all_stats = json_data["ALL STATS"]

    new_metrics.append(Metric(
        metric_name_prefix + 'qps', all_stats["Total"]["Ops/sec"],
        type=MetricType.GAUGE, labels=labels, help="QPS"
    ))

    return new_metrics


if __name__ == "__main__":
    wrapper_main.main(parse)
