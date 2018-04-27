.. _configuration:

Configuration
#############


You can set the following environment variables:


Cron job AND Lambda
===================

``SENTRY_DSN``
--------------
**Type:** String

**Default:** ``None``

Use sending crashes to http://sentry.prod.mozaws.net/


``SERVER_URL``
--------------
**Type:** String

**Default:** ``http://localhost:8888/v1``

URL to the Kinto server for storage.


``BUCKET``
----------
**Type:** String

**Default:** ``build-hub``

Name of Kinto bucket to store it in.


``COLLECTION``
--------------
**Type:** String

**Default:** ``releases``

Name of Kinto collection to store it in.


``AUTH``
--------
**Type:** String

**Default:** ``user:pass``

Credentials for connecting to the Kinto server.


``TIMEOUT_SECONDS``
-------------------
**Type:** Integer

**Default:** 300

Max. seconds for fetching JSON URLs.


``NB_PARALLEL_REQUESTS``
------------------------
**Type:** Integer

**Default:** 8

Used both for number of parallel HTTP GET requests and the number of records
to send in each batch operation to Kinto.


``PRODUCTS``
------------
**Type:** List of strings separated by space

**Default:** ``firefox thunderbird mobile devedition``

Which product names to not ignore.

``ARCHIVE_URL``
---------------
**Type:** String

**Default:** ``https://archive.mozilla.org/``

Primarily is an environment variable so it can be changed with when running
unit tests to check that the unit tests actually don't depend on real
network calls.

``LOG_METRICS``
---------------
**Type:** String

**Default:** ``datadog``

Used to decided which `backend for markus to use <http://markus.readthedocs.io/en/latest/backends.html>`_.
Value must be one of ``datadog``, ``logging``, ``void`` or ``cloudwatch``.

If set to ``datadog`` (which is default), it will then send ``statsd`` commands
to ``${STATSD_HOST}:${STATSD_PORT}`` (with namespace ``${STATSD_NAMESPACE}``).
Their defaults are: ``localhost``, ``8125`` and ``''``.

If set to ``logging``, instead of sending metrics command anywhere, they are
included in the configured Python logging with prefix of ``metrics``.

If set to ``void``, all metrics are ignored and not displayed or sent anywhere.

If set to ``cloudwatch``, prints to ``stdout`` a custom format used by
`Datadog and AWS Cloudswatch <https://docs.datadoghq.com/integrations/amazon_lambda/>`_
that AWS Lambda can use.

Cron job ONLY
=============

``INITIALIZE_SERVER``
---------------------
**Type:** Bool

**Default:** True

Whether to initialize the Kinto server on first run.


``MIN_AGE_LAST_MODIFIED_HOURS``
-------------------------------
**Type:** Integer

**Default:** 0  (disabled)

When processing the CSV files, how "young" does an entry have to be to be
considered at all. Entries older than this are skipped.


``CSV_DOWNLOAD_DIRECTORY``
--------------------------

**Type:** String

**Default:** ``/tmp`` (as per Python's ``tempfile.gettempdir()``)

Path to where CSV files, from the inventory, is stored. When using Docker
for local development, it's advantageous to set this to a mounted directory.
E.g. ``./csv-downloads`` so that the data isn't lost between runs of
stopping and starting the Docker container.


``INVENTORIES``
---------------
**Type:** List of strings

**Default:** ``firefox, archive``

Which inventories to scrape and in which order.


Lamba ONLY
==========

``NB_RETRY_REQUEST``
--------------------
**Type:** Integer

**Default:** 6

Specifically sent to the ``backoff`` function for how many (exponentially
increasing sleeps) attempts to try to re-read if a HTTP GET fails.


``CACHE_FOLDER``
----------------
**Type:** String

**Default:** ``.``

Before the scraping really starts, we build up a Python dict of every
previously saved release ID and it's hash (as a string from the ``data``).
This is used to be able to quickly answer *"Did we already have this release
and has it not changed?"*.

Once this has been built up, that Python dict is dumped to disk, in
``CACHE_FOLDER``, so that next time it's faster to generate this dict without
having to query the whole Kinto database.
