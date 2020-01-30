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
import requests
from dataclasses import dataclass
from typing import List, Dict, Optional

from wca.config import Numeric
from wca.scheduler.data_providers import DataProvider
from wca.scheduler.types import ResourceType, NodeName, Resources
from wca.security import SSL, HTTPSAdapter

log = logging.getLogger(__name__)

QUERY_PATH = "/api/v1/query"
URL_TPL = '{prometheus_ip}{path}?query={name}'


class PrometheusDataProviderException(Exception):
    pass


NODE_FREE_RESOURCES_QUERY_MAP: Dict[ResourceType, str] = {
    ResourceType.CPU: 'sum(platform_topology_cores) by (nodename) - '
    'sum(task_requested_cpus) by (nodename) or sum(platform_topology_cores) by (nodename)',
    ResourceType.MEM: 'sum(node_memory_MemTotal_bytes) by (nodename) - '
    'sum(task_requested_mem_bytes) by (nodename) or sum(node_memory_MemTotal_bytes) '
    'by (nodename)',
    ResourceType.MEMBW_READ: 'sum(platform_nvdimm_read_bandwidth_bytes_per_second) '
    'by (nodename) - sum(delta(platform_pmm_bandwidth_reads[5s])*64) by (nodename) or '
    'sum(platform_nvdimm_read_bandwidth_bytes_per_second) by (nodename)',
    ResourceType.MEMBW_WRITE: 'sum(platform_nvdimm_write_bandwidth_bytes_per_'
    'second) by (nodename) - sum(delta(platform_pmm_bandwidth_writes[5s])*64) by (nodename) or '
    'sum(platform_nvdimm_write_bandwidth_bytes_per_second) by (nodename)'
}

APP_REQUESTED_RESOURCES_QUERY_MAP: Dict[ResourceType, str] = {
        ResourceType.CPU: 'max_over_time(task_requested_cpus{app=%r}[24h:5s])',
        ResourceType.MEM: 'max_over_time(task_requested_mem_bytes{app=%r}[24h:5s])',
        ResourceType.MEMBW_READ: 'max_over_time'
        '(task_membw_reads_bytes_per_second{app=%r}[24h:5s])',
        ResourceType.MEMBW_WRITE: 'max_over_time'
        '(task_membw_writes_bytes_per_second{app=%r}[24h:5s])'
}


@dataclass
class PrometheusDataProvider(DataProvider):
    ip: str
    timeout: Optional[Numeric(1, 60)] = 1.0
    ssl: Optional[SSL] = None

    def get_node_free_resources(
            self, resources_types: List[ResourceType]) -> Dict[NodeName, Resources]:

        free_resources = {}
        for resource in resources_types:
            results = self._do_query(NODE_FREE_RESOURCES_QUERY_MAP[resource])
            for result in results:
                node = result['metric']['nodename']
                value = result['value'][1]

                if node not in free_resources:
                    free_resources[node] = {}

                free_resources[node][resource] = float(value)

        log.debug('Free resources: {}'.format(free_resources))

        return free_resources

    def get_app_requested_resources(
            self, app: str, resources_types: List[ResourceType]) -> Resources:

        requested_resources = {resource: 0.0 for resource in resources_types}
        for resource in resources_types:
            results = self._do_query(APP_REQUESTED_RESOURCES_QUERY_MAP[resource] % app)
            for result in results:
                value = result['value'][1]

                requested_resources[resource] = float(value)

        log.debug('Requested resources: {}'.format(requested_resources))

        return requested_resources

    def _do_query(self, query: str):
        url = URL_TPL.format(
                prometheus_ip=self.ip,
                path=QUERY_PATH,
                name=query)
        try:
            if self.ssl:
                s = requests.Session()
                s.mount(self.ip, HTTPSAdapter())
                response = s.get(
                        url,
                        timeout=self.timeout,
                        verify=self.ssl.server_verify,
                        cert=self.ssl.get_client_certs())
            else:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise PrometheusDataProviderException(e)

        return response.json()['data']['result']
