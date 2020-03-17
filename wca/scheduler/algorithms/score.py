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
from typing import Tuple, Optional, List, Dict

from wca.logger import TRACE
from wca.scheduler.algorithms import RescheduleResult
from wca.scheduler.algorithms.base import (
        BaseAlgorithm, QueryDataProviderInfo, DEFAULT_DIMENSIONS)
from wca.scheduler.algorithms.fit import app_fits
from wca.scheduler.data_providers.score import ScoreDataProvider, NodeType, AppsProfile
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

    def __init__(self, data_provider: ScoreDataProvider,
                 dimensions: List[ResourceType] = DEFAULT_DIMENSIONS,
                 max_node_score: float = 10.,
                 alias: str = None,
                 score_target: Optional[float] = None
                 ):
        super().__init__(data_provider, dimensions, max_node_score, alias)
        self.score_target = score_target

    def app_fit_node_type(self, app_name: AppName, node_name: NodeName) -> Tuple[bool, str]:
        apps_profile = self.data_provider.get_apps_profile()
        node_type = self.data_provider.get_node_type(node_name)

        if log.getEffectiveLevel() <= TRACE:
            log.log(TRACE, '[Filter:PMEM specific] apps_profile: \n%s', str(apps_profile))
            log.log(TRACE, '[Filter:PMEM specific] node_type: \n%s', str(node_type))

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

        # @TODO moved to app_fit_nodes
        # if fits:
        #     fits, message = self.app_fit_node_type(app_name, node_name)

        return fits, message

    def app_fit_nodes(self, node_names: List[NodeName], app_name: str,
                      data_provider_queried: QueryDataProviderInfo) -> \
            Tuple[List[NodeName], Dict[NodeName, str]]:
        """
        Return accepted and failed nodes.
        """

        # @TODO make it generic
        # if fitting node type and that node type is passed inside node_names
        if 'node101' in node_names and self.app_fit_node_type(app_name, 'node101')[0]:
            return ['node101'], {node_name: 'App match PMEM and PMEM available!'
                                 for node_name in node_names
                                 if node_name != 'node101'}

        return node_names, {}

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
