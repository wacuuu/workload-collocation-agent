import statistics

from wca.scheduler.algorithms.base import used_free_requested, divide_resources
from wca.scheduler.algorithms.fit import Fit
from wca.scheduler.types import ResourceType as rt


class HierBAR(Fit):

    def __init__(self,
                 data_provider,
                 dimensions=(rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE),
                 alias=None,
                 ):
        Fit.__init__(self, data_provider, dimensions, alias=alias)

    def priority_for_node(self, node_name, app_name, data_provider_queried) -> float:
        """
        # ---
        # BAR
        # ---
        """
        nodes_capacities, assigned_apps_counts, apps_spec, _ = data_provider_queried

        used, free, requested, capacity, membw_read_write_ratio, metrics = \
            used_free_requested(node_name, app_name, self.dimensions,
                                nodes_capacities, assigned_apps_counts, apps_spec)

        requested_empty_fraction = divide_resources(
            requested, capacity,
            membw_read_write_ratio
        )
        variance = statistics.variance(requested_empty_fraction.values())
        bar_score = (1.0 - variance)
        # print(app_name, node_name, requested_empty_fraction, variance, bar_score)
        return bar_score