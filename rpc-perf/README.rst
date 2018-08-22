Memcached and rpc-perf workload
===============================

Building Docker image
=====================

.. code-block:: sh

    docker build -f rpc-perf/Dockerfile -t serenity/rpc-perf .

Running a workload in Aurora cluster
====================================

rpc-perf can be used to stress Memcached/Twemcache or Redis. Same configuration is used for both services. Aurora job manifest supports all the `common environment variables`_. Additional variables are documented in `rpc-perf.aurora`_.

.. _common environment variables: /common.aurora
.. _rpc-perf.aurora: rpc-perf.aurora

Execute following command to start a job running redis, memcached, twemcache or rpc-perf:

.. code-block:: sh

 aurora job create $cluster/$user/staging$env_uniq_id/$workload_type-$workload_uniq_id  rpc-perf/rpc-perf.aurora

Execute following command to stop a running job:

.. code-block:: sh

 aurora job create $cluster/$user/staging$env_uniq_id/$workload_type-$workload_uniq_id  rpc-perf/rpc-perf.aurora
  
See some examples of environment variables' values below:

- to control memcached you need to set following variables:

.. code-block:: sh

 workload_protocol=memcache workload_port=11211 cluster=example workload_image_tag=swan workload_type=memcached workload_address=192.0.2.100 workload_image='serenity/swan' kafka_brokers=192.0.2.200:9092 user=miwanowsk env_uniq_id=123 workload_uniq_id=456 workload_host_ip=192.0.2.100 load_generator_host_ip=192.0.2.100 

- to control rpc-perf that will send traffic to memcached instance above you need to set following variables:

.. code-block:: sh

 workload_protocol=memcache workload_port=11211 cluster=example workload_image_tag=swan workload_type=rpc-perf workload_address=192.0.2.100 workload_image='serenity/rpc-perf' kafka_brokers=192.0.2.200:9092 user=miwanowsk env_uniq_id=123 workload_uniq_id=456 workload_host_ip=192.0.2.100 load_generator_host_ip=192.0.2.100 

Example run memcached

.. code-block:: sh

    workload_host_ip=100.64.176.15 rpcperf_protocol=memcache workload_port=7000 workload_address=$workload_host_ip cluster=example workload_image_tag=swan workload_type=memcached workload_image='serenity/swan' kafka_brokers=192.0.2.200:9092 user=$USER env_uniq_id=15 workload_uniq_id=$workload_port load_generator_host_ip=$workload_host_ip sh -c 'aurora job create $cluster/$user/staging$env_uniq_id/$workload_type-$workload_uniq_id rpc-perf/rpc-perf.aurora'

Example run rpc-perf for memcached

.. code-block:: sh

    workload_host_ip=100.64.176.15 rpcperf_protocol=memcache workload_port=7000 workload_address=$workload_host_ip cluster=example workload_image_tag=swan workload_type=rpc-perf workload_image='serenity/swan' kafka_brokers=192.0.2.200:9092 user=$USER env_uniq_id=15 workload_uniq_id=$workload_port load_generator_host_ip=$workload_host_ip sh -c 'aurora job create $cluster/$user/staging$env_uniq_id/$workload_type-$workload_uniq_id rpc-perf/rpc-perf.aurora'

Example run redis

.. code-block:: sh

    workload_host_ip=100.64.176.15 rpcperf_protocol=redis workload_port=6379 workload_address=$workload_host_ip cluster=example workload_image_tag=3 workload_type=redis workload_image='serenity/redis' kafka_brokers=192.0.2.200:9092 user=$USER env_uniq_id=15 workload_uniq_id=$workload_port load_generator_host_ip=$workload_host_ip sh -c 'aurora job create $cluster/$user/staging$env_uniq_id/$workload_type-$workload_uniq_id rpc-perf/rpc-perf.aurora'

Example run rpc-perf for redis

.. code-block:: sh

    workload_host_ip=100.64.176.15 rpcperf_protocol=redis workload_port=6379 workload_address=$workload_host_ip cluster=example workload_image_tag=3 workload_type=rpc-perf workload_image='serenity/redis' kafka_brokers=192.0.2.200:9092 user=$USER env_uniq_id=15 workload_uniq_id=$workload_port load_generator_host_ip=$workload_host_ip sh -c 'aurora job create $cluster/$user/staging$env_uniq_id/$workload_type-$workload_uniq_id rpc-perf/rpc-perf.aurora'

