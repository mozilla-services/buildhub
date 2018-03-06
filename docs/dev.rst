.. _dev:

Developer Documentation
#######################

To do development locally all you need is ``docker`` and ``docker-compose``.

Functional Tests
================

The functional tests require that you have a ``kinto`` server up and running.
By default, the functional tests assumes that the ``kinto`` server is running
at ``http://kinto:8888``. To start that server, run:

.. code-block:: shell

    $ docker-compose up kinto

From the host you can test that it's running with ``curl``:

.. code-block:: shell

    $ curl localhost:8888

To start the functional tests now, run:

.. code-block:: shell

    $ docker-compose run buildhub functional-tests

Note that the default ``docker-compose.yml`` sets up a volume mount. So
if you change any of the files in the current directory, it's immediately
used in the next ``docker-compose run ...`` run.

Unit Tests
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
