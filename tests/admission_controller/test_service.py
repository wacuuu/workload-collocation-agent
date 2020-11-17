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
from wca.admission_controller.service import AnnotatingService
from wca.admission_controller.app_data_provider import AppDataProvider
from wca.prometheus import Prometheus
import base64

from unittest.mock import patch
import jsonpatch

app_data_provider = AppDataProvider(prometheus=Prometheus('127.0.0.1', 1234))
annotating_service = AnnotatingService(configuration={'data_provider': app_data_provider})


@patch('wca.admission_controller.service.AnnotatingService._get_wss', return_value=2)
@patch('wca.admission_controller.service.AnnotatingService._get_rss',
       return_value=4)
def test_mutate(rss, wss):
    request_json = {'request': {
                      'namespace': 'default',
                      'object': {
                         "apiVersion": "v1",
                         "kind": "Pod",
                         "metadata": {
                             "labels": {
                                 "app": "sysbench-memory-small",
                                 "workload": "sysbench-memory"}}}}}
    spec = request_json['request']['object']
    patched_spec = {"apiVersion": "v1",
                    "kind": "Pod",
                    "metadata": {
                        "labels": {
                            "app": "sysbench-memory-small",
                            "workload": "sysbench-memory"},
                        "annotations": {
                            "toptierlimit.cri-resource-manager.intel.com/pod": "{}G".format(2),
                            "cri-resource-manager.intel.com/memory-type": "dram,pmem"}}}
    patch = jsonpatch.JsonPatch.from_diff(spec, patched_spec)
    with annotating_service.app.test_request_context('mocked_request', json=request_json):
        output = annotating_service._mutate_pod()
        assert output.json == {
                "response": {
                    "allowed": True,
                    "status": {"message": 'Patching pod'},
                    "patch": base64.b64encode(str(patch).encode()).decode(),
                    "patchtype": "JSONPatch",
                }
            }
