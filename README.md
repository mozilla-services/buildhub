# Buildhub

[![CircleCI](https://circleci.com/gh/mozilla-services/buildhub.svg?style=svg)](https://circleci.com/gh/mozilla-services/buildhub)

_Buildhub_ aims to provide a public database of comprehensive information about releases and builds.

* [Online catalog](https://mozilla-services.github.io/buildhub/)
* [Web API documentation](https://buildhub.readthedocs.io)

## Licence

[MPL 2.0](http://www.mozilla.org/MPL/2.0/)

## Development

1.  Install Docker
2.  To run tests: `make test`
3.  To lint check Python code: `make lintcheck`

## Continuous Integration

We use [CircleCI](https://circleci.com/gh/mozilla-services/buildhub)
for all continous integration.

## Releasing

There are a few pieces to Buildhub.

### AWS Lambda job and cron job

Generate a new `lambda.zip` file by running:

    rm lambda.zip
    make lambda.zip

This runs a script inside a Docker container to generate the `lambda.zip`
file.

You need to have write access to `github.com/mozilla-services/buildhub`.

You need a [GitHub Personal Access Token](https://github.com/settings/tokens)
with `repos` scope. This is to generate GitHub Releases and upload assets
to them.

Create a Python virtual environment and install "requests" and "python-decouple"
into it.

Run `./bin/make-release.py`. You need to set the `GITHUB_API_KEY` environment
variable. You need to specify the "type" of the release as a command-line
argument. Choices are:

* `major` (e.g. '2.6.9' to '3.0.0')
* `minor` (e.g. '2.6.7' to '2.7.0')
* `patch` (e.g. '2.6.7' to '2.6.8')

Then do this in your Python virtual environment:

    $ GITHUB_API_KEY=895f...ce09 ./bin/make-release.py minor

This will bump the version in `setup.py`, update the `CHANGELOG.rst` and
make a tag and push that tag to GitHub.

Then, it will create a Release and upload the latest `lambda.zip` as an
attachment to that Release.

You need to file a Bugzilla bug to have the Lambda job upgraded on Stage.
[Issue #423](https://github.com/mozilla-services/buildhub/issues/423)
is about automating this away.

To upgrade the Lambda job on **Stage** run:

    ./bin/deployment-bug.py stage-lambda

To upgrade the cron job _and_ Lambda job on **Prod** run:

    ./bin/deployment-bug.py prod

### Website ui

Install yarn.

Then run:

    $ cd ui
    $ yarn install
    $ yarn deploy

## Datadog

[Buildhub Performance](https://app.datadoghq.com/dash/794559/buildhub-performance)
