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
    sudo docker build -f SpecJBB/Dockerfile -t specjbb:$tag --network=host .
    image_id=$(sudo docker images | grep "$tag"  | perl -pe 's/\s+/ /g' | cut -f3 -d' ')
    sudo docker tag $image_id $docker_registry/serenity/specjbb:$tag
    sudo docker push $docker_registry/serenity/specjbb:$tag


Running in mesos cluster
========

File specjbb.aurora is prepared for running specjbb on two nodes.
On first a controller and an injector processes will be created.
On second a backend process will be created.

Aurora job manifest supports all the `common environment variables`_. Additional variables are documented in `specjbb.aurora`_.

.. _common environment variables: /common.aurora
.. _specjbb.aurora: specjbb.aurora

To run aurora jobs:

.. code-block:: shell

    export cluster=example
    export role=<role>
    export env_uniq_id=16  #used: last octet of IP address where backend is run (could be anything else)
    export load_generator_host_ip=<first_node_ip>
    export application_host_ip=<second_node_ip>  #backend
    export qps=1000  # setting too high qps may result in a failure of specjbb

    # Must be different for each run.
    export port_=42000 # controller listen port (below used as workload_uniq_id)
    export workload_uniq_id=$port_
    export load_generator_port=$port_

    # Note:
    # read ../common.aurora for more variables to set.

    aurora job create $cluster/$role/staging${env_uniq_id}/specjbb_controller--${workload_uniq_id} specjbb.aurora
    aurora job create $cluster/$role/staging${env_uniq_id}/specjbb_injector--${workload_uniq_id} specjbb.aurora
    aurora job create $cluster/$role/staging${env_uniq_id}/specjbb_backend--${workload_uniq_id} specjbb.aurora

To kill aurora jobs:

.. code-block:: shell

    aurora job killall $cluster/$role/staging${env_uniq_id}/specjbb_controller--${workload_uniq_id}
    aurora job killall $cluster/$role/staging${env_uniq_id}/specjbb_injector--${workload_uniq_id}
    aurora job killall $cluster/$role/staging${env_uniq_id}/specjbb_backend--${workload_uniq_id}
