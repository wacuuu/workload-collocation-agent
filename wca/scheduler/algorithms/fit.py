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
from typing import Tuple, List

from wca.metrics import Metric
from wca.scheduler.algorithms import DataMissingException, RescheduleResult
from wca.scheduler.algorithms.base import BaseAlgorithm, sum_resources, subtract_resources, \
    used_free_requested, QueryDataProviderInfo, calculate_read_write_ratio
from wca.scheduler.cluster_simulator import Resources

log = logging.getLogger(__name__)


def enough_resources_on_node(capacity, used, membw_read_write_ratio):
    free = subtract_resources(
        capacity,
        used,
        membw_read_write_ratio,
    )

    # CHECK
    broken_capacities = {r: abs(v) for r, v in free.items() if v < 0}

    return not bool(broken_capacities), broken_capacities, free


def app_fits(node_name, app_name, dimensions, nodes_capacities,
             assigned_apps, apps_spec) -> Tuple[bool, str, List[Metric]]:
    # Current node context: used and free currently
    used, free, requested, capacity, membw_read_write_ratio, metrics = \
        used_free_requested(node_name, app_name, dimensions,
                            nodes_capacities, assigned_apps, apps_spec)
    metrics.extend(metrics)

    # SUBTRACT: "free" after simulated assigment of requested
    try:
        requested_and_used = sum_resources(requested, used)
    except ValueError as e:
        msg = 'cannot sum app=%s requested=%s and node=%s used=%s: %s' % (
            app_name, requested, node_name, used, e)
        log.error(msg)
        raise DataMissingException(msg) from e

    fits, broken_capacities, free = enough_resources_on_node(
        capacity, requested_and_used, membw_read_write_ratio)
    if fits:
        log.debug('[Filter][app=%s][node=%s] ok free_after_bind=%r',
                  app_name, node_name, free)
        message = ''
    else:
        broken_capacities_str = \
            ','.join(['({}: {})'.format(r, v) for r, v in broken_capacities.items()])
        log.debug('[Filter][app=%s][node=%s] broken capacities: missing %r',
                  app_name, node_name, broken_capacities_str)
        message = 'Could not fit node for dimensions: missing {}.'.format(
            broken_capacities_str)

    return fits, message, metrics


class Fit(BaseAlgorithm):
    """Filter all nodes where the scheduled app does not fit.
       Supporting any number of dimensions.
       Treats MEMBW_READ and MEMBW_WRITE differently than other dimensions."""

    def app_fit_node(self, node_name, app_name, data_provider_queried) -> Tuple[bool, str]:
        nodes_capacities, assigned_apps, apps_spec, _ = data_provider_queried
        fits, message, metrics = app_fits(
            node_name, app_name, self.dimensions,
            nodes_capacities, assigned_apps, apps_spec)
        self.metrics.extend(metrics)
        return fits, message

    def priority_for_node(self, node_name: str, app_name: str,
                          data_provider_queried: Tuple) -> float:
        """no prioritization method for FitGeneric"""
        return 0.0

    def reschedule_with_metrics(self, data_provider_queried: QueryDataProviderInfo,
                                ) -> Tuple[RescheduleResult, List[Metric]]:
        """Fit pods that over-allocate available resources and remove them.

        We're going to remove from every over-used node the applications with
        most multiple copies.
        """

        nodes_capacities, assigned_apps, apps_spec, unassigned_apps_count = data_provider_queried

        reschedule_result: RescheduleResult = {}

        for node_name, capacity in nodes_capacities.items():
            apps_count = assigned_apps.get(node_name, {})
            used = Resources.create_empty(self.dimensions).data
            if apps_count:
                # sorted by count, last app_name will be the most assigned to node
                app_name, apps = None, {}
                for app_name, apps in sorted(apps_count.items(), key=lambda x: x[1]):
                    app_resource = apps_spec[app_name]
                    used = sum_resources(used, app_resource)

                membw_read_write_ratio = calculate_read_write_ratio(capacity)
                fits, broken_capacities, free = enough_resources_on_node(
                    capacity, used, membw_read_write_ratio)

                if app_name and not fits:
                    # Try to remove last app from node (just one)
                    reschedule_result[node_name] = {app_name: apps}
                    log.debug('found app=%r (count=%d) to reschedule because of fit', app_name,
                              apps)

        return reschedule_result, []
