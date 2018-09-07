Tensorflow inference workload
=============================

Runs prediction on images using the resnet50 neural net with pre-trained weights.
Used dataset comes from https://www.kaggle.com/moltean/fruits


Aurora job run and kill examples
--------------------------------

Aurora job manifest supports all the `common environment variables`_.
Additional variables are documented in `tensorflow_inference.aurora`_.
Please read `run_workloads.sh`_ and `config.template.sh`_
to see how to run or stop the workload.

.. _common environment variables: /workloads/common.aurora
.. _tensorflow_inference.aurora: tensorflow_inference.aurora
.. _run_workloads.sh: /run_workloads.sh
.. _config.template.sh: /config.template.sh

Building docker image
---------------------

All commands and scripts should be run from the top directory of the repository. File `kaggle.json` needs to be available in this directory too (it is necessary to download image dataset from Kaggle). To obtain the file you will need to create an account at Kaggle and download API credentials as described in `documentation`_.

.. _documentation: https://github.com/Kaggle/kaggle-api#api-credentials

.. code-block:: sh

    docker build -f workloads/tensorflow-inference/Dockerfile -t tensorflow-inference .

Running the workload using wrapper
----------------------------------

Example run command, when kafka server is running on host, port 9092:

.. code-block:: sh

    docker run --net="host" tensorflow-inference ./wrapper.pex --command "inference" --log_level DEBUG

Example of metric received in kafka:

.. code-block:: sh

    # TYPE images_processed counter
    images_processed 1.0 1534426270000

