#!/usr/bin/env bash
set -eo pipefail

usage() {
  echo "usage: ./bin/run.sh version|waitfor|functional-tests|unit-tests|lintcheck|lambda.zip|initialize-kinto|latest-inventory-to-kinto"
  echo ""
  echo "    version                     Show current version"
  echo "    waitfor                     Run ./bin/wait-for"
  echo "    functional-tests            Run all tests"
  echo "    unit-tests                  Run all tests except the functional ones"
  echo "    lintcheck                   Run flake8 on all code"
  echo "    lambda.zip                  Build Zip archive from buildhub package"
  echo "    latest-inventory-to-kinto   Load latest S3 inventory to a Kinto server"
  echo ""
  exit 1
}

[ $# -lt 1 ] && usage

case $1 in
  version)
    cat version.json
    ;;
  waitfor)
    ./bin/wait-for ${@:2}
    ;;
  unit-tests)
    py.test --ignore=jobs/tests/test_lambda_s3_event_functional.py --ignore=jobs/tests/test_lambda_s3_event_functional.py --override-ini="cache_dir=/tmp/tests" jobs/tests ${@:2}
    ;;
  functional-tests)
    SERVER_URL=http://testkinto:9999/v1 py.test --override-ini="cache_dir=/tmp/tests" jobs/tests ${@:2}
    ;;
  lambda.zip)
    rm -fr .venv
    python -m venv .venv
    source .venv/bin/activate
    pip install -I ./jobs
    pip install -r jobs/requirements/default.txt -c jobs/requirements/constraints.txt
    pushd .venv/lib/python3.6/site-packages/
    zip -r /app/lambda.zip *
    popd
    rm -fr .venv
    ;;
  latest-inventory-to-kinto)
    latest-inventory-to-kinto ${@:2}
    ;;
  lintcheck)
    flake8 jobs/buildhub jobs/tests
    ;;
  *)
    exec "$@"
    ;;
esac
