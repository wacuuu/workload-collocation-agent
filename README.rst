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
- Register any external class with ``-r`` or by using ``rmi.config.register`` API 

.. _`YAML tags`: http://yaml.org/spec/1.2/spec.html#id2764295

TODO: configuration: better description & more examples

