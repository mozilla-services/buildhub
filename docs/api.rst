.. _api:

API
###

The BuildHub API is just a Kinto instance with a collection of records. A :ref:`series of jobs <jobs>` is charge of keeping those records up to date when new releases are published.

Servers
=======

* **Production**: https://buildhub.prod.mozaws.net/v1/ (`catalog-prod`_)
* **Stage**: https://buildhub.stage.mozaws.net/v1/ (`catalog-stage`_)
* **Development**: https://kinto-ota.dev.mozaws.net/v1/ (`catalog-dev`_)

.. _catalog-prod: https://mozilla-services.github.io/buildhub/prod/
.. _catalog-stage: https://mozilla-services.github.io/buildhub/stage/
.. _catalog-dev: https://mozilla-services.github.io/buildhub/dev/

Clients
=======

Since it is an HTTP API and the records are public, you can simply use any HTTP client, like `curl <http://curl.haxx.se>`_ or `httpie <https://httpie.org>`_.

But for more convenience, especially regarding pagination and error handling, some dedicated libraries are also available:

* `kinto-http.js <https://github.com/Kinto/kinto-http.js>`_ (JavaScript)
* `kinto-http.py <https://github.com/Kinto/kinto-http.py>`_ (Python)
* `kinto-http.rs <https://github.com/Kinto/kinto-http.rs>`_ (Rust)
* `kinto-http.java <https://github.com/intesens/kinto-http-java>`_ (Java)

Data
====

A single record has the following fields (:ref:`see below <data-schema>` for more details):

.. code-block:: javascript

    {
        "id": "firefox_beta_50-0b11_macosx_el",
        "schema": 1497453926485,
        "last_modified": 1498140377629,
        "target": {
            "platform": "macosx",
            "os": "mac",
            "version": "50.0b11",
            "channel": "beta",
            "locale": "el"
        },
        "build": {
            "id": "20161027110534",
            "date": "2016-10-27T11:05:34Z",
            "number": 2,
            "as": "$(CC)",
            "ld": "ldd",
            "cc": "/usr/bin/ccache /home/worker/workspace/build/src/gcc/bin/gcc -std=gnu99",
            "cxx": "/usr/bin/ccache /home/worker/workspace/build/src/gcc/bin/g++ -std=gnu++11",
            "host": "x86_64-pc-linux-gnu",
            "target": "x86_64-pc-linux-gnu",
        },
        "source": {
            "tree": "releases/mozilla-beta",
            "product": "firefox",
            "revision": "829a3f99f2606759305e3db204185242566a4ca6",
            "repository": "https://hg.mozilla.org/releases/mozilla-beta"
        },
        "download": {
            "mimetype": "application/x-apple-diskimage",
            "date": "2016-10-28T00:56:42Z",
            "size": 86180614,
            "url": "https://archive.mozilla.org/pub/firefox/releases/50.0b11/mac/el/Firefox 50.0b11.dmg"
        }
    }


Listing records
===============

Basic API
---------

The list of records is available at:

* `${SERVER}/buckets/build-hub/collections/releases/records <https://buildhub.stage.mozaws.net/v1/buckets/build-hub/collections/releases/records?_limit=10>`_

And a single record at:

* `${SERVER}/buckets/build-hub/collections/releases/records/${ID} <https://buildhub.stage.mozaws.net/v1/buckets/build-hub/collections/releases/records/firefox_beta_50-0b11_macosx_el>`_

A set of filters and pagination options can be used to query the list. The most notable features are:

* querystring filters (with ``?field=value`` or dedicated operators like ``?min_field=value`` or ``?has_field=true``)
* paginated list of records (follow the URL in the ``Next-Page`` response header)
* fields selection (with ``?_fields=``)
* polling for changes (with ``?_since=timestamp`` filter or ETags in request headers)

`More information in the Kinto documentation <https://kinto.readthedocs.io/en/stable/api/1.x/filtering.html>`_.

Elasticsearch API
-----------------

An ElasticSearch endpoint is also available for more powerful queries. It powers the online catalog.

