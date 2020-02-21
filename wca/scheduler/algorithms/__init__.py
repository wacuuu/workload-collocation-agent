# Copyright (c) 2019 Intel Corporation
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
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Set, Dict

from wca.logger import TRACE
from wca.metrics import Metric, MetricType
from wca.scheduler.data_providers import DataProvider
from wca.scheduler.metrics import MetricRegistry, MetricName
from wca.scheduler.types import ExtenderArgs, ExtenderFilterResult, HostPriority, \
    NodeName, Resources, AppsCount
from wca.scheduler.types import ResourceType as rt, AppName
from wca.scheduler.utils import extract_common_input

log = logging.getLogger(__name__)


class Algorithm(ABC):
    @abstractmethod
    def filter(self, extender_args: ExtenderArgs) -> Tuple[
        ExtenderFilterResult, List[Metric]]:
        pass

    @abstractmethod
    def prioritize(self, extender_args: ExtenderArgs) -> Tuple[
        List[HostPriority], List[Metric]]:
        pass

    @abstractmethod
    def get_metrics_registry(self) -> Optional[MetricRegistry]:
        return None

    @abstractmethod
    def get_metrics_names(self) -> List[str]:
        return []

    @abstractmethod
    def reinit_metrics(self):
        pass



QueryDataProviderInfo = Tuple[
    Dict[NodeName, Resources],  # nodes_capacities
    Dict[NodeName, AppsCount],  # assigned_apps_counts
    Dict[AppName, Resources]  # apps_spec
]


class BaseAlgorithm(Algorithm):
    """Implementing some basic functionalities which probably
       each Algorithm subclass will need to do. However forcing
       some way of implementing filtering and prioritizing which may
       not match everybody needs."""

    def __init__(self, data_provider: DataProvider,
                 dimensions: Tuple = (rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE),
                 max_node_score: float = 10,
                 alias: str = None
                 ):
        self.data_provider = data_provider
        self.dimensions = dimensions
        self.metrics = None
        self.alias = alias
        self.reinit_metrics()
        self.max_node_score = max_node_score

    def reinit_metrics(self):
        self.metrics = MetricRegistry()

    def __str__(self):
        if self.alias:
            return self.alias
        return '%s(%d)' % (self.__class__.__name__, len(self.dimensions))

    def filter(self, extender_args: ExtenderArgs) -> ExtenderFilterResult:
        log.debug('[Filter] ExtenderArgs: %r' % extender_args)
        app_name, nodes_names, namespace, name = extract_common_input(extender_args)

        extender_filter_result = ExtenderFilterResult()

        data_provider_queried = self.query_data_provider()

        for node_name in nodes_names:
            passed, message = self.app_fit_node(node_name, app_name, data_provider_queried)
            if not passed:
                log.log(TRACE, 'Failed Node %r, %r', node_name, message)
                log.debug('Failed Node %r, %r', node_name, message)
                extender_filter_result.FailedNodes[node_name] = message
            else:
                extender_filter_result.NodeNames.append(node_name)

        return extender_filter_result

    def prioritize(self, extender_args: ExtenderArgs) -> List[HostPriority]:
        app_name, nodes_names, namespace, name = extract_common_input(extender_args)

        priorities = []

        data_provider_queried = self.query_data_provider()

        if len(nodes_names) <= 1:
            return priorities

        # print('Number of nodes to prioritetize:', len(nodes_names))
        for node_name in sorted(nodes_names):
            priority = self.priority_for_node(node_name, app_name, data_provider_queried)
            priority_scaled = int(priority * self.max_node_score)
            # print(app_name, node_name, priority_scaled)
            priorities.append(HostPriority(node_name, priority_scaled))

        return priorities

    def get_metrics_registry(self) -> Optional[MetricRegistry]:
        return self.metrics

    def get_metrics_names(self) -> List[str]:
        return self.metrics.get_names()

    def query_data_provider(self) -> QueryDataProviderInfo:
        """Should be overwritten if one needs more data from DataProvider."""
        dp = self.data_provider
        assigned_apps_counts, apps_unassigned = dp.get_apps_counts()
        nodes_capacities = dp.get_nodes_capacities(self.dimensions)
        apps_spec = dp.get_apps_requested_resources(self.dimensions)
        return nodes_capacities, assigned_apps_counts, apps_spec

    @abstractmethod
    def app_fit_node(self, node_name: NodeName, app_name: str,
                     data_provider_queried: QueryDataProviderInfo) -> Tuple[bool, str]:
        """Consider if the app match the given node."""

    @abstractmethod
    def priority_for_node(self, node_name: str, app_name: str,
                          data_provider_queried: QueryDataProviderInfo) -> float:
        """Considering priority of the given node."""


def used_resources_on_node(
        dimensions: Set[rt],
        assigned_apps_counts: Dict[AppName, int],
        apps_spec: [Dict[AppName, Resources]]) -> Resources:
    """Calculate used resources on a given node using data returned by data provider."""
    used = {dim: 0 for dim in dimensions}
    for app, count in assigned_apps_counts.items():
        for dim in dimensions:
            used[dim] += apps_spec[app][dim] * count
    return used


