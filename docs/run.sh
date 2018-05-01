#!/usr/bin/env bash
set -eo pipefail

usage() {
  echo "usage: ./run.sh build"
  echo ""
  echo "    build                         Generate the docs/_build/html/ files"
  echo ""
  exit 1
}


[ $# -lt 1 ] && usage

case $1 in
  build)
    cd docs && make html
    ;;
  *)
    exec "$@"
    ;;
esac
