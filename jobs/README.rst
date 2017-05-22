This folder contains several scripts to aggregate build information from different sources and keeping it up to date.

.. note::

    The ``user:pass`` in the command-line examples is the Basic auth for Kinto.


Scrape archives
===============

Scrape nightly, beta and releases from https://archives.mozilla.org and publishes records on a ``archives`` collection.

The archives website is a folder tree whose folder and file listings can be obtained in JSON.

This script walks through every version, platform and locale folders to pick the release archives for Firefox, Thunderbird and Fennec.

For the English locale (``en-US``), and for a limited set of versions (aka. «candidates») a set of metadata is available (build id, revision, ...). The script will leave those related fields empty when the metadata is not available for a particular archive.

.. code-block:: bash

    python3 scrape_archives.py --server http://localhost:8888/v1 --auth user:pass --debug

.. note::

    Currently, it won't scan nightlies before the current month.


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
