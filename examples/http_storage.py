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

from dataclasses import dataclass
from wca.storage import Storage
import logging
import requests

log = logging.getLogger(__name__)


@dataclass
class HTTPStorage(Storage):

    http_endpoint: str = 'http://127.0.0.1:8000'

    def store(self, metrics):
        log.info('sending!')
        try:
            requests.post(
                self.http_endpoint,
                json={metric.name: metric.value for metric in metrics},
                timeout=1
            )
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            log.warning('timeout!')
