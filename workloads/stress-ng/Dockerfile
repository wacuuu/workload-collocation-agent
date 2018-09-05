# Building stress-ng.
FROM centos:7 AS stress-ng

RUN yum install -y gcc git make wget patch
RUN wget http://kernel.ubuntu.com/~cking/tarballs/stress-ng/stress-ng-0.09.28.tar.xz
RUN tar -xf stress-ng-0.09.28.tar.xz
WORKDIR /stress-ng-0.09.28
ADD /workloads/stress-ng/APM.patch APM.patch
RUN cat APM.patch | patch -p 1
RUN make

# Builing final container that consists of workloads only.
FROM centos:7

RUN yum install -y epel-release
RUN yum makecache
RUN yum install -y python36
RUN useradd -M stress-ng
ADD /dist/wrapper.pex /wrapper.pex
COPY --from=stress-ng /stress-ng-0.09.28/stress-ng /usr/bin/stress-ng
