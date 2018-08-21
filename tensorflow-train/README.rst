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

All commands and scripts should be run from the top folder of the repository.

To build the image, dataset .zip file is needed in the workloads/tensorflow-train/ folder.
First, create virtual environment and activate it:

.. code-block:: sh

    python3 -m venv <PATH_TO_VENV>
    source <PATH_TO_VENV>/bin/activate

Then, install kaggle python package:

.. code-block:: sh

    pip install -r tensorflow-train/requirements.txt

prep_dataset.py script assumes that file ~/.kaggle/kaggle.json with the account token exists.
To generate such file, one has to create an account at https://www.kaggle.com/ .
To create the token, go to https://www.kaggle.com/<USERNAME>/account and press the "Create New API Token"
button. kaggle.json file will be downloaded. Move it to the folder ~/.kaggle/
Then run:

.. code-block:: sh

   python3 tensorflow-train/prep_dataset.py

After that the docker image can be built with:

.. code-block:: sh

    docker build -f tensorflow-train/Dockerfile -t tensorflow-train .

Running the workload using wrapper
----------------------------------

Example run command, when kafka server is running on host, port 9092:

.. code-block:: sh

    docker run --net="host" tensorflow-train ./wrapper.pex --command "training" --log_level DEBUG

Example of metric received in kafka:

.. code-block:: sh

    # TYPE images_processed counter
    images_processed 1.0 1534426270000

