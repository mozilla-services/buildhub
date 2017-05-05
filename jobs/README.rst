This folder contains several worker jobs.

.. notes::

    The ``user:pass`` is the Basic auth on Kinto.


Pulse listener
==============

Listen to Pulse build and publishes records on a ``builds`` collection.

Obtain Pulse user and password at https://pulseguardian.mozilla.org

.. code-block:: bash

    PULSEGUARDIAN_USER="my-user" PULSEGUARDIAN_PASSWORD="XXX" python2 listen_pulse.py --auth user:pass --debug


Scrap archives
==============

Scrap releases on https://archives.mozilla.org and publishes records on a ``archives`` collection.


.. code-block:: bash

    python3 scrap_archives.py --auth user:pass --debug


TODO
====

* Python 3 everywhere (migrate or get rid of MozillaPulse helper)

