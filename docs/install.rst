===========================
Installing and running OWCA
===========================

Running OWCA as non-root user
-----------------------------

OWCA processes should not be run with root privileges. Following privileges are needed to run OWCA as non-root user:

- `CAP_DAC_OVERRIDE capability`_ - to allow non-root user writing to cgroups and resctrlfs kernel filesystems.
- ``/proc/sys/kernel/perf_event_paranoid`` - `content of the file`_ must be set to ``0`` or ``-1`` to allow non-root
  user to collect all the necesary event information.

If it is impossible or undesired to run OWCA with privileges outlined above, then you must add ``-0`` (or its
long form: ``--root``) argument when starting the process)

..  _`CAP_DAC_OVERRIDE capability`: https://github.com/torvalds/linux/blob/6f0d349d922ba44e4348a17a78ea51b7135965b1/include/uapi/linux/capability.h#L119
.. _`content of the file`: https://linux.die.net/man/2/perf_event_open
