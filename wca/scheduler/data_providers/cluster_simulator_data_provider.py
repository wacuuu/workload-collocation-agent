"""
Module for providing.
"""
from typing import Iterable, Dict, Tuple

from dataclasses import dataclass
from wca.scheduler.cluster_simulator import ClusterSimulator
from wca.scheduler.data_providers import DataProvider
from wca.scheduler.types import Resources, NodeName, TaskName, AppsCount, ResourceType, AppName


@dataclass
class ClusterSimulatorDataProvider(DataProvider):
    simulator: ClusterSimulator

    def get_nodes_capacities(self, resources: Iterable[ResourceType]) -> Dict[NodeName, Resources]:
        """Returns for >>nodes<< maximal capacities for >>resources<<"""
        r = {}
        for node in self.simulator.nodes:
            r[node.name] = {r: node.initial.data[r] for r in resources}
        return r

    def get_apps_counts(self) -> Tuple[Dict[NodeName, AppsCount], AppsCount]:
        apps_per_node = {}
        for node in self.simulator.nodes:
            node_name = node.name
            apps_per_node[node_name] = {}
            for task in self.simulator.tasks:
                if task.assignment == node:
                    app_name = task.get_core_name()
                    if app_name in apps_per_node[node_name]:
                        apps_per_node[node_name][app_name] += 1
                    else:
                        apps_per_node[node_name][app_name] = 1
        # @TODO is it possible to simulate unassigned apps ?
        return apps_per_node, {}

    def get_apps_requested_resources(self, resources: Iterable[ResourceType]) \
            -> Dict[AppName, Resources]:
        apps_requested = {}
        for node in self.simulator.nodes:
            for task in self.simulator.tasks:
                app_name = task.get_core_name()
                apps_requested[app_name] = {r: task.requested.data[r] for r in resources}
        return apps_requested
