from typing import List, Tuple, Callable

import enum
from dataclasses import dataclass

from wca.scheduler.algorithms import Algorithm
from wca.scheduler.types import ExtenderArgs, ExtenderFilterResult, HostPriority
from wca.scheduler.utils import extract_common_input


class ResourceType(enum.Enum):
    MEM = 'mem'
    CPU = 'cpu'
    MEMBW = 'membw'


@dataclass
class FFDGeneric(Algorithm):
    """Fit first decreasing; supports as many dimensions as needed."""

    free_space_for_resource: Callable[[ResourceType, str], int] = None
    requested_resource_for_app: Callable[[ResourceType, str], int] = None

    resources: Tuple[ResourceType] = (ResourceType.CPU, ResourceType.MEM,
                                      ResourceType.MEMBW,)

    def app_fit_node(self, app, node):
        return all([self.requested_resource_for_app(resource, app) <
                    self.free_space_for_resource(resource, node)
                    for resource in self.resources])

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
