Overview
########


*Buildub* aims to provide a public database of comprehensive information about releases and builds.

Concretely, it is a JSON API (`Kinto <https://kinto-storage.org>`_) where you can query a collection of records.

Quickstart
==========

Browse the database
-------------------

* `Online catalog <https://mozilla-services.github.io/buildhub/>`_

Basic JSON API
--------------

Buildhub is just a collection of records on a Kinto server.

* `$SERVER/buckets/build-hub/collections/releases/records?_limit=10 <https://buildhub.stage.mozaws.net/v1/buckets/buildhub/collections/releases/records?_limit=10>`_

A set of filters and pagination options can be used to query the collection. See :ref:`the dedicated section <api>`.

Elasticsearch API
-----------------

An ElasticSearch endpoint is also available for more powerful queries:

* `$SERVER/buckets/build-hub/collections/releases/search <https://buildhub.stage.mozaws.net/v1/buckets/buildhub/collections/releases/search>`_

`More information in the Elasticsearch documentation <https://www.elastic.co/guide/en/elasticsearch/reference/current/search.html>`_

Table of contents
=================

.. toctree::
   :maxdepth: 2

   api
   jobs
   support
