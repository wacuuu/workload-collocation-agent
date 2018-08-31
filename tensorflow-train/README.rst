Tensorflow training workload
============================

Runs training of a neural net with the resnet50 architecture. Exposes a metric of the total number
of images processed during the training from the start of the workload.
Used dataset comes from https://www.kaggle.com/paultimothymooney/blood-cells/


Aurora job run and kill examples
--------------------------------

Example run

.. code-block:: sh

    load_generator_host_ip= name=tf_train cluster=example user=$USER wrapper_prometheus_port=9092 workload_uniq_id=$wrapper_prometheus_port env_uniq_id=16 workload_host_ip=192.0.2.100 sh -c 'aurora job create $cluster/$user/staging$env_uniq_id/$name-$wrapper_prometheus_port tensorflow_train.aurora'

Example kill

.. code-block:: sh

    load_generator_host_ip= name=tf_train cluster=example user=$USER wrapper_prometheus_port=9092 workload_uniq_id=$wrapper_prometheus_port env_uniq_id=16 workload_host_ip=192.0.2.100 sh -c 'aurora job killall $cluster/$user/staging$env_uniq_id/$name-$wrapper_prometheus_port'

Building docker image
---------------------

All commands and scripts should be run from the top directory of the repository. File `kaggle.json` needs to be available in this directory too (it is necessary to download image dataset from Kaggle). To obtain the file you will need to create an account at Kaggle and download API credentials as described in `documentation`_.

.. _documentation: https://github.com/Kaggle/kaggle-api#api-credentials

.. code-block:: sh

    docker build -f tensorflow-inference/Dockerfile -t tensorflow-inference .

Running the workload using wrapper
----------------------------------

Example run command, when kafka server is running on host, port 9092:

.. code-block:: sh

    docker run --net="host" tensorflow-train ./wrapper.pex --command "training" --log_level DEBUG

Example of metric received in kafka:

.. code-block:: sh

    # TYPE images_processed counter
    images_processed 1.0 1534426270000

