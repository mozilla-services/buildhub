#!/usr/bin/env bash
set -eo pipefail

usage() {
  echo "usage: ./bin/run.sh version|functional-tests|unit-tests|lintcheck|lambda.zip|initialize-kinto|latest-inventory-to-kinto"
  echo ""
  echo "    version                     Show current version"
  echo "    functional-tests            Run all tests"
  echo "    unit-tests                  Run all tests except the functional ones"
  echo "    lintcheck                   Run flake8 on all code"
  echo "    lambda.zip                  Build Zip archive from buildhub package"
  # echo "    start-kinto                 Start Kinto server with memory backend"
  # echo "    initialize-kinto            Initialize a Kinto server for buildhub"
  echo "    latest-inventory-to-kinto   Load latest S3 inventory to a Kinto server"
  echo ""
  exit 1
}

[ $# -lt 1 ] && usage

case $1 in
  version)
    cat version.json
    ;;
  unit-tests)
    py.test --ignore=jobs/tests/test_lamdba_s3_event_functional.py --override-ini="cache_dir=/tmp/tests" jobs/tests ${@:2}
    ;;
  functional-tests)
    py.test --override-ini="cache_dir=/tmp/tests" jobs/tests ${@:2}
    ;;
  lambda.zip)
    pip install virtualenv
    rm -fr .venv
    virtualenv .venv
    source .venv/bin/activate
    pip install -e jobs
    pip install -r jobs/requirements/default.txt -c jobs/requirements/constraints.txt
    pushd .venv/lib/python3.6/site-packages/
    zip -r /tmp/lambda.zip *
    popd
    cp /tmp/lambda.zip .
    ;;
  # start-kinto)
  #   # The --host 0.0.0.0 is important, otherwise it defaults to 127.0.0.1
  #   # and that doesn't work with docker-compose.
  #   [ -f config/kinto.ini ] || kinto init --backend memory --host 0.0.0.0
  #   kinto start ${@:2}
  #   ;;
  # initialize-kinto-wizard)
  #   kinto-wizard load ${@:2}
  #   ;;
  latest-inventory-to-kinto)
    # source .venv/bin/activate
    latest-inventory-to-kinto ${@:2}
    ;;
  lintcheck)
    flake8 jobs/buildhub jobs/tests
    ;;
  *)
    exec "$@"
    ;;
esac
