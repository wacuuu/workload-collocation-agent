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

FROM centos:7 as base
RUN yum update -y
RUN yum install -y wget \
    libtool libevent libevent-devel openssl-devel \
    autoconf automake make gcc-c++


RUN wget https://github.com/downloads/libevent/libevent/libevent-2.0.21-stable.tar.gz && \
    tar xfz libevent-2.0.21-stable.tar.gz && \
    pushd libevent-2.0.21-stable && \
    ./configure && \
    make && \
    make install && \
    popd && \
    export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:${PKG_CONFIG_PATH}

FROM base as builder
RUN yum install -y pcre-devel zlib-devel libmemcached-devel libjemalloc1 libjemalloc-dev gcc
RUN wget https://github.com/RedisLabs/memtier_benchmark/archive/1.2.17.tar.gz && \
    tar xfz 1.2.17.tar.gz && \
    cd ./memtier_benchmark-1.2.17 && \
    autoreconf -ivf && \
    ./configure && \
    make && \
    make install

RUN wget http://download.redis.io/redis-stable.tar.gz && \
    tar xvzf redis-stable.tar.gz && \
    cd redis-stable && \
    make

FROM base
RUN yum install -y epel-release && \
    yum makecache && \
    yum install -y python36 python3-distutils

RUN useradd -M memtier

COPY --from=builder /usr/local/bin/memtier_benchmark /usr/local/bin/memtier_benchmark
COPY /dist/memtier_benchmark_wrapper.pex /usr/bin/
COPY --from=builder redis-stable/src/redis-cli /usr/local/bin/

ENTRYPOINT ["memtier_benchmark"]
