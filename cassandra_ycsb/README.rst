Cassandra workload
==================

Cassandra and YCSB job manifest
---------------------------------

Aurora job manifest supports all the `common environment variables`_. Additional variables are documented in `cassandra_ycsb.aurora`_.

.. _common environment variables: /common.aurora
.. _cassandra_ycsb.aurora: cassandra_ycsb.aurora

Cassandra & YCSB images
--------------------------

Following snippet can be used to build YCSB Docker image:

.. code-block:: sh

    docker build -f cassandra_ycsb/ycsb/Dockerfile -t 192.0.2.200/serenity/ycsb:2 .

YCSB image contains Intel patch for generating sinousiod like load.

Running a workload in Aurora cluster
------------------------------------

.. code-block:: sh

    # starting database services
    workload_uniq_id=cassandra-1 wrapper_prometheus_port=8901 name=cassandra cluster=example user=$USER env_uniq_id=0106 application_host_ip=192.0.2.100 load_generator_host_ip=192.0.2.101 cassandra_port=9042 jmx_port=7199 sh -c 'aurora job create $cluster/$user/staging$env_uniq_id/$name-$cassandra_port cassandra_ycsb.aurora'
    workload_uniq_id=cassandra-2 wrapper_prometheus_port=8902 name=cassandra cluster=example user=$USER env_uniq_id=0106 application_host_ip=192.0.2.100 load_generator_host_ip=192.0.2.101 cassandra_port=9043 jmx_port=7200 sh -c 'aurora job create $cluster/$user/staging$env_uniq_id/$name-$cassandra_port cassandra_ycsb.aurora'

    # starting load generators
    workload_uniq_id=cassandra-1 wrapper_prometheus_port=8901 name=ycsb_cassandra cluster=example user=$USER env_uniq_id=0106 application_host_ip=192.0.2.100 load_generator_host_ip=192.0.2.101 cassandra_port=9042 sh -c 'aurora job create $cluster/$user/staging$env_uniq_id/$name-$cassandra_port cassandra_ycsb.aurora'
    workload_uniq_id=cassandra-2 wrapper_prometheus_port=8902 name=ycsb_cassandra cluster=example user=$USER env_uniq_id=0106 application_host_ip=192.0.2.100 load_generator_host_ip=192.0.2.101 cassandra_port=9043 sh -c 'aurora job create $cluster/$user/staging$env_uniq_id/$name-$cassandra_port cassandra_ycsb.aurora'

