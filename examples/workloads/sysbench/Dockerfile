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

FROM centos:7 as builder

RUN curl -s https://packagecloud.io/install/repositories/akopytov/sysbench/script.rpm.sh | bash
RUN yum -y install sysbench

RUN useradd -M sysbench

#RUN yum update -y
#RUN yum install -y wget && \
#    yum -y install make automake libtool pkgconfig libaio-devel && \
#    yum -y install mariadb-devel openssl-devel && \
#    yum -y install postgresql-devel
#
#RUN wget https://github.com/akopytov/sysbench/archive/1.0.18.tar.gz && \
#    tar xfz 1.0.18.tar.gz && \
#    cd ./sysbench-1.0.18 && \
#    ./autogen.sh && \
#    # Add --with-pgsql to build with PostgreSQL support
#    ./configure && \
#    make -j && \
#    make install
#
#
#FROM centos:7
#RUN yum update -y
#RUN yum install -y wget && \
#    yum install -y epel-release && \
#    yum makecache && \
#    yum install -y python36 python3-distutils
#
