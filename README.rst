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

Using pipenv (recommended)
--------------------------

.. code:: shell-session

   pipenv install --dev
   pipenv run python setup.py test


Using tox
---------

.. code:: shell-session

   tox
