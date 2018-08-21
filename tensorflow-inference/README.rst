Tensorflow inference workload
=============================

Runs prediction on images using the resnet50 neural net with pre-trained weights.
Used dataset comes from https://www.kaggle.com/moltean/fruits


Aurora job run and kill examples
--------------------------------

Example run

.. code-block:: sh

    name=tf_inference cluster=example user=$USER load_generator_host_ip= wrapper_prometheus_port=9092 workload_uniq_id=$wrapper_prometheus_port env_uniq_id=16 workload_host_ip=192.0.2.100 sh -c 'aurora job create $cluster/$user/staging$env_uniq_id/$name-$wrapper_prometheus_port tensorflow_inference.aurora'


Example kill

.. code-block:: sh

    name=tf_inference cluster=example user=$USER load_generator_host_ip= wrapper_prometheus_port=9092 workload_uniq_id=$wrapper_prometheus_port env_uniq_id=16 workload_host_ip=192.0.2.100 sh -c 'aurora job killall $cluster/$user/staging$env_uniq_id/$name-$wrapper_prometheus_port'

Building docker image
---------------------

All commands and scripts should be run from the top folder of the repository.

To build the image, dataset files are needed in the workloads/tensorflow-inference/ folder.
First, create virtual environment and activate it:

.. code-block:: sh

    python3 -m venv <PATH_TO_VENV>
    source <PATH_TO_VENV>/bin/activate

Then, install kaggle python package:

.. code-block:: sh

    pip install -r tensorflow-inference/requirements.txt

prep_dataset_fruits.py script assumes that file ~/.kaggle/kaggle.json with the account token exists.
To generate such file, one has to create an account at https://www.kaggle.com/ .
To create the token, go to https://www.kaggle.com/<USERNAME>/account and press the "Create New API Token"
button. kaggle.json file will be downloaded. Move it to the folder ~/.kaggle/
Then run:

.. code-block:: sh

   python3 tensorflow-inference/prep_dataset_fruits.py

After that the docker image can be built with:

.. code-block:: sh

    docker build -f tensorflow-inference/Dockerfile -t tensorflow-inference .

Running the workload using wrapper
----------------------------------

Example run command, when kafka server is running on host, port 9092:

.. code-block:: sh

    docker run --net="host" tensorflow-inference ./wrapper.pex --command "inference" --log_level DEBUG

Example of metric received in kafka:

.. code-block:: sh

    # TYPE images_processed counter
    images_processed 1.0 1534426270000

