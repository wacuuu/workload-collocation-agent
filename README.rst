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

.. code:: shell-session

   pipenv install --dev
   pipenv run python setup.py test
   # or 
   PYTHONPATH=. pytest tests


Using tox
---------

.. code:: shell-session

   tox


Configuration
-------------

Available features: 

- Create complex and configure python objects using `YAML tags`_ e.g. Runner, MesosNode, Storage
- Passing arguments and simple parameters type check
- Including other yaml or json files
- Register any external class with ``-r`` or by using ``rmi.config.register`` API 

.. _`YAML tags`: http://yaml.org/spec/1.2/spec.html#id2764295

TODO: configuration: better description & more examples