* `$SERVER/buckets/build-hub/collections/releases/search <https://buildhub.stage.mozaws.net/v1/buckets/build-hub/collections/releases/search>`_

`More information in the Elasticsearch documentation <https://www.elastic.co/guide/en/elasticsearch/reference/current/search.html>`_


Example queries
===============

Is this an official build id?
-----------------------------

In order to check that a build id exists, we'll just check that it is mentioned in at least one record.

::

    curl -s -I "${SERVER}/buckets/build-hub/collections/releases/records?build.id=20110110192031&_limit=1" | grep "Total-Records: 1"

.. code-block:: javascript

    import KintoClient from "kinto-http";
    const client = new KintoClient(SERVER);
    const collection = client.bucket("build-hub").collection("releases");
    records = await collection.listRecords({limit: 1, filters: {"build.id": "20110110192031"}});
    console.log(records.length == 1);

.. code-block:: python

    import kinto_http

    client = kinto_http.Client("https://buildhub.stage.mozaws.net/v1")
    records = client.get_records(**{"build.id": "20110110192031", "_limit": 1, "pages": 1},
                                 bucket="build-hub", collection="releases")
    print(len(records) == 1)

What is the Mercurial commit ID of a build ID?
----------------------------------------------

.. code-block:: python

    client = kinto_http.Client("https://buildhub.stage.mozaws.net/v1")
    records = client.get_records(**{"build.id": "20110110192031", "_limit": 1, "pages": 1},
                                 bucket="build-hub", collection="releases")
    try:
        revision = records[0]["source"]["revision"]
    except IndexError:
        raise ValueError("Unknown build id")
    except KeyError:
        raise ValueError("Unknown revision")

What locales are available for a certain version?
-------------------------------------------------

.. code-block:: javascript

    import KintoClient from "kinto-http";

    const client = new KintoClient("https://buildhub.stage.mozaws.net/v1");
    const collection = client.bucket("build-hub").collection("releases");
    const records = await collection.listRecords({filters: {"target.version": "53.0b9"}});
    const locales = new Set(records.map(r => r.target.locale));

What are the available build ids of a specific version?
-------------------------------------------------------

Using curl and `jq <https://stedolan.github.io/jq/>`_:

.. code-block:: bash

    $ curl -s "${SERVER}/buckets/build-hub/collections/releases/records?target.version=56.0b12" | \
        jq -r '.data[] | .build.id' | \
        sort -u

    20170914024831



.. _data-schema:

More about the data schema
==========================

