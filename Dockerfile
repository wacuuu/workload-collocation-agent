# Copyright (c) 2018 Intel Corporation
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

#### Getting started
# 1. Build
# docker build -t wca:latest .

# 2. Run
# sudo docker run -it --privileged --rm wca -c /wca/configs/extra/static_measurements.yaml -0
# should output some metrics

# ------------------------ devel ----------------------
FROM centos:7 AS devel

RUN yum -y update && yum -y install python36 python-pip which make git
RUN pip3.6 install pipenv

WORKDIR /wca

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
RUN pipenv install --dev --deploy
ENV PYTHONPATH=/wca

# Cache will be propably invalidated here.
COPY wca configs example .

ENTRYPOINT ["pipenv", "run", "python3.6", "wca/main.py"]

# ------------------------ pex ----------------------
# "pex" stage includes pex file in /usr/bin/
FROM devel AS pex
# required for getting version from git-commit
COPY .git .
RUN make wca_package
RUN cp /wca/dist/wca.pex /usr/bin/
ENTRYPOINT /usr/bin/wca.pex

## ------------------------ standalone ----------------------
## Building final container that consists of wca only.
FROM centos:7 AS standalone
RUN yum -y update && yum -y install python36
COPY --from=pex /wca/dist/wca.pex /usr/bin/
ENTRYPOINT /usr/bin/wca.pex
