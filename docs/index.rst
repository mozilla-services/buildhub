Overview
########

Getting started
===============

Buildhub is a Kinto collection that contains the information about all
the builds.

**Browsing using Kinto**

You can access the database using the Kinto API:

.. note::
   
    https://kinto-ota.dev.mozaws.net/v1/buckets/build-hub/collections/releases/records?_limit=10

`More information in the Kinto documentation <http://kinto.readthedocs.io/en/stable/api/1.x/index.html#full-reference>`_.

**Browsing using Elasticsearch**

You can also use an ElasticSearch endpoint for more powerful queries:

.. note::
   
    https://kinto-ota.dev.mozaws.net/v1/buckets/build-hub/collections/releases/search

`More information in the Elasticsearch documentation <https://www.elastic.co/guide/en/elasticsearch/reference/current/search.html>`_

.. _data_schema:

More about the data schema
==========================

A build follows the following structure:

.. code-block:: none

    {
        "id": "firefox_beta_50-0b11_macosx_el",
        "schema": 1497453926485,
        "last_modified": 1498140377629,
        "target": {
            "platform": "macosx",
            "version": "50.0b11",
            "channel": "beta",
            "locale": "el"
        },
        "build": {
            "id": "20161027110534",
            "date": "2016-10-27T11:05:34Z"
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

You can access a build from the following URL:

.. note::

   https://kinto-ota.dev.mozaws.net/v1/buckets/build-hub/collections/releases/records/firefox_beta_50-0b11_macosx_el



+-------------------+--------------------------------------------------------------------------------------+
| **Field**         | **Description**                                                                      |
+-------------------+--------------------------------------------------------------------------------------+
| ``id``            | A unique ID for a build :ref:`Information about the release ID format <release_id>`. |
+-------------------+--------------------------------------------------------------------------------------+
| ``schema``        | The schema version identifier when the release record was added to the database.     |
+-------------------+--------------------------------------------------------------------------------------+
| ``last_modified`` | The timestamp of the last time the release record was modified in the database.      |
+-------------------+--------------------------------------------------------------------------------------+
| ``target``        | Major information about the release:                                                 |
|                   | ``version``, ``platform``, ``locale`` and ``channel`` it was built for.              |
+-------------------+--------------------------------------------------------------------------------------+
| ``build``         | Information about the build of the release: build ``id`` and build ``date``          |
|                   | This information might be missing for some build when we didn't figure it out yet.   |
+-------------------+--------------------------------------------------------------------------------------+
| ``source``        | Information about the source code version used to make the release.                  |
|                   | ``product``, ``tree`` and ``revision`` in mercurial and a ``repository`` link.       |
+-------------------+--------------------------------------------------------------------------------------+
| ``download``      | Information about the resulting build package aka installer.                         |
|                   | ``mimetype``, ``size``, ``date`` and ``url`` of the downloadable package.            |
+-------------------+--------------------------------------------------------------------------------------+
| ``systemaddons``  | A list of systemaddons that shipped with the release:  the addon ``id``,             |
|                   | the ``buildin`` version, the currently ``updated`` version (from balrog).            |
+-------------------+--------------------------------------------------------------------------------------+

If you wish to make sure a record is valid, you can validate it
against the JSON schema that you can find in the collection
properties::

.. note::

  https://kinto-ota.dev.mozaws.net/v1/buckets/build-hub/collections/releases

We also use it to make sure the records that are added to the
collection respect that schema and does not break your clients by
mistake.


More about the release record ID
================================

.. _release_id:

If you have some information about a release, you might want to guess
its ID directly in order to fetch more information.

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
