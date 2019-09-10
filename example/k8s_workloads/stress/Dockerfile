FROM centos:7 as stage1
RUN yum makecache
RUN yum install -y gcc make git patch libaio-devel libattr-devel libbsd-devel libcap-devel libgcrypt-devel keyutils-libs libsctp-devel zlib-devel
RUN yum install -y patch
RUN git clone https://github.com/ColinIanKing/stress-ng
WORKDIR stress-ng
RUN git checkout V0.10.04
ADD apm.patch .
RUN patch -p1 <apm.patch
RUN make -j
RUN cp stress-ng /usr/bin/stress-ng

