from dataclasses import dataclass

from wca.scheduler.data_providers import DataProvider
from wca.scheduler.types import ResourceType
from wca.security import SSL

QUERY_PATH = "/api/v1/query"
URL_TPL = '{prometheus}{path}?query={name}'


@dataclass
class PrometheusDataProvider(DataProvider):
    ip: str
    ssl: SSL = None

    def get_node_free_space_resource(self, node: str, resource_type: ResourceType) -> float:
        pass

    def get_app_requested_resource(self, app: str, resource_type: ResourceType) -> float:
        pass

    def _do_query(self):
        pass
