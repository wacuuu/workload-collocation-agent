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


NODE_FREE_RESOURCES_QUERY_MAP: Dict[ResourceType, str] = {
    ResourceType.CPU: 'sum(platform_topology_cores) by (nodename) - '
    'sum(task_requested_cpus) by (nodename) or sum(platform_topology_cores) by (nodename)',
    ResourceType.MEM: 'sum(node_memory_MemTotal_bytes) by (nodename) - '
    'sum(task_requested_mem_bytes) by (nodename) or sum(node_memory_MemTotal_bytes) '
    'by (nodename)',
    ResourceType.MEMORY_BANDWIDTH_READS: 'sum(platform_nvdimm_read_bandwidth_bytes_per_second) '
    'by (nodename) - sum(platform_pmm_bandwidth_reads) by (nodename) or '
    'sum(platform_nvdimm_read_bandwidth_bytes_per_second) by (nodename)',
    ResourceType.MEMORY_BANDWIDTH_WRITES: 'sum(platform_nvdimm_write_bandwidth_bytes_per_'
    'second) by (nodename) - sum(platform_pmm_bandwidth_writes) by (nodename) or '
    'sum(platform_nvdimm_write_bandwidth_bytes_per_second) by (nodename)'
}

APP_REQUESTED_RESOURCES_QUERY_MAP: Dict[ResourceType, str] = {
        ResourceType.CPU: 'task_requested_cpus{app=%r}',
        ResourceType.MEM: 'task_requested_mem_bytes{app=%r}',
        ResourceType.MEMORY_BANDWIDTH_READS: 'max_over_time'
        '(delta(task_mb_reads__rB001{app=%r}[5s])[24h:5s])',
        ResourceType.MEMORY_BANDWIDTH_WRITES: 'max_over_time'
        '(delta(task_mb_writes__rB004{app=%r}[5s])[24h:5s])'
}


@dataclass
class PrometheusDataProvider(DataProvider):
    ip: str
    ssl: SSL = None

    def __post_init__(self):
        self.session = requests.Session()
        prometheus_adapter = requests.adapters.HTTPAdapter(max_retries=1)
        self.session.mount(self.ip, prometheus_adapter)

    def get_node_free_resources(
            self, resources: List[ResourceType]) -> Dict[str, Dict[ResourceType, float]]:

        free_resources = {}
        for resource in resources:
            results = self._do_query(NODE_FREE_RESOURCES_QUERY_MAP[resource])
            for result in results:
                node = result['metric']['nodename']
                value = result['value'][1]

                if node not in free_resources:
                    free_resources[node] = {}

                free_resources[node][resource] = value

        return free_resources

    def get_app_requested_resources(
            self, app: str, resources: List[ResourceType]) -> Dict[ResourceType, float]:

        requested_resources = {}
        for resource in resources:
            results = self._do_query(APP_REQUESTED_RESOURCES_QUERY_MAP[resource] % app)
            for result in results:
                value = result['value'][1]

                requested_resources[resource] = value

        return requested_resources

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
