=========
Twemcache
=========

To run the image you need to pass PORT environmental variable into the container (twemcache will bind to this port), e.g.:

.. code:: shell-session

   docker run -ti -e PORT=11211 twemcache

