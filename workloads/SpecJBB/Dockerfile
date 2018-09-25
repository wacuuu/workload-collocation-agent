# Building SpecJBB
FROM centos:7

RUN yum -y update
RUN yum install -y epel-release && yum makecache
RUN yum install -y java-1.8.0-openjdk-devel && yum install -y python36

# add the specjbb to docker
ADD workloads/SpecJBB/specjbb /home/specjbb

# add specjbb custom wrapper to docker
ADD /dist/specjbb_wrapper.pex /usr/bin/specjbb_wrapper.pex

# Note: will be ignored by mesos
WORKDIR /home/specjbb

# Notes:
# path to main executable is:
# /home/specjbb/spejbb2015.jar
# path to wrapper is:
# /usr/bin/specjbb_wrapper.pex
