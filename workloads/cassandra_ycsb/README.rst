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

    docker build -f workloads/cassandra_ycsb/ycsb/Dockerfile -t 192.0.2.200/serenity/ycsb:2 .

YCSB image contains Intel patch for generating sinusoid like load.

Running a workload in Aurora cluster
------------------------------------

Aurora job manifest supports all the `common environment variables`_.
Additional variables are documented in `cassandra_ycsb.aurora`_.
Please read `run_workloads.sh`_ and `config.template.sh`_
to see how to run or stop the workload.

.. _common environment variables: /workloads/common.aurora
.. _cassandra_ycsb.aurora: cassandra_ycsb.aurora
.. _run_workloads.sh: /run_workloads.sh
.. _config.template.sh: /config.template.sh
