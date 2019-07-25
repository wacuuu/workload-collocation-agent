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

FROM ubuntu:18.04 as builder
RUN apt-get update
RUN \
  DEBIAN_FRONTEND=noninteractive \
  apt-get install -y \
    build-essential autoconf automake libpcre3-dev libevent-dev \
    pkg-config zlib1g-dev git libboost-all-dev cmake flex
RUN git clone https://github.com/RedisLabs/memtier_benchmark.git
WORKDIR /memtier_benchmark
RUN autoreconf -ivf && ./configure && make && make install

FROM ubuntu:18.04
LABEL Description="memtier_benchmark"
COPY --from=builder /usr/local/bin/memtier_benchmark /usr/local/bin/memtier_benchmark
RUN \
  apt-get update && \
  DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
      libevent-dev python3.6 python3-distutils\
  && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/

COPY /dist/memtier_benchmark_wrapper.pex /usr/bin/

ENTRYPOINT ["memtier_benchmark"]

