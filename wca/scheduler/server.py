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
from dataclasses import asdict
from flask import Flask, request, jsonify
from typing import Dict

from wca.scheduler.types import ExtenderArgs, ExtenderFilterResult

log = logging.getLogger(__name__)

DEFAULT_NAMESPACE = 'default'


class Server:
    def __init__(self, configuration: Dict[str, str]):
        self.app = Flask('k8s scheduler extender')
        self.algorithm = configuration['algorithm']

        @self.app.route('/status')
        def status():
            log.debug('[Status]')
            return jsonify('running')

        @self.app.route('/filter', methods=['POST'])
        def filter():
            extender_args = ExtenderArgs(**request.get_json())
            log.debug('[Filter] %r ' % extender_args)

            if DEFAULT_NAMESPACE == extender_args.Pod['metadata']['namespace']:
                return jsonify(asdict(self.algorithm.filter(extender_args)))
            else:
                log.info('[Filter] Ignoring Pod %r : Different namespace!' %
                         extender_args.Pod['metadata']['name'])
                return jsonify(ExtenderFilterResult(NodeNames=extender_args.NodeNames))

        @self.app.route('/prioritize', methods=['POST'])
        def prioritize():
            extender_args = ExtenderArgs(**request.get_json())
            log.debug('[Prioritize] %r ' % extender_args)

            if DEFAULT_NAMESPACE == extender_args.Pod['metadata']['namespace']:
                priorities = [asdict(host)
                              for host in self.algorithm.prioritize(extender_args)]
                return jsonify(priorities)
            else:
                log.info('[Prioritize] Ignoring Pod %r : Different namespace!' %
                         extender_args.Pod['metadata']['name'])
                return jsonify([])
