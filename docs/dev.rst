.. _dev:

Developer Documentation
#######################

To do development locally all you need is ``docker`` and ``docker-compose``.

Local development server
========================

First start the ``kinto`` server:

.. code-block:: shell

    $ docker-compose up kinto

This will start a ``kinto`` server you can reach via ``localhost:8888``.
It needs to be bootstrapped once. To that run (in another terminal):

.. code-block:: shell

    $ docker-compose run kinto migrate
    $ docker-compose run kinto initialize-kinto-wizard jobs/buildhub/initialization.yml  --server http://kinto:8888/v1 --auth user:pass

You should now have a running PostgreSQL and Elasticsearch that you can
populate with buildhub data and inspect. To see what's inside the PostgreSQL
server you can run:

.. code-block:: shell

    $ docker-compose run db psql -h db -U postgres

To see what's in the Elasticsearch you can simply open
``http://localhost:9200`` in your browser.


Initial data
============

The above steps will set up a working but blank ``kinto`` database. I.e.
no actual records in PostgreSQL and no documents indexed in Elasticsearch.

To boostrap the data, you can run ``latest-inventory-to-kinto``. You do that
like this:


.. code-block:: shell

    $ docker-compose run buildhub bash
    app@b95573edb130:~$ latest-inventory-to-kinto

That'll take a while.

Functional tests
================

The functional tests require that you have a ``kinto`` server up and running.
By default, the functional tests assumes that the ``kinto`` server is running
at ``http://testkinto:9999``. To start that server, run:

.. code-block:: shell

    $ docker-compose up testkinto

From the host you can test that it's running with ``curl``:

.. code-block:: shell

    $ curl localhost:9999

At least once, prime the ``kinto`` server like this:

.. code-block:: shell

    $ docker-compose run kinto initialize-kinto-wizard jobs/buildhub/initialization.yml  --server http://testkinto:9999/v1 --auth user:pass

To start the functional tests now, run:

.. code-block:: shell

    $ docker-compose run buildhub functional-tests

Note that the default ``docker-compose.yml`` sets up a volume mount. So
if you change any of the files in the current directory, it's immediately
used in the next ``docker-compose run ...`` run.

.. note::

    In the instructions above, you had to have two terminals open. One for the
    ``kinto`` server and one for the running of the tests. Alternatively
    you can use ``docker-compose up -d testkinto`` to put it in the background.
    Use ``docker-compose ps`` to see that it's running.
    And when you no longer need it, instead of ``Ctrl-C`` in that terminal,
    run ``docker-compose stop``. Again, use ``docker-compose ps`` to see that
    it's *not* running.

Unit tests
==========

The unit tests is basically the functional tests except those tests
that depend on the presence of an actual server available on
``localhost:8888``. These tests are faster to run when iterating rapidly
when you know the functional test isn't immediately important or relevant.

Simple run:

.. code-block:: shell

    $ docker-compose run buildhub unit-tests

Unlike the functional tests, this does not require first running
``docker-compose up kinto``.


Lint checking
=============

To ``flake8`` check all the tests and jobs code run:

.. code-block:: shell

    $ docker-compose run buildhub lintcheck


Generating ``lambda.zip`` file
==============================

The ``lambda.zip`` is a zip file for the ``site-packages`` of a Python 3.6
that has ``buildhub`` and all its dependencies including the ``.pyc`` files.

To generate the file use:

.. code-block:: shell

    $ docker-compose run buildhub lambda.zip

.. note::

    You might want to assert that the ``buildhub`` ``.pyc`` files really
    are there. ``unzip -l lambda.zip | grep buildhub``.

Running pytests like a pro
==========================

If you're hacking on something and find that typing
``docker-compose run buildhub functional-tests`` is too slow, there is a
better way to run ``pytest`` more iteratively and more rapidly. To do
so enter a ``bash`` shell as ``root``:

.. code-block:: shell

    $ docker-compose run --user 0 buildhub bash

From here you can run ``pytest`` with all its possible options.
For example:

.. code-block:: shell

    $ pytest jobs/tests/ -x --ff --showlocals --tb=native

And you can now install ``pytest-watch`` to have the tests run as soon
as you save any of the relevant files:


.. code-block:: shell

    $ pip install pytest-watch
    # Now replace `pytest` with `ptw -- `
    $ ptw -- jobs/tests/ -x --ff --showlocals --tb=native