+-----------------------+----------------------------------------------------------------------+
| **Field**             | **Description**                                                      |
+-----------------------+----------------------------------------------------------------------+
| ``id``                | A unique ID for a build (:ref:`see details <release_id>`).           |
+-----------------------+----------------------------------------------------------------------+
| ``schema``            | The schema version when the record was added to the database.        |
+-----------------------+----------------------------------------------------------------------+
| ``last_modified``     | The timestamp incremented when the record was created/modified.      |
+-----------------------+----------------------------------------------------------------------+
| ``source``            | Information about the source code version used to build the release. |
+-----------------------+----------------------------------------------------------------------+
| ``source.product``    | One of ``firefox``, ``thunderbird``, ``fennec`` or ``devedition``    |
+-----------------------+----------------------------------------------------------------------+
| ``source.revision``   | **Optional** Mercurial changeset                                     |
+-----------------------+----------------------------------------------------------------------+
| ``source.repository`` | **Optional** Mercurial repository                                    |
+-----------------------+----------------------------------------------------------------------+
| ``source.tree``       | **Optional** Mercurial tree                                          |
+-----------------------+----------------------------------------------------------------------+
| ``target``            | Major information about the release.                                 |
+-----------------------+----------------------------------------------------------------------+
| ``target.version``    | Public version number                                                |
+-----------------------+----------------------------------------------------------------------+
| ``target.locale``     | Locale name                                                          |
+-----------------------+----------------------------------------------------------------------+
| ``target.channel``    | AUS update channel name                                              |
+-----------------------+----------------------------------------------------------------------+
| ``target.os``         | Operating system                                                     |
+-----------------------+----------------------------------------------------------------------+
| ``target.platform``   | OS and CPU architecture                                              |
+-----------------------+----------------------------------------------------------------------+
| ``build``             | Information about the build itself.                                  |
+-----------------------+----------------------------------------------------------------------+
| ``build.id``          | **Optional** Build identifier.                                       |
+-----------------------+----------------------------------------------------------------------+
| ``build.date``        | **Optional** Build date time.                                        |
+-----------------------+----------------------------------------------------------------------+
| ``build.number``      | **Optional** Release candidate number.                               |
+-----------------------+----------------------------------------------------------------------+
| ``build.as``          | **Optional** Assembler executable                                    |
+-----------------------+----------------------------------------------------------------------+
| ``build.ld``          | **Optional** Linker executable                                       |
+-----------------------+----------------------------------------------------------------------+
| ``build.cc``          | **Optional** C compiler command                                      |
+-----------------------+----------------------------------------------------------------------+
| ``build.cxx``         | **Optional** C++ compiler command                                    |
+-----------------------+----------------------------------------------------------------------+
| ``build.host``        | **Optional** Compiler host alias (cpu)-(vendor)-(os)                 |
+-----------------------+----------------------------------------------------------------------+
| ``build.target``      | **Optional** Target host alias (cpu)-(vendor)-(os)                   |
+-----------------------+----------------------------------------------------------------------+
| ``download``          | Information about the resulting downloadable archive.                |
+-----------------------+----------------------------------------------------------------------+
| ``download.url``      | Public archive URL                                                   |
+-----------------------+----------------------------------------------------------------------+
| ``download.size``     | In Bytes                                                             |
+-----------------------+----------------------------------------------------------------------+
| ``download.mimetype`` | File type                                                            |
+-----------------------+----------------------------------------------------------------------+
| ``download.date``     | Publication date                                                     |
+-----------------------+----------------------------------------------------------------------+

The complete JSON schema is available in the collection metadata:

* `${SERVER}/buckets/build-hub/collections/releases <https://buildhub.stage.mozaws.net/v1/buckets/build-hub/collections/releases>`_

The records added to the collection will be validated against that schema.


More about the release record ID
================================

.. _release_id:

If you have some information about a release, you might want to guess
its ID directly in order to fetch the individual record directly.

The unique ID of a release is the following:

.. code-block:: none

    {PRODUCT_NAME}_{CHANNEL}_{VERSION}_{PLATFORM}_{LOCALE}

- ``{PRODUCT_NAME}``: It can be either ``firefox``, ``fennec`` or ``thunderbird``
- ``{CHANNEL}``: It can be either ``aurora``, ``beta``, ``nightly``, ``nightly-old-id``
  The channel is not part of the ID for ``release`` and ``esr`` builds
- ``{VERSION}``: It is the full version of the build. Dots are replaced by ``-`` i.e ``55-0-1``, ``55-1b2``
  For nightly we use the date and time of the build as a version prefix. i.e: ``2017-06-01-10-02-05_55-0a1``
- ``{PLATFORM}``: It is the target platform. i.e: ``macosx``, ``android-arm``, ``android-api-15``, ``win32``, ``win64``, ``linux-i386``, etc.
- ``{LOCALE}``: It is the locale code. i.e ``fr-fr``, ``en-us``

All dots are replaced with dashes and all string are in lowercase.

Here are some example of release ID:

- ``firefox_nightly_2017-05-03-03-02-12_55-0a1_win64_en-us``
- ``thunderbird_52-0-1_linux-x86_64_en-us``
- ``firefox_aurora_54-0a2_macosx_en-us``
- ``firefox_beta_52-0b6_linux-x86_64_en-us``
- ``firefox_50-0rc1_linux-x86_64_fr``
- ``firefox_52-0esr_linux-x86_64_en-us``
- ``fennec_nightly-old-id_2017-05-30-10-01-27_55-0a1_android-api-15_multi``
