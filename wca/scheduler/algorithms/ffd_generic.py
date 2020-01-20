from typing import List, Tuple

from dataclasses import dataclass

from wca.scheduler.algorithms import Algorithm
from wca.scheduler.data_providers import DataProvider
from wca.scheduler.types import ExtenderArgs, ExtenderFilterResult, HostPriority, ResourceType
from wca.scheduler.utils import extract_common_input


@dataclass
class FFDGeneric(Algorithm):
    """Fit first decreasing; supports as many dimensions as needed."""

    data_provider: DataProvider
    dimensions: Tuple[ResourceType] = (ResourceType.CPU, ResourceType.MEM,
                                      ResourceType.MEMBW,)

    def app_fit_node(self, app, node):
        return all([
            self.data_provider.get_app_requested_resource(app, resource)
            <
            self.data_provider.get_node_free_space_resource(node, resource)
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
