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

from dataclasses import dataclass, field
from urllib.parse import urljoin
from typing import Iterable, Dict, Optional, List

from wca.config import Numeric, Str, Path
from wca.kubernetes import SERVICE_TOKEN_FILENAME, SERVICE_CERT_FILENAME
from wca.resources import _MEMORY_UNITS
from wca.scheduler.data_providers import DataProvider
from wca.scheduler.types import Resources, ResourceType, NodeName, TaskName
from wca.security import SSL, HTTPSAdapter

log = logging.getLogger(__name__)

QUERY_PATH = "/api/v1/query"
URL_TPL = '{prometheus_ip}{path}?query={name}'


class PrometheusDataProviderException(Exception):
    pass


@dataclass
class Prometheus:
    ip: str
    timeout: Optional[Numeric(1, 60)] = 1.0
    ssl: Optional[SSL] = None

    def do_query(self, query: str):
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


@dataclass
class Kubeapi:
    kubeapi_host: Str = None
    kubeapi_port: Str = None  # Because !Env is String and another type cast might be problematic

    client_token_path: Optional[Path(absolute=True, mode=os.R_OK)] = SERVICE_TOKEN_FILENAME
    server_cert_ca_path: Optional[Path(absolute=True, mode=os.R_OK)] = SERVICE_CERT_FILENAME

    timeout: Numeric(1, 60) = 5  # [s]
    monitored_namespaces: List[Str] = field(default_factory=lambda: ["default"])

    def __post_init__(self):
        self.kubeapi_endpoint = "https://{}:{}".format(self.kubeapi_host, self.kubeapi_port)

        log.debug("Created kubeapi endpoint %s", self.kubeapi_endpoint)

        with pathlib.Path(self.client_token_path).open() as f:
            self.service_token = f.read()

    def request_kubeapi(self, target):

        full_url = urljoin(
                self.kubeapi_endpoint,
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
    return int(memory[:-2] * _MEMORY_UNITS['Ki'])


@dataclass
class ClusterDataProvider(DataProvider):
    kubeapi: Kubeapi
    prometheus: Prometheus

    def get_nodes_capacities(self, resources: Iterable[ResourceType]) -> Dict[NodeName, Resources]:
        node_capacities = {}

        # Cpu and Memory capacity source.
        kubeapi_nodes_data = list(self.kubeapi.request_kubeapi('/api/v1/nodes')['items'])

        # Get nodes names and basic resources.
        node_capacities = {
                node['metadata']['name']: {
                    ResourceType.CPU: int(node['status']['capacity']['cpu']),
                    ResourceType.MEM: _convert_k8s_memory_capacity(
                        node['status']['capacity']['memory'])
                    }
                for node in kubeapi_nodes_data
        }

        # Get prometheus metrics.

        # TODO: Implementation.
        if ResourceType.MEMBW in resources:
            pass

        return node_capacities

    def get_assigned_tasks_requested_resources(
            self, resources: Iterable[ResourceType],
            nodes: Iterable[NodeName]) -> Dict[NodeName, Dict[TaskName, Resources]]:
        """Return for all >>nodes<< all tasks requested >>resources<< assigned to them."""
        pass

    def get_app_requested_resources(self, resources: Iterable[ResourceType], app: str) -> Resources:
        """Returns for >>app<< requested resources; if a dimension cannot be read from kubernetes metadata,
           use some kind of approximation for maximal value needed for a dimension."""
        pass

    def get_node_membw_read_write_ratio(self, node: str) -> float:
        """For DRAM only node should return 1."""
        pass
