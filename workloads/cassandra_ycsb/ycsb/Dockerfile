FROM centos:7

RUN yum -y update && yum -y install java-1.8.0-openjdk-devel wget git patch which epel-release nc
RUN yum -y install python2-pip python36 && pip install cqlsh

# Download Apache Maven.
RUN wget -O /tmp/apache-maven-3.5.4-bin.tar.gz http://www-eu.apache.org/dist/maven/maven-3/3.5.4/binaries/apache-maven-3.5.4-bin.tar.gz

# Download YCSB orignal code.
RUN git clone --depth 1 --branch 0.14.0 https://github.com/brianfrankcooper/YCSB /opt/ycsb

# Install mvn in /opt/maven
RUN tar -C /tmp -xzf /tmp/apache-maven-3.5.4-bin.tar.gz && mv /tmp/apache-maven-3.5.4 /opt/maven

# Apply intel patch that allow to generate variable (sine-shaped) amount of QPS.
WORKDIR "/opt/ycsb"
ADD /workloads/cassandra_ycsb/ycsb/intel.patch /opt/ycsb/
RUN patch -p1 -i intel.patch

# Required for running /opt/ycsb.
RUN ln -sf /opt/maven/bin/mvn /usr/bin/mvn

# Build ycsb.
RUN /opt/maven/bin/mvn -pl com.yahoo.ycsb:core,com.yahoo.ycsb:cassandra-binding,com.yahoo.ycsb:memcached-binding -am clean package -X -Dcheckstyle.skip dependency:build-classpath -DincludeScope=compile -Dmdep.outputFilterFile=true

RUN echo 'export M2_HOME=/usr/local/maven' >> /etc/profile.d/maven.sh
RUN echo 'export PATH=${M2_HOME}/bin:${PATH}' >> /etc/profile.d/maven.sh

# Adding YCSB wrapper
ADD /dist/ycsb_wrapper.pex /usr/bin/

ENTRYPOINT ["./bin/ycsb"]
