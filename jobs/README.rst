This folder contains several scripts to aggregate build information from Mozilla archives (and eventually keeping it up to date).

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

In order to fetch inventories from S3, install the dedicated Amazon Services client:

.. code-block:: bash

   sudo apt-get install awscli

We are interested in two listing: ``firefox`` and ``archive`` (thunderbird, mobile).

.. code-block:: bash

    export LISTING=archive

List available manifests in the inventories folder:

.. code-block:: bash

    aws --no-sign-request --region us-east-1 s3 ls "s3://net-mozaws-prod-delivery-inventory-us-east-1/public/inventories/net-mozaws-prod-delivery-$LISTING/delivery-$LISTING/"

Download the latest manifest:

.. code-block:: bash

    aws --no-sign-request --region us-east-1 s3 cp s3://net-mozaws-prod-delivery-inventory-us-east-1/public/inventories/net-mozaws-prod-delivery-$LISTING/delivery-$LISTING/2017-08-02T00-11Z/manifest.json

Download the associated files (using `jq <https://stedolan.github.io/jq/download/>`_):

.. code-block:: bash

    files=$(jq -r '.files[] | .key' < 2017-08-01T00-12Z/manifest.json)
    for file in $files; do
        aws --no-sign-request --region us-east-1 s3 cp "s3://net-mozaws-prod-delivery-inventory-us-east-1/public/$file" .
    done

Concatenate all CSV into one:

.. code-block:: bash

    zcat *.gz > inventory.csv

Parse S3 inventory, fetch metadata, and print records as JSON in stdout:

.. code-block:: bash

    cat inventory.csv | inventory-to-records > records.data

Load records into Kinto:

.. code-block:: bash

    cat records.data | to-kinto --server https://kinto/ --bucket build-hub --collection release --auth user:pass initialization.yaml

Repeat with ``LISTING=firefox``.
