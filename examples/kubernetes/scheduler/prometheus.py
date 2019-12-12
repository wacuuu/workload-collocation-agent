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
import logging
import requests

log = logging.getLogger(__name__)


# CONSTANTS
_PROMETHEUS_QUERY_PATH = "/api/v1/query"
_PROMETHEUS_QUERY_RANGE_PATH = "/api/v1/query_range"
_PROMETHEUS_URL_TPL = '{prometheus}{path}?query={name}'
_PROMETHEUS_RANGE_TPL = '&start={start}&end={end}&step=1s'
_PROMETHEUS_TIME_TPL = '&time={time}'
_PROMETHEUS_TAG_TPL = '{key}="{value}"'


def _build_raw_query(prometheus, query, time=None):
    path = _PROMETHEUS_QUERY_PATH
    url = _PROMETHEUS_URL_TPL.format(
        prometheus=prometheus,
        path=path,
        name=query,)

    if time:
        url += _PROMETHEUS_TIME_TPL.format(time=time)

    log.debug('Full url: %s', url)
    return url


def do_raw_query(prometheus_ip, query, result_tag, time):
    url = _build_raw_query(prometheus_ip, query, time)
    response = requests.get(url)
    response = response.json()

    if response['status'] == 'error':
        raise Exception(response['error'])

    assert response['data']['resultType'] == 'vector'
    result = response['data']['result']
    return {pair['metric'][result_tag]: float(pair['value'][1]) for pair in result}
