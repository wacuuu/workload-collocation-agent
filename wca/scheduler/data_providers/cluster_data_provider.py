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
import pathlib
import requests
import os

from collections import defaultdict
from dataclasses import dataclass, field
from urllib.parse import urljoin
from typing import Iterable, Dict, Optional, List, Tuple

from wca.config import Numeric, Str, Path
from wca.kubernetes import SERVICE_TOKEN_FILENAME, SERVICE_CERT_FILENAME
from wca.resources import _MEMORY_UNITS
from wca.scheduler.data_providers import DataProvider
from wca.scheduler.types import Resources, ResourceType, NodeName, AppName
from wca.security import SSL, HTTPSAdapter

log = logging.getLogger(__name__)

QUERY_PATH = "/api/v1/query"
URL_TPL = '{prometheus_ip}{path}?query={name}'


class PrometheusDataProviderException(Exception):
    pass


@dataclass
class Prometheus:
    host: str
    port: int
    timeout: Optional[Numeric(1, 60)] = 1.0
    ssl: Optional[SSL] = None

    def do_query(self, query: str):
        url = URL_TPL.format(
                prometheus_ip='{}:{}'.format(self.host, str(self.port)),
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


@dataclass
class Kubeapi:
    host: Str = None
    port: Str = None  # Because !Env is String and another type cast might be problematic

    client_token_path: Optional[Path(absolute=True, mode=os.R_OK)] = SERVICE_TOKEN_FILENAME
    server_cert_ca_path: Optional[Path(absolute=True, mode=os.R_OK)] = SERVICE_CERT_FILENAME

    timeout: Numeric(1, 60) = 5  # [s]
    monitored_namespaces: List[Str] = field(default_factory=lambda: ["default"])

    def __post_init__(self):
        self.endpoint = "https://{}:{}".format(self.host, self.port)

        log.debug("Created kubeapi endpoint %s", self.endpoint)

        with pathlib.Path(self.client_token_path).open() as f:
            self.service_token = f.read()

    def request_kubeapi(self, target):

        full_url = urljoin(
                self.endpoint,
                target)

        r = requests.get(
                full_url,
                headers={
                    "Authorization": "Bearer {}".format(self.service_token),
                    },
                timeout=self.timeout,
                verify=self.server_cert_ca_path)

        if not r.ok:
            log.error('An unexpected error occurred for target "%s": %i %s - %s',
                      target, r.status_code, r.reason, r.raw)
        r.raise_for_status()

        return r.json()


# TODO: Consider if K8s return memory only in 'Ki' unit.
def _convert_k8s_memory_capacity(memory: str) -> int:
    return int(memory[:-2]) * _MEMORY_UNITS['Ki']


@dataclass
class ClusterDataProvider(DataProvider):
    kubeapi: Kubeapi
    prometheus: Prometheus

    def get_nodes_capacities(self, resources: Iterable[ResourceType]) -> Dict[NodeName, Resources]:
        # Check if basic resources are needed. If not, something is wrong.
        if ResourceType.CPU not in resources and ResourceType.MEM:
            # TODO: Consider to log warning rather than raising exception.
            raise Exception

        # CPU and Memory capacity source.
        kubeapi_nodes_data = list(self.kubeapi.request_kubeapi('/api/v1/nodes')['items'])

        # Get nodes names and basic resources.
        node_capacities = {
                node['metadata']['name']: {
                    ResourceType.CPU: int(node['status']['capacity']['cpu']),
                    ResourceType.MEM: _convert_k8s_memory_capacity(
                        node['status']['capacity']['memory']),
                    }
                for node in kubeapi_nodes_data
        }

        # Check if maybe more resources
        if ResourceType.MEMBW_READ in resources and ResourceType.MEMBW_WRITE in resources:
            # TODO: Calculate it.
            DRAM_MEMBW_READ_BYTES = 200 * 1e9  # +/- default for every DRAM type
            DRAM_MEMBW_WRITE_BYTES = 200 * 1e9

            # Check which nodes have PMM (in Memory Mode).
            NODES_PMM_MEMORY_MODE_QUERY = 'sum(platform_mem_mode_size_bytes) by (nodename) != 0'
            query_result = self.prometheus.do_query(NODES_PMM_MEMORY_MODE_QUERY)
            nodes_to_consider = []

            for row in query_result:
                nodes_to_consider.append(row['metric']['nodename'])

            # Every other should have only DRAM.
            for node, capacities in node_capacities.items():
                if node not in nodes_to_consider:
                    capacities[ResourceType.MEMBW_READ] = DRAM_MEMBW_READ_BYTES
                    capacities[ResourceType.MEMBW_WRITE] = DRAM_MEMBW_WRITE_BYTES

            # Read Memory Bandwidth from PMM nodes.
            if len(nodes_to_consider) > 0:

                MEMBW_READ_QUERY = \
                    'sum(platform_nvdimm_read_bandwidth_bytes_per_second) by (nodename)'
                query_result = self.prometheus.do_query(MEMBW_READ_QUERY)

                for row in query_result:
                    node = row['metric']['nodename']
                    if node in nodes_to_consider:
                        value = int(row['value'][1])
                        node_capacities[node][ResourceType.MEMBW_READ] = value
                    else:
                        continue

                MEMBW_WRITE_QUERY = \
                    'sum(platform_nvdimm_write_bandwidth_bytes_per_second) by (nodename)'
                query_result = self.prometheus.do_query(MEMBW_WRITE_QUERY)
                for row in query_result:
                    node = row['metric']['nodename']
                    if node in nodes_to_consider:
                        value = int(row['value'][1])
                        node_capacities[node][ResourceType.MEMBW_WRITE] = value
                    else:
                        continue

        log.debug('Node capacities: %r ' % node_capacities)

        return node_capacities

    def get_apps_counts(self) \
            -> Tuple[Dict[NodeName, Dict[AppName, int]], Dict[AppName, int]]:

        assigned_apps = defaultdict(lambda: defaultdict(int))
        unassigned_apps = defaultdict(int)

        for namespace in self.kubeapi.monitored_namespaces:
            target = '/api/v1/namespaces/{}/pods'.format(namespace)
            pods_data = list(self.kubeapi.request_kubeapi(target)['items'])

            for pod in pods_data:
                name = pod['metadata']['name']
                app = pod['metadata']['labels'].get('app')

                if not app:
                    log.warning('Unknown app label for pod %r' % name)
                    continue

                node = pod['spec'].get('nodeName')
                host_ip = pod['status'].get('hostIP')

                # Check if Pod is assigned.
                if not (node and host_ip):
                    unassigned_apps[app] += 1
                else:
                    assigned_apps[node][app] += 1

        log.debug(assigned_apps)

        return assigned_apps, unassigned_apps

    def get_apps_requested_resources(self, resources: Iterable[ResourceType]) \
            -> Dict[AppName, Resources]:
        pass
