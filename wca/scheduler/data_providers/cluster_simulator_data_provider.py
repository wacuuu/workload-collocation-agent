"""
Module for providing.
"""
from dataclasses import dataclass
from wca.scheduler.cluster_simulator import ClusterSimulator
from wca.scheduler.data_providers import DataProvider
from wca.scheduler.types import ResourceType


@dataclass
class ClusterSimulatorDataProvider(DataProvider):
    def __repr__(self):
        return "ClusterSimulatorDataProvider"

    simulator: ClusterSimulator

    def get_node_free_space_resource(self, node: str, resource_type: ResourceType) -> float:
        node = self.simulator.get_node_by_name(node)
        if node is None:
            raise Exception('no such node')
        return node.unassigned.data[resource_type]

    def get_app_requested_resource(self, app: str, resource_type: ResourceType) -> float:
        task = self.simulator.get_task_by_name(app)
        if task is None:
            raise Exception('no such task')
        return task.requested.data[resource_type]

    def get_membw_read_write_ratio(self, node: str) -> float:
        node = self.simulator.get_node_by_name(node)
        return node.initial.data[ResourceType.MEMBW_READ] / node.initial.data[ResourceType.MEMBW_WRITE]
