===============
Workloads (gym)
===============

Description
===========

This project consists of Dockerfiles and wrappers that allow to launch a workload and expose its metrics in Prometheus format over HTTP.

Building docker images
----------------------
Docker build commands have to be run from the top project directory, for example

.. code-block:: sh

    docker build -f stress-ng/Dockerfile -t stress-ng-workload .

Building wrapper
----------------


.. code-block:: sh

    git clone https://github.intel.com/serenity/workloads
    cd workloads/wrapper

Initialize and update git submodule:

.. code-block:: sh

    git submodule update --init

Prepare virtual environment:

.. code-block:: sh

    pipenv install --dev
    pipenv shell

Then you can run tests and build package using tox.
Wrapper executable will be in ``workloads/wrapper/dist/wrapper.pex``

.. code-block:: sh

    tox

Wrapper
-------
stress-ng example:


.. code-block:: sh

    docker run -p 8080:8080 stress-ng-workload ./wrapper.pex --command "stress-ng -c 1" --log_level DEBUG --stderr 1 --prometheus_port 8080 --prometheus_ip 0.0.0.0 --labels "{'workload':'stress-ng','cores':'1'}"

Check for values with

.. code-block:: sh

   curl localhost:8080

Returned Prometheus message example:

.. code-block:: sh

    # TYPE counter counter
    counter{cores="1",workload="stress-ng"} 360.0 1533906162000

Implementing workload specific parsing function
-----------------------------------------------
Wrapper allows to provide a different implementation of the workload output parsing function. Example with dummy parsing function is in wrapper/example_workload_wrapper.py.
To use the implemented function, developer has to create his own, workload specific pex. One has to extend the tox.ini file with a new environment with different starting point, here
wrapper.example_workload_wrapper and .pex output file:

.. code-block:: sh

    [testenv:example_package]
    deps =
        pex
        -e ./rmi
    commands = pex . ./rmi -o dist/example_workload_wrapper.pex --disable-cache -m wrapper.example_workload_wrapper

Remember to extend the list of environments in tox.ini:

.. code-block:: sh

    [tox]
    envlist = flake8,unit,package,example_package

Implementation of the parsing function should return only the Metrics read from the current lines of workload output. Previous metrics should be discarded/overwritten.
