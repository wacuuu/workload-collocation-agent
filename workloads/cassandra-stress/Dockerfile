FROM cassandra
RUN ln -sfn /usr/bin/python2 /usr/bin/python
RUN apt-get update && apt-get -y upgrade
RUN apt -y install build-essential
RUN apt -y install libssl-dev zlib1g-dev libncurses5-dev libncursesw5-dev libreadline-dev libsqlite3-dev
RUN apt -y install libgdbm-dev libdb5.3-dev libbz2-dev libexpat1-dev liblzma-dev tk-dev
RUN apt -y install wget
RUN wget https://www.python.org/ftp/python/3.6.6/Python-3.6.6.tar.xz
RUN tar xf Python-3.6.6.tar.xz
WORKDIR /Python-3.6.6
RUN ./configure --enable-optimizations
RUN make -j 8
RUN make altinstall
WORKDIR /
ADD /dist/cassandra_stress_wrapper.pex /usr/bin/cassandra_stress_wrapper.pex
RUN mkdir -p /stress
ADD workloads/cassandra-stress/loop_cassandra_stress.sh /stress/loop_cassandra_stress.sh
RUN chmod +x /stress/loop_cassandra_stress.sh


