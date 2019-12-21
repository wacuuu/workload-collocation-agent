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

FROM centos:7

WORKDIR /

# Install dependencies.
RUN yum -y update && yum -y install epel-release
RUN yum -y install python36

# Prepare configuration directories.
RUN mkdir -p /etc/wca-scheduler.d
RUN mkdir -p /usr/src/wca-scheduler

# Prepare wca-scheduler and configuration.
COPY dist/wca-scheduler.pex  /usr/bin/wca-scheduler.pex
COPY examples/kubernetes/wca-scheduler/wca-scheduler.conf /etc/wca-scheduler.d/wca-scheduler.conf

# Prepare NGINX server configuration.
COPY examples/kubernetes/wca-scheduler/wca-scheduler-server.conf /etc/wca-scheduler.d/wca-scheduler-server.conf

# Run wca-scheduler.
ENTRYPOINT ["wca-scheduler.pex", "wca.scheduler.main:main(\"/etc/wca-scheduler.d/wca-scheduler.conf\")", "-b unix:/usr/src/wca-scheduler/wca-scheduler.sock"]
