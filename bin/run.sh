#!/usr/bin/env bash
set -eo pipefail

usage() {
  echo "usage: ./bin/run.sh version|test|lambda.zip|kinto|initialize-kinto|latest-inventory-to-kinto"
  echo ""
  echo "    version                     show current version"
  echo "    lambda.zip                  build Zip archive from buildhub package"
  echo "    kinto                       run a Kinto server"
  echo "    initialize-kinto            initialize a Kinto server for buildhub"
  echo "    latest-inventory-to-kinto   load latest S3 inventory to a Kinto server"
  echo ""
  exit 1
}

[ $# -lt 1 ] && usage

source .venv/bin/activate

case $1 in
  version)
    cat version.json
    ;;
  lambda.zip)
    cd .venv/lib/python3.6/site-packages/
    zip -r ../../../../lambda.zip *
    ;;
  kinto)
    kinto start --ini $KINTO_INI --port $PORT
    ;;
  initialize-kinto)
    kinto-wizard load jobs/buildhub/initialization.yml ${@:2}
    ;;
  latest-inventory-to-kinto)
    latest-inventory-to-kinto ${@:2}
    ;;
  *)
    usage
    ;;
esac