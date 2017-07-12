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


Scrape archives
===============

Scrape nightly, beta and releases from https://archives.mozilla.org and publishes records on a ``releases`` collection.

The archives website is a folder tree whose folder and file listings can be obtained in JSON.

This script walks through every version, platform and locale folders to pick the release archives for Firefox, Thunderbird and Fennec.

For the English locale (``en-US``), and for a limited set of versions (aka. «candidates») a set of metadata is available (build id, revision, ...). The script will leave those related fields empty when the metadata is not available for a particular archive.

.. code-block:: bash

    python3 scrape_archives.py --server http://localhost:8888/v1 --auth user:pass --debug

.. note::

    Currently, it won't scan nightlies before the current month.
