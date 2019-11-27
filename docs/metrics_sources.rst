===============
Metrics sources
===============

**This software is pre-production and should not be deployed to production servers.**

.. contents:: Table of Contents


Perf event based
================

To collect metrics you need to provide ``event_names`` list (defaults to instructions,
cycles, cache-misses, memstalls) to runner object in config file.

**Only a few or several hardware events can be collected at the same time, because
Processor have a fixed number of registers which can be programmed to gain hardware information!**


Resctrl based
=============

To collect metrics you need to have hardware with `Intel RDT <https://www.intel.com/content/www/us/en/architecture-and-technology/resource-director-technology.html>`_ support and set ``rdt_enabled`` in config file.
