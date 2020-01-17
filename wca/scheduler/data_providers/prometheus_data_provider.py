import requests
from dataclasses import dataclass
from typing import List, Dict

from wca.scheduler.data_providers import DataProvider
from wca.scheduler.types import ResourceType
from wca.security import SSL

QUERY_PATH = "/api/v1/query"
URL_TPL = '{prometheus_ip}{path}?query={name}'


class PrometheusDataProviderException(Exception):
    pass


QUERY_MAPPING: Dict[ResourceType, str] = {
        ResourceType.CPU: 'sum(platform_topology_cores) by (nodename) - '
        'sum(task_requested_cpus) by (nodename) or sum(platform_topology_cores) by (nodename)',
        ResourceType.MEM: 'sum(node_memory_MemTotal_bytes) by (nodename) - '
        'sum(task_requested_mem_bytes) by (nodename) or sum(node_memory_MemTotal_bytes) '
        'by (nodename)',
        ResourceType.MEMBW: '',
        }


@dataclass
class PrometheusDataProvider():
    ip: str
    ssl: SSL = None

    def __post_init__(self):
        self.session = requests.Session()
        prometheus_adapter = requests.adapters.HTTPAdapter(max_retries=1)
        self.session.mount(self.ip, prometheus_adapter)

    def get_free_resources(
            self, resources: List[ResourceType]) -> Dict[str, Dict[ResourceType, float]]:

        free_resources = {}
        for resource in resources:
            results = self._do_query(QUERY_MAPPING[resource])
            for result in results:
                node = result['metric']['nodename']
                value = result['value'][1]

                if node not in free_resources:
                    free_resources[node] = {}

                free_resources[node][resource] = value

        return free_resources

    def get_requested_resources(
            self, app: str, resources: List[ResourceType]) -> Dict[ResourceType, float]:
        pass

    def _do_query(self, query: str):
        url = URL_TPL.format(
                prometheus_ip=self.ip,
                path=QUERY_PATH,
                name=query)
        try:
            response = self.session.get(url, timeout=1)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise PrometheusDataProviderException(e)

        return response.json()['data']['result']
