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
from dataclasses import asdict
from flask import Flask, request, jsonify
from typing import Dict

from wca.scheduler.types import ExtenderArgs


app = Flask('k8s scheduler extender')

log = logging.getLogger(__name__)


class Server:
    def __init__(self, configuration: Dict[str, str]):
        app = Flask('k8s scheduler extender')
        self.app = app
        self.algorithm = configuration['algorithm']

        @app.route('/api/scheduler/test')
        def hello():
            log.info("['/api/scheduler/test'] -> passed")
            return "Hello World"

        @app.route('/api/scheduler/filter', methods=['POST'])
        def filter():
            extender_args = ExtenderArgs(**request.get_json())
            return jsonify(asdict(self.algorithm.filter(extender_args)))

        @app.route('/api/scheduler/prioritize', methods=['POST'])
        def prioritize():
            extender_args = ExtenderArgs(**request.get_json())
            priorities = [asdict(host)
                          for host in self.algorithm.prioritize(extender_args)]
            return jsonify(priorities)

    def run(self, *args, **kwargs):
        self.app.run(*args, **kwargs)
