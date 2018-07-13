==========================
Resource Mesos Integration
==========================

Requirements
============

- Python 3.6.x
- pipenv
- tox (for CI, automatic testing)
- Centos >= 7.5


Development installation & running tests.
=========================================

.. code:: shell-session

   git clone https://github.intel.com/serenity/rmi
   cd rmi


Using pipenv for creating developer's environment
-------------------------------------------------


Install ``pipenv`` using "user installation" scheme:

.. code:: shell-session

    pip install --user pipenv

In case of any troubles check `pragmatic installation of pipenv.`_

.. _`pragmatic installation of pipenv.`: https://docs.pipenv.org/install/#pragmatic-installation-of-pipenv

Then prepare virtual environment for rmi project.

.. code:: shell-session

   pipenv install --dev
   pipenv run python setup.py test

   # or from virtualenv
   pipenv shell
   PYTHONPATH=. pytest tests
   tox
   
Tip, you can use virtualenv created by pipenv in your favorite IDE.

Using tox
---------

You can use tox to run unittests and check code style with flake8.
Notice that after using pipenv install you have already tox in your virtual environment.


.. code:: shell-session

   tox


Configuration
-------------

Available features: 

- Create complex and configure python objects using `YAML tags`_ e.g. Runner, MesosNode, Storage
- Passing arguments and simple parameters type check
- Including other yaml or json files
- Register any external class with ``-r`` or by using ``rmi.config.register`` decorator API 

.. _`YAML tags`: http://yaml.org/spec/1.2/spec.html#id2764295

TODO: configuration: better description & more examples


External detector example
------------------------------


Before you run the example you need to: 

- Have Mesos cluster set up
- Mesos operator API available at http://127.0.0.1:5051
- Install the project:


.. code:: shell
   
    pip install -e .


Assuming that external implementation of detector is provided as
``external_package`` in ``example`` module and called ``ExampleDetector`` defined as:


.. code:: python

    #example/external_package.py

    from rmi import detectors
    from rmi import mesos
    from rmi import metrics


    class ExampleDetector(detectors.AnomalyDectector):
        """Always return anomaly for given task."""

        def __init__(self, task_id: mesos.TaskId):
            self.task_id = task_id

        def detect(self, platform, task_measurements):
            anomalies = [
                detectors.Anomaly(
                    task_ids=['task_id'], 
                    resource=detectors.ContendedResource.CPUS
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

    # rmi -c example.yaml -r example.external_package:ExampleDetector -l debug

you will receive output:

.. code:: shell-session

    2018-07-13 14:51:32,829 DEBUG    {MainThread} [rmi.logger] level=DEBUG
    2018-07-13 14:51:32,829 DEBUG    {MainThread} [rmi.main] started PID=30048
    2018-07-13 14:51:32,913 DEBUG    {MainThread} [rmi.storage] [Metric(name='platform_dummy', value=1, labels={}, type=None, help=None)]
    2018-07-13 14:51:32,913 DEBUG    {MainThread} [rmi.storage] [Metric(name='anomaly', value=1, labels={'task_id': 'task_id', 'resource': <ContendedResource.CPUS: 'cpus'>, 'uuid': <bound method Anomaly.uuid of Anomaly(task_ids=['task_id'], resource=<ContendedResource.CPUS: 'cpus'>)>}, type=<MetricType.COUNTER: 'counter'>, help=None), Metric(name='some_debug', value=2, labels={'version': 2}, type=None, help=None)]



Register API
------------

Instead of providing class as command line parameter you can register the class explicitly in the following way:


.. code:: python

    #example_package/example_module.py

    ...
    from rmi import config

    @config.register
    class ExampleDetector(detectors.AnomalyDectector):
        ...


then you can run integration by just providing config file:


.. code:: shell-session

    # rmi -c example.yaml -l debug
