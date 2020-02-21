# Copyright (c) 2020 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from typing import Tuple, Dict, Any

from wca.logger import TRACE
from wca.metrics import Metric, MetricType
from wca.scheduler.algorithms.base import sum_resources, divide_resources, \
    used_free_requested
from wca.scheduler.algorithms.fit import Fit
from wca.scheduler.data_providers import DataProvider
from wca.scheduler.metrics import MetricName
from wca.scheduler.types import ResourceType as rt

log = logging.getLogger(__name__)


# @dataclass
# class MaxNodeScore(Fit):
#     algo: BaseAlgorithm
#     max_node_score: float = 1
#
#     def priority_for_node(self, node_name, app_name, data_provider_queried) -> float:
#         return self.algo.priority_for_node(node_name, app_name,
#                                            data_provider_queried) * self.max_node_score


def get_requested_fraction(app_name, apps_spec, assigned_apps_counts, node_name,
                           nodes_capacities, dimensions):
    # Current node context: used and free currently
    used, free, requested, capacity, membw_read_write_ratio, metrics = \
        used_free_requested(node_name, app_name, dimensions,
                            nodes_capacities, assigned_apps_counts, apps_spec)

    # FRACTION
    requested_fraction = divide_resources(
        sum_resources(requested, used), capacity,
        membw_read_write_ratio
    )
    for resource, fraction in requested_fraction.items():
        metrics.append(
            Metric(name=MetricName.BAR_REQUESTED_FRACTION,
                   value=fraction, labels=dict(app=app_name, resource=resource),
                   type=MetricType.GAUGE))
    log.log(TRACE,
            "[Prioritize][app=%s][node=%s][least_used] (requested+used) fraction ((requested+used)/capacity): %s",
            app_name, node_name, requested_fraction)
    return requested_fraction, metrics


class LeastUsed(Fit):
    def __init__(self, data_provider: DataProvider,
                 dimensions: Tuple = (rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE),
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
        """
        # ----------
        # Least used
        # ----------
        """
        nodes_capacities, assigned_apps_counts, apps_spec = data_provider_queried
        requested_fraction, metrics = get_requested_fraction(
            app_name, apps_spec, assigned_apps_counts, node_name, nodes_capacities, self.dimensions)
        self.metrics.extend(metrics)

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
        log.log(TRACE,
                "[Prioritize][app=%s][node=%s][least_used] Least used score (weighted linear sum of free_fraction): %s",
                app_name, node_name, least_used_score)
        self.metrics.add(
            Metric(name=MetricName.BAR_LEAST_USED_SCORE,
                   value=least_used_score, labels=dict(app=app_name, node=node_name),
                   type=MetricType.GAUGE))

        return least_used_score


class BAR(Fit):
    def __init__(self,
                 data_provider,
                 dimensions=(rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE),
                 bar_weights: Dict[rt, float] = None,
                 alias=None,
                 ):
        Fit.__init__(self, data_provider, dimensions, alias=alias)
        self.bar_weights = bar_weights or {}

    def priority_for_node(self, node_name, app_name, data_provider_queried) -> float:
        """
        # ---
        # BAR
        # ---
        """
        nodes_capacities, assigned_apps_counts, apps_spec = data_provider_queried
        requested_fraction, metrics = get_requested_fraction(
            app_name, apps_spec, assigned_apps_counts, node_name, nodes_capacities, self.dimensions)
        self.metrics.extend(metrics)

        # Mean - priority according to variance of dimensions
        mean = sum([v for v in requested_fraction.values()]) / len(requested_fraction)
        log.log(TRACE, "[Prioritize][app=%s][node=%s][bar] Mean: %s", app_name, node_name, mean)
        self.metrics.add(
            Metric(name=MetricName.BAR_MEAN,
                   value=mean, labels=dict(app=app_name, node=node_name),
                   type=MetricType.GAUGE))

        # Variance
        if len(requested_fraction) > 2:
            variance = sum([((fraction - mean) * (fraction - mean)) * self.bar_weights.get(rt, 1)
                            for rt, fraction in requested_fraction.items()]) \
                       / len(requested_fraction)
        elif len(requested_fraction) == 2:
            values = list(requested_fraction.values())
            variance = abs(values[0] - values[1])
        else:
            variance = 0

        log.log(TRACE,
                "[Prioritize][app=%s][node=%s][bar] Variance(weighted quadratic sum of requested_fraction-mean): %s",
                app_name, node_name, variance)
        self.metrics.add(
            Metric(name=MetricName.BAR_VARIANCE,
                   value=variance, labels=dict(app=app_name, node=node_name),
                   type=MetricType.GAUGE))

        bar_score = (1.0 - variance)
        log.log(TRACE, "[Prioritize][app=%s][node=%s][bar] Bar score: %s", app_name, node_name,
                bar_score)
        self.metrics.add(
            Metric(name=MetricName.BAR_SCORE,
                   value=bar_score, labels=dict(app=app_name, node=node_name),
                   type=MetricType.GAUGE))

        return bar_score


class LeastUsedBAR(LeastUsed, BAR):
    def __init__(self, data_provider: DataProvider,
                 dimensions: Tuple = (rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE),
                 least_used_weights: Dict[rt, float] = None,
                 bar_weights: Dict[rt, float] = None,
                 least_used_weight=1,
                 alias=None,
                 max_node_score: float = 10,
                 ):
        LeastUsed.__init__(self, data_provider, dimensions, least_used_weights, alias=alias)
        BAR.__init__(self, data_provider, dimensions, bar_weights)
        self.least_used_weight = least_used_weight

    def __str__(self):
        if self.alias:
            return super().__str__()
        return '%s(%d,luw=%.2f)' % (self.__class__.__name__, len(self.dimensions),
                                    self.least_used_weight)

    def priority_for_node(self, node_name: str, app_name: str,
                          data_provider_queried: Tuple[Any]) -> float:
        least_used_score = LeastUsed.priority_for_node(self, node_name, app_name,
                                                       data_provider_queried)
        bar_score = BAR.priority_for_node(self, node_name, app_name, data_provider_queried)
        # ---
        # Putting together Least-used and BAR.
        # ---
        result = least_used_score * self.least_used_weight + bar_score
        log.log(
            TRACE, "[Prioritize][app=%s][node=%s] least_used_score=%s"
                   " bar_score=%s least_used_weight=%s result=%s",
            app_name, node_name, least_used_score, bar_score, self.least_used_weight, result)
        self.metrics.add(
            Metric(name=MetricName.BAR_RESULT,
                   value=result, labels=dict(app=app_name, node=node_name),
                   type=MetricType.GAUGE))

        return result
