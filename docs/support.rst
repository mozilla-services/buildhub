.. _support:

Support
#######

Do not hesitate to ask questions, start conversations, or report issues on the `BuildHub Github repo <https://github.com/mozilla-services/buildhub/>`_.

.. note::

    Currently we use the same issue tracker for problems related to code (eg. features, bugs) and data (eg. missing builds records) for every component (UI, server, lambda, cron job...).


Frequently Asked Questions
==========================

Builds XYZ are missing, is it normal?
-------------------------------------

It's never normal. Every missing data should be considered as bug and reported.

We have a cron jobs that back fills the data when a bug is fixed.


How can I help you triage/debug?
--------------------------------

Answering those questions may help:

- Is data missing for every product/version/platform/channel?
- How old is the newest entry?
- Does the missing release file on https://archive.mozilla.org have a different path/URL than the previous releases?
