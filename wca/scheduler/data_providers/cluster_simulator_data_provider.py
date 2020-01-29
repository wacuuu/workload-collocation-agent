"""
Module for providing.
"""
from typing import Iterable, Dict

from dataclasses import dataclass
from wca.scheduler.cluster_simulator import ClusterSimulator
from wca.scheduler.data_providers import DataProvider
from wca.scheduler.types import ResourceType, Resources, NodeName, TaskName


@dataclass
class ClusterSimulatorDataProvider(DataProvider):
    simulator: ClusterSimulator

    def get_nodes_capacities(self, resources: Iterable[ResourceType]) -> Dict[NodeName, Resources]:
        """Returns for >>nodes<< maximal capacities for >>resources<<"""
        r = {}
        for node in self.simulator.nodes:
            r[node.name] = {r: node.initial.data[r] for r in resources}
        return r

    def get_assigned_tasks_requested_resources(
            self, resources: Iterable[ResourceType], nodes: Iterable[NodeName]) -> Dict[NodeName, Dict[TaskName, Resources]]:
        """Return for all >>nodes<< all tasks requested >>resources<< assigned to them."""
        r = {}
        for node in self.simulator.nodes:
            r[node.name] = {}
            for task in self.simulator.tasks:
                if task.assignment == node:
                    r[node.name][task.name] = {r: task.requested.data[r] for r in resources}
        return r

    def get_app_requested_resources(self, resources: Iterable[ResourceType], app: str) -> Resources:
        """Returns for >>app<< requested resources; if a dimension cannot be read from kubernetes metadata,
           use some kind of approximation for maximal value needed for a dimension."""
        task = self.simulator.get_task_by_name(app)
        if task is None:
            raise Exception('no such task')
        return {resource_type: task.requested.data[resource_type] for resource_type in resources}

    def get_node_membw_read_write_ratio(self, node: str) -> float:
        node = self.simulator.get_node_by_name(node)
        return node.initial.data[ResourceType.MEMBW_READ] / node.initial.data[ResourceType.MEMBW_WRITE]
