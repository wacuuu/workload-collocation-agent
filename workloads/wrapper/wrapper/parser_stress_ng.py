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

from io import TextIOWrapper
from typing import List, Dict
import re
from wca.metrics import Metric, MetricType
from wrapper import wrapper_main
from wrapper.parser import readline_with_check

EOF_line = "..."


def parse(input: TextIOWrapper, regexp: str, separator: str = None,
          labels: Dict[str, str] = {}, metric_name_prefix: str = '') -> List[Metric]:
    """Custom parse function for stress_ng
        stress-ng: info:  [25] Time 1572363779, counter 425, diff 61
        stress-ng: info:  [27] Time 1572363779, counter 426, diff 61
        stress-ng: info:  [23] Time 1572363780, counter 475, diff 60
        stress-ng: info:  [26] Time 1572363780, counter 322, diff 40
        stress-ng: info:  [24] Time 1572363780, counter 321, diff 39
        stress-ng: info:  [25] Time 1572363780, counter 485, diff 60
        stress-ng: info:  [27] Time 1572363780, counter 485, diff 59
        stress-ng: info:  [23] Time 1572363781, counter 536, diff 61
        stress-ng: info:  [24] Time 1572363781, counter 362, diff 41
        stress-ng: info:  [26] Time 1572363781, counter 363, diff 41
        stress-ng: info:  [25] Time 1572363781, counter 547, diff 62
        stress-ng: info:  [27] Time 1572363781, counter 547, diff 62
        stress-ng: info:  [23] stress-ng-stream: memory rate: 3852.67 MB/sec, 1541.07 Mflop/sec /
        (instance 0)
        stress-ng: info:  [27] stress-ng-stream: memory rate: 3922.76 MB/sec, 1569.10 Mflop/sec /
        (instance 4)
        stress-ng: info:  [26] Time 1572363782, counter 403, diff 40
        stress-ng: info:  [24] Time 1572363782, counter 402, diff 40
        stress-ng: info:  [25] Time 1572363782, counter 608, diff 61
        stress-ng: info:  [27] Time 1572363782, counter 609, diff 62
        stress-ng: info:  [25] stress-ng-stream: memory rate: 3920.62 MB/sec, 1568.25 Mflop/sec /
        (instance 2)
        stress-ng: info:  [24] stress-ng-stream: memory rate: 2597.47 MB/sec, 1038.99 Mflop/sec /
        (instance 1)
        stress-ng: info:  [26] stress-ng-stream: memory rate: 2603.78 MB/sec, 1041.51 Mflop/sec /
        (instance 3)
        stress-ng: info:  [22] successful run completed in 10.01s
        ---
        system-info:
              stress-ng-version: 0.10.08
              run-by: root
              date-yyyy-mm-dd: 2019:10:29
              time-hh-mm-ss: 15:43:02
              epoch-secs: 1572363782
              hostname: 31ff53b6528c
              sysname: Linux
              nodename: 31ff53b6528c
              release: 4.15.0-66-generic
              version: #75-Ubuntu SMP Tue Oct 1 05:24:09 UTC 2019
              machine: x86_64
              uptime: 28799
              totalram: 33605263360
              freeram: 14022410240
              sharedram: 2681659392
              bufferram: 1237618688
              totalswap: 0
              freeswap: 0
              pagesize: 4096
              cpus: 8
              cpus-online: 8
              ticks-per-second: 100

        stress-ng: info:  [22] stressor       bogo ops real time  usr time  sys time   bogo ops/s  /
         bogo ops/s
        stress-ng: info:  [22]                           (secs)    (secs)    (secs)   (real time) /
        (usr+sys time)
        metrics:
        stress-ng: info:  [22] stream             2623     10.00     49.82      0.10       262.18  /
        52.54
            - stressor: stream
              bogo-ops: 2623
              bogo-ops-per-second-usr-sys-time: 52.544071
              bogo-ops-per-second-real-time: 262.179501
              wall-clock-time: 10.004596
              user-time: 49.820000
              system-time: 0.100000

        ...
    """

    new_metrics = []
    new_line = readline_with_check(input, EOF_line)

    # Parse metric summary on the end stressing
    brief = re.search(
        r'(?P<bogo_ops>\d+.\d*) +'
        r'(?P<real_time>\d+.\d*) +'
        r'(?P<user_time>\d+.\d*) +'
        r'(?P<system_time>\d+.\d*) +'
        r'(?P<bogo_ops_per_second_real_time>\d+.\d*) +'
        r'(?P<bogo_ops_per_second_usr_sys_time>\d+.\d*)',
        new_line)
    if brief is not None:
        bogo_ops = float(brief['bogo_ops'])
        real_time = float(brief['real_time'])
        user_time = float(brief['user_time'])
        system_time = float(brief['system_time'])
        bogo_ops_real = float(brief['bogo_ops_per_second_real_time'])
        bogo_ops_usr_sys = float(brief['bogo_ops_per_second_usr_sys_time'])

        new_metrics.append(
            Metric(metric_name_prefix + 'bogo_ops', bogo_ops,
                   type=MetricType.GAUGE, labels=labels,
                   help="Summary bogo ops"))
        new_metrics.append(
            Metric(metric_name_prefix + 'real_time', real_time,
                   type=MetricType.GAUGE, labels=labels,
                   help="Summary real_time (secs)"))
        new_metrics.append(
            Metric(metric_name_prefix + 'user_time', user_time,
                   type=MetricType.GAUGE, labels=labels,
                   help="Summary user_time (secs)"))
        new_metrics.append(
            Metric(metric_name_prefix + 'system_time', system_time,
                   type=MetricType.GAUGE, labels=labels,
                   help="Summary system_time (secs)"))
        new_metrics.append(
            Metric(metric_name_prefix + 'bogo_ops_per_second_real_time', bogo_ops_real,
                   type=MetricType.GAUGE, labels=labels,
                   help="Summary bogo ops/s real time"))
        new_metrics.append(
            Metric(metric_name_prefix + 'bogo_ops_per_second_usr_sys_time', bogo_ops_usr_sys,
                   type=MetricType.GAUGE, labels=labels,
                   help="Summary bogo ops/s usr+sys time"))

    info = re.search(r'stress-ng: info: {2}\[(?P<id>\d*)\]+ ' +
                     r'Time (?P<time>\d*), counter (?P<counter>\d*), diff (?P<diff>\d*)', new_line)

    if info is not None:
        time = info['time']
        id_proc = info['id']
        counter = int(info['counter'])
        diff = int(info['diff'])

        labels.update({"id_proc_stress_ng": id_proc})
        labels.update({"stress_ng_time": time})
        new_metrics.append(
            Metric(metric_name_prefix + 'bogo_ops_counter', counter,
                   type=MetricType.COUNTER, labels=labels,
                   help="Counter bogo ops per proc stress-ng, updated per 1 sec"))
        new_metrics.append(
            Metric(metric_name_prefix + 'bogo_ops_gauge', diff,
                   type=MetricType.GAUGE, labels=labels,
                   help="Gauge bogo ops per proc stress-ng, updated per 1 sec"))

    return new_metrics


if __name__ == "__main__":
    wrapper_main.main(parse)
