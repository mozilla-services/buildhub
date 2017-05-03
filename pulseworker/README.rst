Usage
=====

Obtain Pulse user and password at https://pulseguardian.mozilla.org

.. code-block:: bash

    PULSEGUARDIAN_USER="my-user" PULSEGUARDIAN_PASSWORD="XXX" python main.py --auth user:pass --debug

.. notes::

    The ``user:pass`` is the Basic auth on Kinto.

TODO
====

* Python 3 (migrate or get rid of MozillaPulse helper)

