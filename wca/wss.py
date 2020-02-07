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

import logging
import os

from wca.metrics import Measurements, MetricName

log = logging.getLogger(__name__)


class WSS:

    def __init__(self, get_pids, reset_interval):
        self.get_pids = get_pids
        self.reset_interval = reset_interval
        self._cycle = 0

    def get_measurements(self) -> Measurements:
        self._cycle += 1
        measurements = {}
        pids = set(self.get_pids(include_threads=False))
        all_pids = os.listdir('/proc')
        all_pids = set(filter(lambda x: x.isdecimal(), all_pids))
        pids = pids & all_pids
        log.debug('calculating wss for pids %s', pids)

        referenced = 0
        for pid in pids:
            try:
                with open('/proc/{}/smaps'.format(pid)) as f:
                    for line in f.readlines():
                        if 'Referenced' in line:
                            referenced += int(line.split('Referenced:')[1].split()[0])
            except (ProcessLookupError, FileNotFoundError):
                log.warning('pid does not exist for clearing refs - ignoring!')
                referenced = 0
        # Referenced comes in kb (rescale to bytes)
        referenced = referenced * 1000  # scale as mega bytes
        measurements[MetricName.TASK_WSS_REFERENCED_BYTES] = referenced

        if self._cycle % self.reset_interval == 0:
            for pid in pids:
                try:
                    with open('/proc/{}/clear_refs'.format(pid), 'w') as f:
                        f.write('1\n')
                except FileNotFoundError:
                    log.warning('pid does not exist for clearing refs - ignoring!')
                    pass

        return measurements
