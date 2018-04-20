.. _dev:

Developer Documentation
#######################

To do development locally all you need is ``docker`` and ``docker-compose``.

Quickstart
==========

To start everything just run:

.. code-block:: shell

    $ docker-compose up

This will start:

* A ``kinto`` server backed by PostgreSQL that syncs everything to
  Elasticsearch (accessible via ``localhost:8888``)
* A PostgreSQL server
* An Elasticsearch server (accessible via ``localhost:9200``)
* A ``kinto`` memory-storage server for running functional tests against
  (accessible via ``localhost:9999``)
* A (``create-react-app``) React server (accessible via ``localhost:3000``)

The very first time you run it, the database will be empty. You need to
populate it with an initial "scrape". More about that in the following
section.


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

That'll take a while. A really long while. Be prepared to go for lunch and
leave your computer on.

.. note::

    Don't worry about it being called "LATEST-inventory-to-kinto". It just
    means it uses the latest *manifest* (generated once a day) but it
    still iterates over every single build in S3.


Incremental data
================

When you've run ``latest-inventory-to-kinto`` at least once, the second time
it will be faster because, before sending data to ``kinto`` the
``to_kinto.py`` script will generate a massive dictionary of all previously
inserted IDs. However, all the "scraping" still needs to be processed again.
If you want to you can set an environment variable first that will
quickly ignore any S3 objects that are "too old". For example:

.. code-block:: shell

    $ docker-compose run buildhub bash
    app@b95573edb130:~$ MIN_AGE_LAST_MODIFIED_HOURS=48 latest-inventory-to-kinto

With ``MIN_AGE_LAST_MODIFIED_HOURS=48`` it means that any build that is found
to be older than 2 days from today (in UTC) will immediately bit skipped.
This will drastically reduce the time it takes to run the whole job.

Functional tests
================

The functional tests require that you have a ``kinto`` server up and running.
By default, the functional tests assumes that the ``kinto`` server is running
at ``http://testkinto:9999``. To start that server, run:

.. code-block:: shell

    $ docker-compose up testkinto


.. note::

    The reason there are **two** ``kinto`` servers (one for functional tests
    and one for a local dev instance) is because the functional tests have
    fixture expectations and can't guarantee that it leaves the database in
    the same state as *before* the tests.
    It would be annoying if you local instance changes weirdly (potentially
    unrealistic names) every you run the funtional tests.

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

The unit tests are basically the functional tests except the tests
that depend on the presence of an actual server available. These tests
are faster to run when iterating rapidly when you know the
functional test isn't immediately important or relevant.

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

Writing documentation
=====================

To work on the documentation, edit the ``docs/**/*.rst`` files. To build
and see the result of your work run:

.. code-block:: shell

    $ docker-compose run docs build

That will generate the ``docs/_build/html/`` directory (unless there were
errors) and you can open the ``index.html`` in your browser:

.. code-block:: shell

    $ open docs/_build/html/index.html

.. note::

    Our ``sphinx-build`` command transforms any warnings into errors.

Upgrading UI packages
=====================

To update any of the packages that the UI uses, follow these steps
(as an example):

.. code-block:: shell

    $ docker-compose run ui bash
    root@be2dda49e5ef:/app# yarn outdated
    root@be2dda49e5ef:/app# yarn upgrade prettier --latest
    root@be2dda49e5ef:/app# exit

Check that the ``ui/package.json`` and ``ui/yarn.lock`` changed accordingly.

Licensing preamble
==================

Every file of code we write, since we use Mozilla Public License 2.0, has to
have a preamble. The best way to describe is to look at existing code.
There's a script to check if any files have been missed:

.. code-block:: shell

    $ ./bin/sanspreamble.py

Run it to check which files you might have missed.

Adding/Updating Python packages to requirements files
=====================================================

You don't need a virtualenv on the host as long as you have
`hashin <https://pypi.python.org/pypi/hashin>`_ installed globally.

Alternatively you can use Docker. In this example we add a new package
called ``markus``:

.. code-block:: shell

    $ docker-compose run --user 0 buildhub bash
    root@2ec530633121:/app# pip install hashin
    root@2ec530633121:/app# cd jobs/
    root@2ec530633121:/app/jobs# hashin markus -r requirements/default.txt

Some packages might require additonal "contraint packages". Best way to
know is to find out by seeing if ``pip install ...`` fails:


.. code-block:: shell

    root@2ec530633121:/app/jobs# pip install -r requirements/default.txt -c requirements/constraints.txt

If it fails because an extra constraint package is required add it like this:

.. code-block:: shell

    root@2ec530633121:/app/jobs# hashin some-extra-package -r requirements/constraints.txt

Finally, exit the interactive Docker shell and try to rebuild:

.. code-block:: shell

    $ docker-compose build buildhub

Debugging metrics logging
=========================

By default, all metrics logging goes to
``markus.backends.datadog.DatadogMetrics``. This requires that you have a
``statsd`` server running on ``$STATSD_HOST:STATSD_PORT``. If you don't
have that locally you can change it to plain Python logging by setting
``LOG_METRICS=logging``. For example:

.. code-block:: shell

    $ docker-compose run buildhub bash
    app@b95573edb130:~$ LOG_METRICS=logging latest-inventory-to-kinto

The current only allowed values for the ``LOG_METRICS`` environment variable
is ``datadog`` (default) and ``logging``. Anything else will raise a
``NotImplementedError`` exception.


Environment Variables and Settings files
========================================

Every environment variable that is defined and expected can obviously be
changed on the command line. E.g.

.. code-block:: shell

    app@b95573edb130:~$ CSV_DOWNLOAD_DIRECTORY=/tmp/stuff latest-inventory-to-kinto

But you can also, put all *your* preferences in a ``.env`` file or a
``settings.ini`` file in the root of the project. These are yours to keep and
not check in.

The order of preference is as follows:

1. Command line
2. ``settings.ini`` file
3. ``.env`` file

See documentation on `python-decouple here
<https://pypi.org/project/python-decouple/#id5>`_.

The rule of thumb is that all environment variables defined in the Python
code should **be for the purpose of production run**. Meaning, if you want
something that is not how we run it, by default, in production it's up to you
to override it.

Also, this rule of thumb implies that environment variables should be
secure by default. If there's a sensitive setting, don't leave insecure for
developers and expecting OPs to make it explictly secure. It's the other
way around. If you want to make some less secure (perhaps it's fine because
you're running it on your laptop with fake data), it's up to you to either
specify it on the command line or update your personal ``.env`` file.
