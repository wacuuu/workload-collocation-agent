Twemcache and rpc-perf workload
===============================

Building Docker image
=====================

.. code-block:: sh

    docker build -f workloads/rpc-perf/Dockerfile -t serenity/rpc-perf .

Running a workload in Aurora cluster
====================================

rpc-perf can be used to stress Twemcache or Redis.

Aurora job manifest supports all the `common environment variables`_.
Additional variables are documented in `rpc_perf.aurora`_.
Please read `run_workloads.sh`_ and `config.template.sh`_
to see how to run or stop the workload.

.. _common environment variables: /workloads/common.aurora
.. _rpc_perf.aurora: rpc-perf.aurora
.. _run_workloads.sh: /run_workloads.sh
.. _config.template.sh: /config.template.sh
