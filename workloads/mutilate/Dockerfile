FROM ubuntu:trusty

RUN apt-get update && apt-get install -qy scons libevent-dev gengetopt libzmq-dev git g++

RUN ln -sfn /usr/bin/python2 /usr/bin/python
RUN apt -y install wget
RUN apt-get -y install zlib1g-dev build-essential

WORKDIR /opt
RUN wget https://www.python.org/ftp/python/3.6.6/Python-3.6.6.tgz
RUN tar -xvf Python-3.6.6.tgz
WORKDIR /opt/Python-3.6.6
RUN ./configure
RUN make
RUN make install

WORKDIR /
RUN git clone https://github.com/Bplotka/mutilate.git

WORKDIR mutilate

RUN git checkout masterless && scons

ADD /dist/mutilate_wrapper.pex /usr/bin/mutilate_wrapper.pex
ADD workloads/mutilate/loop_mutilate.sh /mutilate/loop_mutilate.sh
RUN chmod +x /mutilate/loop_mutilate.sh

