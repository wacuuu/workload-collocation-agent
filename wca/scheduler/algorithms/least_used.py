import logging
from typing import Tuple, Dict

from wca.logger import TRACE
from wca.metrics import Metric, MetricType
from wca.scheduler.algorithms.base import get_requested_fraction
from wca.scheduler.algorithms.fit import Fit
from wca.scheduler.data_providers import DataProvider
from wca.scheduler.metrics import MetricName
from wca.scheduler.types import ResourceType as rt

log = logging.getLogger(__name__)


class LeastUsed(Fit):
    def __init__(self, data_provider: DataProvider,
                 dimensions: List[ResourceType] = [rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE],
                 least_used_weights: Dict[rt, float] = None,
                 alias=None
                 ):
        Fit.__init__(self, data_provider, dimensions, alias=alias)
        if least_used_weights is None:
            self.least_used_weights = {dim: 1 for dim in self.dimensions}
            self.least_used_weights[rt.MEMBW_FLAT] = 1
        else:
            self.least_used_weights = least_used_weights

    def priority_for_node(self, node_name, app_name, data_provider_queried) -> float:
        """ Least used """
        nodes_capacities, assigned_apps_counts, apps_spec, unassigned_apps_counts = data_provider_queried
        requested_fraction, metrics = get_requested_fraction(
            app_name, apps_spec, assigned_apps_counts, node_name, nodes_capacities, self.dimensions)
        self.metrics.extend(metrics)

        log.log(TRACE,
                "[Prioritize][app=%s][node=%s] (requested+used) fraction ((requested+used)/capacity): %s",
                app_name, node_name, requested_fraction)

        weights = self.least_used_weights
        weights_sum = sum([weight for weight in weights.values()])
        free_fraction = {dim: 1.0 - fraction for dim, fraction in requested_fraction.items()}
        log.log(TRACE,
                "[Prioritize][app=%s][node=%s][least_used] free fraction (after new scheduling new pod) (1-requested_fraction): %s",
                app_name, node_name, free_fraction)
        log.log(TRACE, "[Prioritize][app=%s][node=%s][least_used] free fraction linear sum: %s",
                app_name, node_name, sum(free_fraction.values()))
        least_used_score = \
            sum([free_fraction * weights[dim] for dim, free_fraction in free_fraction.items()]) \
            / weights_sum
        log.debug(
            "[Prioritize][app=%s][node=%s][least_used] Least used score (weighted linear sum of free_fraction): %s",
            app_name, node_name, least_used_score)
        self.metrics.add(
            Metric(name=MetricName.BAR_LEAST_USED_SCORE,
                   value=least_used_score, labels=dict(app=app_name, node=node_name),
                   type=MetricType.GAUGE))

        return least_used_score
