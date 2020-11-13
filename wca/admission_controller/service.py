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
# limitations under the License

import base64
import copy
from enum import Enum
import logging
from typing import Dict, List, Optional

import jsonpatch
from flask import Flask, jsonify, request

from wca.admission_controller.app_data_provider import AppDataProvider

log = logging.getLogger(__name__)


class AnnotatingService:
    """
    """
    def __init__(self, configuration: Dict[str, str]):
        """
        self.dram_only_threshold - set to 100.0, to not use this functionality, otherwise it can
            be decided that despite having wss/rss < 100% all memory will be allocated on DRAM.
        self.cold_start_duration - whether to start the workload on PMEM memory, if memory type
            for workload is DRAM,PMEM, duration of that period if set
        self.if_toptier_limit - whether to add toptier_limit annotation
        """
        self.data_provider: AppDataProvider = configuration['data_provider']
        self.app = Flask(__name__)

        self.dram_only_threshold: float = configuration.get('dram_threshold', 100.0)
        self.cold_start_duration: Optional[int] = None
        self.if_toptier_limit: bool = True

        self.monitored_namespaces: List[str] = \
            configuration.get('monitored_namespaces', ['default'])

        @self.app.route("/mutate", methods=["POST"])
        def mutate():
            return self._mutate_pod()

    def _create_patch(self, spec, modified_spec, message='Patching pod'):
        patch = jsonpatch.JsonPatch.from_diff(spec, modified_spec)
        return jsonify(
            {
                "response": {
                    "allowed": True,
                    "status": {"message": message},
                    "patch": base64.b64encode(str(patch).encode()).decode(),
                    "patchtype": "JSONPatch",
                }
            }
        )

    def _get_wss(self, app_name) -> Optional[str]:
        wss_per_app = self.data_provider.get_wss()
        log.debug('wss={}, app={}'.format(wss_per_app, app_name))
        if app_name in wss_per_app:
            return str(wss_per_app[app_name])
        return None

    def _get_rss(self, app_name) -> Optional[str]:
        rss_per_app = self.data_provider.get_rss()
        log.debug('rss={}, app={}'.format(rss_per_app, app_name))
        if app_name in rss_per_app:
            return str(rss_per_app[app_name])
        return None

    def _get_memory_type(self, wss: str, rss: str):
        ratio = float(wss) / float(rss) * 100
        if ratio > self.dram_only_threshold:
            memory_type = MemoryType.DRAM
        else:
            memory_type = MemoryType.HMEM
        return memory_type

    def _mutate_pod(self):
        annotations_key = "annotations"
        spec = request.json["request"]["object"]
        modified_spec = copy.deepcopy(spec)
        annotations = {}

        log.debug("[_mutate_pod] modified_spec={}".format(modified_spec))
        log.debug("[_mutate_pod] request={}".format(request.json["request"]))

        if request.json["request"]["namespace"] not in self.monitored_namespaces:
            return self._create_patch(spec, modified_spec)

        app_name: str = modified_spec["metadata"]["labels"]["app"]
        wss: Optional[str] = self._get_wss(app_name)
        rss: Optional[str] = self._get_rss(app_name)

        if wss is not None:
            if self.if_toptier_limit:
                annotations.update({'toptierlimit.cri-resource-manager.intel.com/pod':
                                    '{}G'.format(wss)})

        if wss is not None and rss is not None:
            memory_type = self._get_memory_type(wss, rss)
            annotations.update({'cri-resource-manager.intel.com/memory-type': memory_type})

            if memory_type == MemoryType.HMEM and self.cold_start_duration is not None:
                annotations.update({'cri-resource-manager.intel.com/cold-start':
                                   {'duration': self.cold_start_duration}})

        if not modified_spec["metadata"].get(annotations_key) and annotations:
            modified_spec["metadata"].update({annotations_key: {}})
        if annotations:
            modified_spec["metadata"][annotations_key].update(annotations)

        return self._create_patch(spec, modified_spec)


class MemoryType(str, Enum):
    DRAM = 'dram'
    HMEM = 'dram,pmem'
