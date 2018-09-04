=========
Workloads
=========

Description
===========

This project consists of Dockerfiles and wrappers that allow to launch a workload and expose its metrics in Prometheus format over HTTP.

Building docker images
======================

Docker build commands have to be run from the top project directory, for example

.. code-block:: sh

    docker build -f stress-ng/Dockerfile -t stress-ng-workload .

Building wrapper
================

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
