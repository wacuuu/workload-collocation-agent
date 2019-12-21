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

QUERY_PATH = "/api/v1/query"
QUERY_RANGE_PATH = "/api/v1/query_range"
URL_TPL = '{prometheus}{path}?query={name}'
RANGE_TPL = '&start={start}&end={end}&step=1s'
TIME_TPL = '&time={time}'
TAG_TPL = '{key}="{value}"'

SESSION_TIMEOUT = 1


prometheus_adapter = requests.adapters.HTTPAdapter(max_retries=1)


class PrometheusException(Exception):
    pass


def _build_raw_query(prometheus, query, time=None):
    path = QUERY_PATH
    url = URL_TPL.format(
        prometheus=prometheus,
        path=path,
        name=query,)

    if time:
        url += TIME_TPL.format(time=time)

    log.debug('Full url: %s', url)
    return url


def do_raw_query(prometheus_ip, query, result_tag, time):
    url = _build_raw_query(prometheus_ip, query, time)
    session = requests.Session()
    session.mount(url, prometheus_adapter)

    try:
        response = session.get(url, timeout=SESSION_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise PrometheusException(e)

    response = response.json()

    assert response['data']['resultType'] == 'vector'
    result = response['data']['result']
    return {
            pair['metric'][result_tag]: float(pair['value'][1])
            for pair in result
            }
