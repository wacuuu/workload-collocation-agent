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
import json
import logging
import time
from io import TextIOWrapper
from typing import List

from wca.metrics import Metric, MetricType
from wrapper import wrapper_main

log = logging.getLogger(__name__)

EOF_line = "Stop-Memtier-Now"


def parse(input: TextIOWrapper, regexp: str, separator: str = None,
          labels=None, metric_name_prefix: str = '') -> List[Metric]:
    """Custom parse function for memtier_benchmark
    memtier can't return proper json to stdout, tmp file is needed
    """
    if labels is None:
        labels = {}
    new_metrics = []

    # HACK: wait for process to finish in order to read from json file
    # _ = input.read()
    time.sleep(1)
    with open("/tmp/memtier_benchmark") as f:
        try:
            json_data = json.load(f)
        except json.decoder.JSONDecodeError:
            log.warning("Can't parse file")
            return []

    all_stats = json_data["ALL STATS"]

    new_metrics.append(Metric(
        metric_name_prefix + 'qps', all_stats["Totals"]["Ops/sec"],
        type=MetricType.GAUGE, labels=labels, help="QPS"
    ))
    new_metrics.append(Metric(
        metric_name_prefix + 'latency', all_stats["Totals"]["Latency"],
        type=MetricType.GAUGE, labels=labels, help="latency"
    ))
    return new_metrics


if __name__ == "__main__":
    wrapper_main.main(parse)
