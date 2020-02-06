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

import wca.security
import wca.databases

ssl = wca.security.SSL()
ssl.server_verify = '/tmp/zk/serverCA.crt'
ssl.client_cert_path = '/tmp/zk/client.crt'
ssl.client_key_path = '/tmp/zk/client.key'
zk = wca.databases.ZookeeperDatabase(['localhost:2281'], 'test', ssl=ssl)
zk.set(b'key', b'test')

assert zk.get(b'key') == b'test'
