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
from typing import Tuple, Optional, List

from wca.scheduler.algorithms import RescheduleResult
from wca.scheduler.algorithms.base import (
        BaseAlgorithm, QueryDataProviderInfo, DEFAULT_DIMENSIONS)
from wca.scheduler.algorithms.fit import app_fits
from wca.scheduler.data_providers.creatone import CreatoneDataProvider, NodeType, AppsProfile
from wca.scheduler.types import (AppName, NodeName, ResourceType)

log = logging.getLogger(__name__)


MIN_APP_PROFILES = 2


def _get_app_node_type(
        apps_profile: AppsProfile, app_name: AppName,
        score_target: Optional[float] = None) -> NodeType:

    if len(apps_profile) > MIN_APP_PROFILES:
        if score_target:
            if app_name in apps_profile and apps_profile[app_name] >= score_target:
                return NodeType.PMEM
        else:
            sorted_apps_profile = sorted(apps_profile.items(), key=lambda x: x[1], reverse=True)
            if app_name == sorted_apps_profile[0][0]:
                return NodeType.PMEM

    return NodeType.DRAM


class Creatone(BaseAlgorithm):

    def __init__(self, data_provider: CreatoneDataProvider,
                 dimensions: List[ResourceType] = DEFAULT_DIMENSIONS,
                 max_node_score: float = 10.,
                 alias: str = None,
                 score_target: Optional[float] = None
                 ):
        super().__init__(data_provider, dimensions, max_node_score, alias)
        self.score_target = score_target

    def app_fit_node_type(self, app_name: AppName, node_name: NodeName) -> Tuple[bool, str]:
        apps_profile = self.data_provider.get_apps_profile()
        nodes_type = self.data_provider.get_nodes_type()

        node_type = nodes_type[node_name]
        app_type = _get_app_node_type(apps_profile, app_name, self.score_target)

        if node_type != app_type:
            return False, '%r not prefered for %r type of node' % (app_name, node_type)

        return True, ''

    def app_fit_node(self, node_name: NodeName, app_name: str,
                     data_provider_queried: QueryDataProviderInfo) -> Tuple[bool, str]:
        log.info('Trying to filter node %r for %r ', node_name, app_name)
        nodes_capacities, assigned_apps, apps_spec, _ = data_provider_queried

        fits, message, metrics = app_fits(
            node_name, app_name, self.dimensions,
            nodes_capacities, assigned_apps, apps_spec)

        self.metrics.extend(metrics)

        if fits:
            fits, message = self.app_fit_node_type(app_name, node_name)

        return fits, message

    def priority_for_node(self, node_name: str, app_name: str,
                          data_provider_queried: QueryDataProviderInfo) -> float:
        return 0.0

    def reschedule(self) -> RescheduleResult:
        apps_on_node, _ = self.data_provider.get_apps_counts()

        result = {}

        for node in apps_on_node:
            result[node] = []
            for app in apps_on_node[node]:
                if not self.app_fit_node_type(app, node):
                    result[node].append(apps_on_node[node][app])

        log.info('[Rescheduling] %r', result)

        return result
