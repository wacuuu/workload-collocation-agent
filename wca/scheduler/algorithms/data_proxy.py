"""
Module for providing.
"""
from dataclasses import dataclass

from wca.scheduler.algorithms.ffd_generic import ResourceType
from wca.scheduler.algorithms.simulator import Simulator


@dataclass
class SimulatorDataProxy():
    simulator: Simulator

    def get_free_space_for_resource(self, resource_name: ResourceType, node: str) -> int:
        node = self.simulator.get_node_by_name(node)
        if node is None:
            raise Exception('no such node')
        if resource_name == ResourceType.CPU:
            return node.unassigned.cpu
        if resource_name == ResourceType.MEMBW:
            return node.unassigned.membw
        if resource_name == ResourceType.MEM:
            return node.unassigned.mem

    def get_requested_resource_for_app(self, resource_name: ResourceType, app: str) -> int:
        task = self.simulator.get_task_by_name(app)
        if task is None:
            raise Exception('no such task')
        if resource_name == ResourceType.CPU:
            return task.initial.cpu
        if resource_name == ResourceType.MEMBW:
            return task.initial.membw
        if resource_name == ResourceType.MEM:
            return task.initial.mem


@dataclass
class PrometheusDataProxy():
    def get_free_space_for_resource(self, resource_name: ResourceType, node: str) -> int:
        pass

    def get_requested_resource_for_app(self, resource_name: ResourceType, app: str) -> int:
        pass
