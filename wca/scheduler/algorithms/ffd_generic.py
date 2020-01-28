from typing import List, Tuple

from dataclasses import dataclass

from wca.scheduler.algorithms import Algorithm
from wca.scheduler.data_providers import DataProvider
from wca.scheduler.types import ExtenderArgs, ExtenderFilterResult, HostPriority, ResourceType, Dict
from wca.scheduler.utils import extract_common_input


@dataclass
class FFDGeneric(Algorithm):
    """Fit first decreasing; supports as many dimensions as needed."""

    data_provider: DataProvider
    dimensions: Tuple[ResourceType] = (ResourceType.CPU, ResourceType.MEM, ResourceType.MEMBW,)

    def app_fit_node(self, app, node):
        dp = self.data_provider  # for shortening notation
        return all([dp.get_app_requested_resource(app, resource) <
                    dp.get_node_free_space_resource(node, resource)
                    for resource in self.dimensions])

    def filter(self, extender_args: ExtenderArgs) -> ExtenderFilterResult:
        app, nodes, namespace, name = extract_common_input(extender_args)
        extender_filter_result = ExtenderFilterResult()

        for i, node in enumerate(nodes):
            if not self.app_fit_node(app, node):
                extender_filter_result.FailedNodes[node] = "Not enough resources."

        return extender_filter_result

    def prioritize(self, extender_args: ExtenderArgs) -> List[HostPriority]:
        app, nodes, namespace, name = extract_common_input(extender_args)
        # choose node which has the most free resources
        return []


@dataclass
class FFDGeneric_AsymetricMembw(Algorithm):
    """Fit first decreasing; supports as many dimensions as needed."""

    data_provider: DataProvider
    dimensions: Tuple[ResourceType] = (ResourceType.CPU, ResourceType.MEM,
                                       ResourceType.MEMBW_WRITE, ResourceType.MEMBW_READ)

    @staticmethod
    def basic_check(app_requested: Dict[ResourceType, int], node_free_space: Dict[ResourceType, int]) -> bool:
        return all([app_requested[resource] < node_free_space[resource] for resource in self.dimensions])

    @staticmethod
    def membw_check(app_requested: Dict[ResourceType, int],
                    node_free_space: Dict[ResourceType, int],
                    node_membw_read_write_ratio: float) -> bool:
        """
        read/write ratio, e.g. 40GB/s / 10GB/s = 4,
        what means reading is 4 time faster
        """

        # Assert that required dimensions are available.
        for resource in (ResourceType.MEMBW_WRITE, ResourceType.MEMBW_READ,):
            for source in (app_requested, node_free_space, node_max_aep_bandwidth):
                assert resource in source

        # To shorten the notation.
        WRITE = ResourceType.MEMBW_WRITE
        READ = ResourceType.MEMBW_READ
        requested = app_requested
        node = node_free_space
        ratio = node_membw_read_write_ratio

        return (node[READ] - requested[READ] - requested[WRITE] * ratio) > 0 and \
               (node[WRITE] - requested[WRITE] - requested[READ] / ratio) > 0

    def app_fit_node(self, app, node):
        dp = self.data_provider

        app_requested   = {resource: self.data_provider.get_app_requested_resource(app, resource) 
                           for resource in self.dimensions}
        node_free_space = {resource: self.data_provider.get_node_free_space_resource(node, resource) 
                           for resource in self.dimensions}

        if not basic_check(app_requested, node_free_space):
            return False

        node_membw_read_write_ratio = self.data_provider.get_membw_read_write_ratio()

        return membw_check(app_requested, node_free_space, node_membw_read_write_ratio)

    def filter(self, extender_args: ExtenderArgs) -> ExtenderFilterResult:
        app, nodes, namespace, name = extract_common_input(extender_args)
        extender_filter_result = ExtenderFilterResult()

        for i, node in enumerate(nodes):
            if not self.app_fit_node(app, node):
                extender_filter_result.FailedNodes[node] = "Not enough resources."

        return extender_filter_result

    def prioritize(self, extender_args: ExtenderArgs) -> List[HostPriority]:
        app, nodes, namespace, name = extract_common_input(extender_args)
        # choose node which has the most free resources
        return []
