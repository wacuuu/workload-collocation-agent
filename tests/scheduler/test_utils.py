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
# from typing import Dict

# from wca.scheduler.utils import extract_common_input
# from wca.scheduler.types import ExtenderArgs

# FIXTURE = 'tests/fixtures/kube-scheduler-request.json'

# extender_args = None

# with open(FIXTURE) as f:
#     response: Dict = f.read()

#     extender_args = ExtenderArgs(
#         Nodes=response.get('Nodes', []),
#         Pod=response.get('Pod', {}),
#         NodeNames=response.get('NodeNames', []))


# def test_extract_common_input(extender_args, expected):
#     assert expected == extract_common_input(extender_args)
