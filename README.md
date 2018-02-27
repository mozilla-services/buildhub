# Buildhub

[![Build Status](https://travis-ci.org/mozilla-services/buildhub.svg?branch=master)](https://travis-ci.org/mozilla-services/buildhub)

_Buildhub_ aims to provide a public database of comprehensive information about releases and builds.

* [Online catalog](https://mozilla-services.github.io/buildhub/)
* [Web API documentation](https://buildhub.readthedocs.io)

## Licence

Apache 2

## Development

1. Create a `virtualenv` based on Python 3.6
2. Install all the dependencies:

```sh
pip install -r jobs/requirements/default.txt -r jobs/requirements/dev.txt -c jobs/requirements/constraints.txt
```

To run tests, install `tox` first: `pip install tox`. Now you can run tests:

```sh
# To run the functiona unit tests
tox -e py36
# To check for linting
tox -e flake8
```

TODO: Wanna mention how to run the unit tests without the functional part.

## Releasing

We don't use `zest.releaser` right now because of some problems with
releasing a package that is not at the root of the repo (`jobs/`), and
because we have no interest in uploading this project to PyPI, but
this could change if we figure out how.

The current procedure is:

* Bump version in `jobs/setup.py`
* Update the release date in `jobs/CHANGELOG.rst`
* `git commit -am "Bump x.y.z"`
* Open PR, wait for it to become green
* Merge PR
* `git tag x.y.z`
* `git push --tags origin`
* `make lambda.zip`
* Add a release on Github with the lambda.zip attached
* [Click here][bugzilla-link] to open a ticket to get it deployed

[bugzilla-link]: https://bugzilla.mozilla.org/enter_bug.cgi?comment=Could%20you%20please%20update%20the%20lambda%20function%20for%20Buildhub%20with%20the%20following%20one%3F%0D%0A%0D%0A%5BInsert%20a%20short%20description%20of%20the%20changes%20here.%5D%0D%0A%0D%0Ahttps%3A%2F%2Fgithub.com%2Fmozilla-services%2Fbuildhub%2Freleases%2Ftag%2FX.Y.Z%0D%0A%0D%0Ahttps%3A%2F%2Fgithub.com%2Fmozilla-services%2Fbuildhub%2Freleases%2Fdownload%2FX.Y.Z%2Fbuildhub-lambda-X.Y.Z.zip%0D%0A%0D%0AThanks%21&component=Operations%3A%20Storage&product=Cloud%20Services&qa_contact=chartjes%40mozilla.com&short_desc=Please%20deploy%20buildhub%20lambda%20function%20X.Y.Z
