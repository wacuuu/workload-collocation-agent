=======
SpecJBB
=======

To build docker image from Dockerfile you need to add specjbb into SpecJBB directory.
Specjbb is not an open source project: You need to buy a license.

User guide for specjbb: https://www.spec.org/jbb2015/docs/userguide.pdf


Building
========
Unarchive file with specjbb2015 and move the specjbb directory to SpecJBB directory of this
repository.
As a result we should have ./Specjbb/specjbb directory with, among others files, specjbb2015.jar.

Build docker image from the root directory of the repository.

To build and send to a docker registry:

.. code-block:: shell

    tag="wrapper-1.0"
    docker_registry=<ip:port>
    sudo docker build -f workloads/SpecJBB/Dockerfile -t specjbb:$tag --network=host .
    image_id=$(sudo docker images | grep "$tag"  | perl -pe 's/\s+/ /g' | cut -f3 -d' ')
    sudo docker tag $image_id $docker_registry/serenity/specjbb:$tag
    sudo docker push $docker_registry/serenity/specjbb:$tag


Running in mesos cluster
========

File specjbb.aurora is prepared for running specjbb on two nodes.
On first a controller and an injector processes will be created.
On second a backend process will be created.

Aurora job manifest supports all the `common environment variables`_.
Additional variables are documented in `specjbb.aurora`_.
Please read `run_workloads.sh`_ and `config.template.sh`_
to see how to run or stop the workload.

.. _common environment variables: /workloads/common.aurora
.. _specjbb.aurora: specjbb.aurora
.. _run_workloads.sh: /run_workloads.sh
.. _config.template.sh: /config.template.sh
