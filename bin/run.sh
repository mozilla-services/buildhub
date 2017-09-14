#!/usr/bin/env bash
set -eo pipefail

usage() {
  echo "usage: ./bin/run.sh version|test|lambda.zip|initialize-kinto|latest-inventory-to-kinto"
  echo ""
  echo "    version                     Show current version"
  echo "    test                        Run tests"
  echo "    lambda.zip                  Build Zip archive from buildhub package"
  echo "    initialize-kinto            Initialize a Kinto server for buildhub"
  echo "    latest-inventory-to-kinto   Load latest S3 inventory to a Kinto server"
  echo ""
  exit 1
}

[ $# -lt 1 ] && usage

case $1 in
  version)
    cat version.json
    ;;
  test)
    python3 -m venv /tmp/tests
    /tmp/tests/bin/pip install --constraint dependencies.txt jobs/
    /tmp/tests/bin/pip install -r jobs/dev-requirements.txt
    /tmp/tests/bin/py.test --ignore=jobs/tests/test_lamdba_s3_event_functional.py --override-ini="cache_dir=/tmp/tests" jobs/tests
    ;;
  lambda.zip)
    cd .venv/lib/python3.6/site-packages/
    zip -r ../../../../lambda.zip *
    ;;
  initialize-kinto)
    source .venv/bin/activate
    kinto-wizard load jobs/buildhub/initialization.yml ${@:2}
    ;;
  latest-inventory-to-kinto)
    source .venv/bin/activate
    latest-inventory-to-kinto ${@:2}
    ;;
  *)
    usage
    ;;
esac