def sum_resources(a: Resources, b: Resources) -> Resources:
    assert set(a.keys()) == set(b.keys()), \
        'the same dimensions must be provided for both resources'
    c = {}
    for resource in a.keys():
        c[resource] = a[resource] + b[resource]
    return c


def substract_resources(a: Resources, b: Resources,
                        membw_read_write_ratio: Optional[float]) -> Resources:
    assert set(a.keys()) == set(b.keys()), \
        'the same dimensions must be provided for both resources'
    dimensions = set(a.keys())

    c = a.copy()
    for dimension in dimensions:
        if dimension not in (rt.MEMBW_READ, rt.MEMBW_WRITE):
            c[dimension] = a[dimension] - b[dimension]
    if rt.MEMBW_READ in dimensions:
        assert rt.MEMBW_WRITE in dimensions
        assert type(membw_read_write_ratio) == float
        read, write = rt.MEMBW_READ, rt.MEMBW_WRITE
        c[read] = a[read] - (b[read] + b[write] * membw_read_write_ratio)
        c[write] = a[write] - (b[write] + b[read] / membw_read_write_ratio)
    return c


def calculate_read_write_ratio(capacity: Resources) -> Optional[float]:
    dimensions = capacity.keys()
    if rt.MEMBW_READ in dimensions:
        assert rt.MEMBW_WRITE in dimensions
        return float(capacity[rt.MEMBW_READ]) / float(capacity[rt.MEMBW_WRITE])
    else:
        return None


def flat_membw_read_write(a: Resources, membw_read_write_ratio: Optional[float]) -> Resources:
    """Takes >>a<< and replace rt.MEMBW_WRITE and rt.MEMBW_READ with single value rt.MEMBW_FLAT."""
    dimensions = a.keys()
    b = a.copy()
    if rt.MEMBW_READ in dimensions:
        assert rt.MEMBW_WRITE in dimensions
        assert type(membw_read_write_ratio) == float
        del b[rt.MEMBW_READ]
        del b[rt.MEMBW_WRITE]
        b[rt.MEMBW_FLAT] = a[rt.MEMBW_READ] + membw_read_write_ratio * a[rt.MEMBW_WRITE]
    return b


def divide_resources(a: Resources, b: Resources,
                     membw_read_write_ratio: Optional[float]) -> Resources:
    """Flattens rt.MEMBW_READ and rt.MEMBW_WRITE to rt.MEMBW_FLAT."""
    assert set(a.keys()) == set(b.keys()), \
        'the same dimensions must be provided for both resources'
    # must flatten membw_read_write
    if rt.MEMBW_READ in a.keys():
        a = flat_membw_read_write(a, membw_read_write_ratio)
        b = flat_membw_read_write(b, membw_read_write_ratio)

    dimensions = set(a.keys())

    c = {}
    for dimension in dimensions:
        c[dimension] = float(a[dimension]) / float(b[dimension])
    return c


def used_free_requested(
        node_name, app_name, dimensions,
        nodes_capacities, assigned_apps_counts, apps_spec,
):
    """Helper function not making any new calculations.
    All three values are returned in context of
    specified node_name and app_name.
    (Converts multiple nodes * apps to single)
    """

    capacity = nodes_capacities[node_name]
    membw_read_write_ratio = calculate_read_write_ratio(capacity)
    used = used_resources_on_node(dimensions, assigned_apps_counts[node_name], apps_spec)
    requested = apps_spec[app_name]

    # currently used and free currently
    free = substract_resources(capacity,
                               used,
                               membw_read_write_ratio)

    metrics = []
    # Metrics: resources: used, free and requested
    for resource in used:
        metrics.append(
            Metric(name=MetricName.NODE_USED_RESOURCE,
                   value=used[resource],
                   labels=dict(node=node_name, resource=resource),
                   type=MetricType.GAUGE, ))
    for resource in free:
        metrics.append(
            Metric(name=MetricName.NODE_FREE_RESOURCE,
                   value=free[resource],
                   labels=dict(node=node_name, resource=resource),
                   type=MetricType.GAUGE, ))
    for resource in requested:
        metrics.append(
            Metric(name=MetricName.APP_REQUESTED_RESOURCE,
                   value=requested[resource],
                   labels=dict(resource=resource, app=app_name),
                   type=MetricType.GAUGE, ))
    for resource in capacity:
        metrics.append(
            Metric(name=MetricName.NODE_CAPACITY_RESOURCE,
                   value=capacity[resource],
                   labels=dict(resource=resource, node=node_name),
                   type=MetricType.GAUGE))

    # Extra metric
    free_membw_flat = flat_membw_read_write(free, membw_read_write_ratio)
    if rt.MEMBW_FLAT in free_membw_flat:
        metrics.append(Metric(
            name=MetricName.FIT_PREDICTED_MEMBW_FLAT_USAGE,
            value=free_membw_flat[rt.MEMBW_FLAT],
            labels=dict(app=app_name, node=node_name),
            type=MetricType.GAUGE))

    # Requested fraction
    log.log(TRACE,
            "[Prioritize][app=%s][node=%s][least_used] Requested %s Free %s Used %s Capacity %s",
            app_name, node_name, dict(requested), free, used, nodes_capacities[node_name])
    return used, free, requested, capacity, membw_read_write_ratio, metrics
