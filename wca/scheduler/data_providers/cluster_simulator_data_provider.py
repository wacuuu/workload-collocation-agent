"""
Module for providing.
"""
from collections import defaultdict
from typing import Iterable, Dict, Tuple

from dataclasses import dataclass
from wca.scheduler.cluster_simulator import ClusterSimulator
from wca.scheduler.data_providers import DataProvider
from wca.scheduler.types import Resources, NodeName, AppsCount, ResourceType, AppName


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
        apps_per_node = {node.name: defaultdict(int) for node in self.simulator.nodes}
        unassigned_tasks = defaultdict(int)
        for task in self.simulator.tasks:
            app_name = task.get_core_name()
            if task.assignment is not None:
                node = task.assignment
                apps_per_node[node.name][app_name] += 1
            else:
                unassigned_tasks[app_name] += 1

        # remove defaultdicts
        apps_per_node_dict = {node_name:dict(apps_count) for node_name,apps_count in apps_per_node.items()}

        return apps_per_node_dict, dict(unassigned_tasks)

    def get_apps_requested_resources(self, resources: Iterable[ResourceType]) \
            -> Dict[AppName, Resources]:
        apps_requested = {}
        for node in self.simulator.nodes:
            for task in self.simulator.tasks:
                app_name = task.get_core_name()
                apps_requested[app_name] = {r: task.requested.data[r] for r in resources}
        return apps_requested
