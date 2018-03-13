#!/usr/bin/env bash
set -eo pipefail

usage() {
  echo "usage: ./run.sh build"
  echo ""
  echo "    start                         Start Kinto server with memory backend"
  echo "    migrate                       Create the kinto database tables"
  echo "    initialize-kinto-wizard       Initialize a Kinto server for buildhub"
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
