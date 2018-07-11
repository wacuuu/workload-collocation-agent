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


Using tox
---------

.. code:: shell-session

   tox


Configuration
-------------

..  TODO:  <11-07-18, pawel.palucki> describe idea of config as dependency injection framework
            including features as passing parameters and include for other files
