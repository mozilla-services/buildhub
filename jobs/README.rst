This folder contains several scripts to aggregate build information from different sources and keeping it up to date.

.. note::

    The ``user:pass`` in the command-line examples is the Basic auth for Kinto.


Initialization
==============

We provide an initialization manifest that will define the buckets and collection and their permissions.

Load it with:

.. code-block:: bash

    kinto-wizard load --server https://kinto/ --auth user:pass initialization.yaml

The JSON schema validation can be enabled on the server with the following setting:

.. code-block:: ini

    kinto.experimental_collection_schema_validation = true

S3 inventory
============

Parse S3 inventory, fetch metadata, and print records as JSON in stdout:

.. code-block:: bash

    cat inventory.csv | inventory-to-records

Load records into Kinto:

.. code-block:: bash

    cat inventory.csv | inventory-to-records | to-kinto --server https://kinto/ --bucket build-hub --collection release --auth user:pass initialization.yaml


System-Addons updates
=====================

Fetch information about available system addons updates for every Firefox release.
Each addon has its ID, a builtin version (if any), and an update available from AUS (if any).

The script will fetch addons updates only if the ``systemaddons`` field of the archive record is set (e.g. not null).

.. code-block:: bash

    python3 sysaddons_update.py --server http://localhost:8888/v1 --auth user:pass --debug



Pulse listener (*WIP*)
======================

Listen to Pulse build and publishes records on a ``builds`` collection.

Obtain Pulse user and password at https://pulseguardian.mozilla.org

.. code-block:: bash

    PULSEGUARDIAN_USER="my-user" PULSEGUARDIAN_PASSWORD="XXX" python2 listen_pulse.py --auth user:pass --debug


TODO
----

* Python 3 everywhere (migrate or get rid of MozillaPulse helper)
