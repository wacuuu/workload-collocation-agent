=====================================================
OWCA - Orchestration-Aware Workload Collocation Agent
=====================================================

Requirements
============

- Python 3.6.x
- pipenv
- tox (for CI, automatic testing)
- Centos >= 7.5


Development installation & running tests.
=========================================

.. code:: shell-session

   git clone https://github.intel.com/serenity/owca
   cd owca


Using pipenv for creating developer's environment
-------------------------------------------------


Install ``pipenv`` using "user installation" scheme:

.. code:: shell-session

    pip install --user pipenv

In case of any troubles check `pragmatic installation of pipenv.`_

.. _`pragmatic installation of pipenv.`: https://docs.pipenv.org/install/#pragmatic-installation-of-pipenv

Then prepare virtual environment for owca project.

.. code:: shell-session

   pipenv install --dev
   pipenv shell

Then you can run tests manually:

.. code:: shell-session

   PYTHONPATH=. pytest tests

Or using tox (flake8 will be run too):

.. code:: shell-session

   tox

Tip, you can use virtualenv created by pipenv in your favorite IDE.


Building executable binary (distribution)
-----------------------------------------

.. code:: shell-session

   tox -e package


Results in single distributable and executable binary in ``dist/owca.pex``.


Configuration
-------------

Available features:

- Create complex and configure python objects using `YAML tags`_ e.g. Runner, MesosNode, Storage
- Passing arguments and simple parameters type check
- Including other yaml or json files
- Register any external class with ``-r`` or by using ``owca.config.register`` decorator API

.. _`YAML tags`: http://yaml.org/spec/1.2/spec.html#id2764295

TODO: configuration: better description & more examples


External detector example
------------------------------


Before you run the example you need to:

- Have Mesos cluster set up
- Mesos operator API available at http://127.0.0.1:5051


Assuming that external implementation of detector is provided as
``external_package`` in ``example`` module and called ``ExampleDetector`` defined as:


.. code:: python

    #example/external_package.py

    from owca import detectors
    from owca import mesos
    from owca import metrics


    class ExampleDetector(detectors.AnomalyDetector):
        """Always return anomaly for given task."""

        def __init__(self, task_id: mesos.TaskId):
            self.task_id = task_id

        def detect(
                self,
                platform: Platform,
                tasks_measurements: TasksMeasurements,
                tasks_resources: TasksResources,
                tasks_labels: TasksLabels
                ) -> (List[Anomaly], List[Metric]):
            anomalies = [
                detectors.ContentionAnomaly(
                    resource=detectors.ContendedResource.CPUS
                    contended_task_id='task1',
                    contending_task_ids=['task2', 'task3']
                    metrics=[Metric(name="a_threshold", value=66.6, type="gauge")]
                )
            ]
            debugging_metrics = [
                metrics.Metric(
                    name='some_debug',
                    value=2,
                    labels=dict(
                        version=2,
                    )
                )
            ]
            return anomalies, debugging_metrics


when given config ``example.yaml`` is used:

.. code:: yaml

    runner: !DetectionRunner
      node: !MesosNode
      action_delay: 1.
      storage: !LogStorage
      detector: !ExampleDetector
        task_id: 'some_task_id'


you can run Resource Mesos Integration in following way:


.. code:: shell-session

    # dist/owca.pex -c example.yaml -r example.external_package:ExampleDetector -l debug

you will receive output:

.. code:: shell-session

    2018-07-13 14:51:32,829 DEBUG    {MainThread} [owca.logger] level=DEBUG
    2018-07-13 14:51:32,829 DEBUG    {MainThread} [owca.main] started PID=30048
    2018-07-13 14:51:32,913 DEBUG    {MainThread} [owca.storage] [Metric(name='platform_dummy', value=1, labels={}, type=None, help=None)]
    2018-07-13 14:51:32,913 DEBUG    {MainThread} [owca.storage] [Metric(name='anomaly', value=1, labels={'task_id': 'task_id', 'resource': <ContendedResource.CPUS: 'cpus'>, 'uuid': <bound method ContentionAnomaly.uuid of ContentionAnomaly(task_ids=['task_id'], resource=<ContendedResource.CPUS: 'cpus'>)>}, type=<MetricType.COUNTER: 'counter'>, help=None), Metric(name='some_debug', value=2, labels={'version': 2}, type=None, help=None)]



Register API
------------

Instead of providing class as command line parameter you can register the class explicitly in the following way:


.. code:: python

    #example_package/example_module.py

    ...
    from owca import config

    @config.register
    class ExampleDetector(detectors.AnomalyDetector):
        ...


then you can run integration by just providing config file:


.. code:: shell-session

    # dist/owca.pex -c example.yaml -l debug

Wrapper
=======

Wrapper allows to send metrics from an application to Kafka and Time-series database.

stress-ng example:


.. code-block:: sh

    docker run -p 8080:8080 stress-ng-workload ./wrapper.pex --command "stress-ng -c 1" --log_level DEBUG --stderr 1 --labels "{'workload':'stress-ng','cores':'1'}"

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
wrapper.parser_example_workload and .pex output file:

.. code-block:: sh

    [testenv:example_package]
    deps =
        pex
        -e ./owca
    commands = pex . ./owca -o dist/example_workload_wrapper.pex --disable-cache -m wrapper.parser_example_workload

Remember to extend the list of environments in tox.ini:

.. code-block:: sh

    [tox]
    envlist = flake8,unit,package,example_package

Implementation of the parsing function should return only the Metrics read from the current lines of workload output. Previous metrics should be discarded/overwritten.
Use function readline_with_check(input) instead of input.readline() to read a line from an input stream. The function raises expection StopIteration when EOF is read.

.. code-block:: sh

    #import
    from owca.wrapper.parser import readline_with_check

    #...

    # Read a line using readline_with_check(input)
    new_line = readline_with_check(input)


OWCA loggers configuration.
===========================

Command line ``--log_level (-l)`` only configures ``owca`` module by default but
it is possible to configure additional modules by specifying ``-l`` multiple times
in a form like this:

.. code-block:: shell

    ./dist/owca.pex -l debug -l example:info

Those will configure ``owca`` module to debug level and ``example`` module to info level.

If you want to quiet ``owca``, and enable verbose messages for some sub packages or
external components you can create section loggers in configuration file and
set desired level. Using configuration file will not work for messages during
objects creation (``__init__`` or ``__post_init__``) - use command line method then.

Example of specifying loggers using configuration file:

.. code-block:: yaml

    loggers:
        owca: error  # Overrides value provided from command line
        owca.storage: info  # Enables debugging for specifc owca module.
        example.external_package: debug  # Enables verbose mode for external component.

Note that, command line parameters have higher priority than configuration files.

Note: that setting level for root logger named ``""`` can enable logging with desired level for all modules including
any third party and standard library.

Please see full example of configuration in ``configs/mesos_external_detector.yaml`` for full
context.

In case of any troubles with loggers configuration, you can run application with
``OWCA_DUMP_LOGGERS=True`` environment variable to dump configuration of all loggers on standard output.


.. code-block:: shell

    OWCA_DUMP_LOGGERS=True dist/owca.pex -c configs/mesos_external_detector.yaml -r example.external_package:ExampleDetector


OWCA Kafka Consumer
===================

Overview
--------

A Kafka consumer which exposes the latest read message in its own HTTP server.


Motivation
----------

There is no official integration between Prometheus and Kafka and we need this
functionality in OWCA project.  In OWCA we send metrics already in Prometheus
format to Kafka, so the only thing developed in this project is to read them and
expose them using HTTP server to allow Prometheus to scrap the data.

