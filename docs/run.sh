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
    sphinx-build -a -W -n -b html -d docs/_build/doctrees docs docs/_build/html
    ;;
  *)
    exec "$@"
    ;;
esac
