# Buildhub

[![Build Status](https://travis-ci.org/mozilla-services/buildhub.svg?branch=master)](https://travis-ci.org/mozilla-services/buildhub)

*Buildhub* aims to provide a public database of comprehensive information about releases and builds.

* [Online catalog](https://mozilla-services.github.io/buildhub/)
* [Web API documentation](https://buildhub.readthedocs.io)

## Licence

Apache 2

## Releasing

We don't use `zest.releaser` right now because of some problems with
releasing a package that is not at the root of the repo (`jobs/`), but
this could change if we figure out how.

The current procedure is:

* Bump version in `jobs/setup.py`
* `git tag x.y.z`
* `git push --tags origin`
* Open a ticket like https://bugzilla.mozilla.org/show_bug.cgi?id=1426340 to get it deployed
